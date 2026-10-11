"""Interval-censored Weibull research framework. Bundled models are SYNTHETIC ONLY.

Run with the optional survival environment, not the original classifier environment.
The upper bound of a right-censored observation is infinity. Never replace event
intervals with their midpoint or treat unknown horizon labels as negatives.
"""
import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import WeibullAFTFitter
from sklearn.model_selection import train_test_split
from .privacy import private_output

SEED = 20261009
FEATURES = {
    "clinical": ["age", "mmse"],
    "clinical_mri": ["age", "mmse", "hippocampus_icv_ratio"],
}


def check_cohort(frame):
    required = {"participant_id", "event", "last_zero_days", "first_positive_days"} | set(FEATURES["clinical_mri"])
    if not required <= set(frame):
        raise ValueError("Missing canonical cohort columns; first run neurovolume.longitudinal.")
    if frame.empty or frame.participant_id.isna().any() or frame.participant_id.astype(str).str.strip().eq("").any() or frame.participant_id.duplicated().any():
        raise ValueError("Require one nonempty, unique participant identifier per row.")
    if not frame.event.isin([0, 1]).all():
        raise ValueError("Event indicator must be 0 or 1.")
    lower = frame.last_zero_days.to_numpy(dtype=float)
    upper = frame.first_positive_days.to_numpy(dtype=float)
    event = frame.event.to_numpy(dtype=bool)
    if not np.isfinite(lower).all() or (lower < 0).any():
        raise ValueError("Last-zero durations must be finite and nonnegative.")
    if not np.isfinite(upper[event]).all() or (upper[event] <= lower[event]).any():
        raise ValueError("Events require a positive-width observed interval.")
    if not np.isnan(upper[~event]).all() or (lower[~event] <= 0).any():
        raise ValueError("Censored rows require a missing upper bound and positive follow-up.")
    for feature, limits in [("age", (18, 120)), ("mmse", (0, 30)), ("hippocampus_icv_ratio", (0, .1))]:
        values = frame[feature].to_numpy(dtype=float)
        observed = values[~np.isnan(values)]
        if not np.isfinite(observed).all() or (observed < limits[0]).any() or (observed > limits[1]).any():
            raise ValueError("Implausible predictor: " + feature)
    if frame.age.isna().any():
        raise ValueError("Age is required.")


def transform(frame, model):
    x = frame[model["features"]].to_numpy(dtype=float)
    x = np.where(np.isnan(x), model["medians"], x)
    return pd.DataFrame((x - model["means"]) / model["scales"], columns=model["features"], index=frame.index)


def fit(frame, family):
    check_cohort(frame)
    features = FEATURES[family]
    raw = frame[features].to_numpy(dtype=float)
    if np.isnan(raw).all(axis=0).any():
        raise ValueError("A training predictor is entirely missing.")
    if frame.event.sum() < 10:
        raise ValueError("Too few events for this software framework (minimum 10; not a study power calculation).")
    medians = np.nanmedian(raw, axis=0)
    imputed = np.where(np.isnan(raw), medians, raw)
    scales = imputed.std(axis=0)
    scales[scales == 0] = 1
    model = {"features": features, "medians": medians.tolist(), "means": imputed.mean(axis=0).tolist(), "scales": scales.tolist()}
    x = transform(frame, model)
    x["lower"] = frame.last_zero_days
    x["upper"] = np.where(frame.event == 1, frame.first_positive_days, np.inf)
    # Fixed in advance of synthetic evaluation. No test-set hyperparameter selection.
    fitter = WeibullAFTFitter(penalizer=.01, l1_ratio=0, model_ancillary=False)
    fitter.fit_interval_censoring(x, lower_bound_col="lower", upper_bound_col="upper")
    model.update({"coefficients": [float(fitter.params_.loc[("lambda_", f)]) for f in features],
                  "intercept": float(fitter.params_.loc[("lambda_", "Intercept")]),
                  "shape": float(np.exp(fitter.params_.loc[("rho_", "Intercept")])),
                  "penalizer": .01, "time_unit": "days", "model": "interval-censored Weibull AFT"})
    return model, fitter


def cumulative_hazard(frame, model, days):
    days = np.asarray(days, dtype=float)
    if np.isnan(days).any() or (days < 0).any():
        raise ValueError("Prediction times must be nonnegative.")
    log_scale = model["intercept"] + transform(frame, model).to_numpy() @ model["coefficients"]
    with np.errstate(divide="ignore", over="ignore"):
        return np.exp(model["shape"] * (np.log(days)[..., None] - log_scale))


def survival(frame, model, days):
    return np.exp(-cumulative_hazard(frame, model, days))


def observation_log_likelihood(frame, model):
    """Conditional on observed assessment bounds; ignores visit-process factors.

    Scores an event with log(S(L)-S(U)); a censored row with log(S(L)).
    Requires noninformative censoring/assessment assumptions. Not disease accuracy.
    """
    lower = frame.last_zero_days.to_numpy(dtype=float)
    upper = np.where(frame.event == 1, frame.first_positive_days, np.inf)
    # Paired times, not all combinations of times and participants.
    log_scale = model["intercept"] + transform(frame, model).to_numpy() @ model["coefficients"]
    with np.errstate(divide="ignore", over="ignore"):
        hl = np.exp(model["shape"] * (np.log(lower) - log_scale))
        hu = np.exp(model["shape"] * (np.log(upper) - log_scale))
    out = -hl
    event = frame.event.to_numpy(dtype=bool)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[event] += np.log(-np.expm1(-(hu[event] - hl[event])))
    if not np.isfinite(out).all():
        raise ValueError("Nonfinite likelihood; inspect fitted model and durations.")
    return out


def synthetic_cohort(n=600, seed=SEED):
    """Invented predictors and known Weibull mechanism; never clinical evidence.

    Scheduled six-month assessments and independent uniform censoring. MRI has
    an effect by construction; this can verify software, not discover biology.
    """
    rng = np.random.default_rng(seed)
    age = np.clip(rng.normal(74, 7, n), 55, 95)
    mmse = np.clip(rng.normal(28, 1.4, n), 23, 30)
    ratio = np.clip(rng.normal(.0048, .0007, n), .002, .007)
    scale = np.exp(np.log(2100) - .035 * (age - 74) + .12 * (mmse - 28) + 650 * (ratio - .0048))
    true_time = scale * (-np.log(rng.uniform(size=n))) ** (1 / 1.6)
    censor = rng.uniform(365, 1825, n)
    upper = np.ceil(true_time / 180) * 180
    last_visit = np.floor(censor / 180) * 180
    event = upper <= last_visit
    lower = np.where(event, np.maximum(0, upper - 180), last_visit)
    # Missingness is independent and introduced after generating event times.
    mmse[rng.random(n) < .05] = np.nan
    ratio[rng.random(n) < .08] = np.nan
    return pd.DataFrame({"participant_id": [f"SYNTH-{i:04}" for i in range(n)], "age": age, "mmse": mmse,
                         "hippocampus_icv_ratio": ratio, "event": event.astype(int), "last_zero_days": lower,
                         "first_positive_days": np.where(event, upper, np.nan)})


def experiment(frame, synthetic=False):
    check_cohort(frame)
    train, test = train_test_split(frame, test_size=.25, random_state=SEED, stratify=frame.event)
    models, scores = {}, {}
    for family in FEATURES:
        models[family], _ = fit(train, family)
        models[family]["data_kind"] = "synthetic software validation" if synthetic else "private research data"
        scores[family] = observation_log_likelihood(test, models[family])
    delta = scores["clinical_mri"] - scores["clinical"]
    rng = np.random.default_rng(SEED + 1)
    bootstrap = np.array([delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(5000)])
    report = {"data_kind": models["clinical"]["data_kind"], "seed": SEED,
              "participants": len(frame), "training_participants": len(train), "test_participants": len(test),
              "training_events": int(train.event.sum()), "test_events": int(test.event.sum()),
              "test_right_censored": int((test.event == 0).sum()),
              "metric": "Mean held-out observation log likelihood (higher is better; not accuracy or calibrated clinical risk)",
              "results": {key: {"mean_test_log_likelihood": float(value.mean())} for key, value in scores.items()},
              "paired_mri_gain": {"mean": float(delta.mean()), "bootstrap_95_interval": np.quantile(bootstrap, [.025, .975]).tolist(), "resamples": 5000},
              "assumptions": ["Weibull event-time distribution", "Independent censoring and noninformative assessment schedule", "First threshold crossing modeled within last-zero/first-positive interval; CDR may fluctuate"],
              "limitations": ["Synthetic MRI effect is imposed by the generator, not a discovery.", "No ADNI training, external validation, personal prognosis, or clinical accuracy claim."] if synthetic else ["One held-out split only; no external validation.", "Observation likelihood does not establish horizon calibration or clinical usefulness."],
              "preprocessing": "Training-only median imputation and standardization; held-out participants never used to fit.",
              "split": "Stratified 75/25 split by participant; fixed seed; no model selection on test results."}
    return models, report, train, test


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--cohort", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.synthetic == bool(args.cohort):
        parser.error("Choose exactly one of --synthetic or --cohort.")
    if not args.synthetic:
        try:
            args.output = private_output(args.output or "private/survival")
        except ValueError as error:
            parser.error(str(error))
    frame = synthetic_cohort() if args.synthetic else pd.read_csv(args.cohort, dtype={"participant_id": str})
    models, report, train, test = experiment(frame, args.synthetic)
    report["software_versions"] = {p: version(p) for p in ["lifelines", "pandas", "numpy", "scipy", "scikit-learn"]}
    report["input_sha256"] = hashlib.sha256(args.cohort.read_bytes()).hexdigest() if args.cohort else None
    report["implementation_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.synthetic:
        report["generator"] = {"participants": 600, "seed": SEED, "assessment_interval_days": 180,
                               "censoring": "independent uniform 365–1825 days, last scheduled visit", "true_shape": 1.6}
    out = args.output or Path("private/survival")
    out.mkdir(parents=True, exist_ok=True)
    (out / "models.json").write_text(json.dumps(models, indent=2, allow_nan=False))
    (out / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    # Split membership is auditable but remains private for real cohorts.
    pd.DataFrame({"participant_id": pd.concat([train.participant_id, test.participant_id]),
                  "partition": ["training"] * len(train) + ["test"] * len(test)}).to_csv(out / "split.csv", index=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
