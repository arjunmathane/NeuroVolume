"""Optional interval-survival tests; executed in requirements-survival environment."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lifelines")
from neurovolume.survival import (check_cohort, fit, observation_log_likelihood,
                                  survival, synthetic_cohort, transform)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fitted():
    frame = synthetic_cohort(500, seed=912)
    model, native = fit(frame.iloc[:400], "clinical_mri")
    return frame, model, native


def test_portable_matches_native_and_browser(fitted):
    frame, model, native = fitted
    test = frame.iloc[400:]
    times = [0, 180, 365, 730, 1095, 1825]
    expected = native.predict_survival_function(transform(test, model), times=times).to_numpy()
    actual = survival(test, model, times)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    assert shutil.which("node"), "Node required for browser prediction parity"
    values = test[model["features"]].astype(object).where(test[model["features"]].notna(), None).to_dict("records")
    script = "import {survivalCurve} from './web/survival.mjs';let s='';for await(const c of process.stdin)s+=c;const a=JSON.parse(s);console.log(JSON.stringify(a.values.map(v=>survivalCurve(a.model,v,a.times))));"
    result = subprocess.run(["node", "--input-type=module", "-e", script], input=json.dumps({"model": model, "values": values, "times": times}, allow_nan=False), text=True, capture_output=True, cwd=ROOT, check=True)
    np.testing.assert_allclose(np.array(json.loads(result.stdout)).T, actual, atol=1e-12)


def test_survival_valid_and_directional_recovery(fitted):
    _, model, _ = fitted
    profiles = pd.DataFrame({"age": [74, 74], "mmse": [28, 28], "hippocampus_icv_ratio": [.003, .006]})
    curves = survival(profiles, model, [0, 365, 1095, 1825])
    assert np.all(curves[0] == 1)
    assert np.all(np.diff(curves, axis=0) <= 0)
    assert np.all((curves >= 0) & (curves <= 1))
    # Independent synthetic seed, imposed positive volume/time effect recovered.
    assert curves[2, 1] > curves[2, 0]


def test_likelihood_uses_interval_probability_and_censoring():
    frame = pd.DataFrame({"age": [74, 74], "mmse": [28, 28], "event": [1, 0], "last_zero_days": [10, 20], "first_positive_days": [20, np.nan]})
    model = {"features": ["age", "mmse"], "medians": [74, 28], "means": [74, 28], "scales": [1, 1], "coefficients": [0, 0], "intercept": np.log(100), "shape": 1}
    expected = [np.log(np.exp(-.1) - np.exp(-.2)), -.2]
    np.testing.assert_allclose(observation_log_likelihood(frame, model), expected)


def test_preprocessing_uses_training_only(fitted):
    frame, model, _ = fitted
    train = frame.iloc[:400][model["features"]]
    np.testing.assert_allclose(model["medians"], train.median().to_numpy())
    extreme = frame.iloc[400:].copy()
    extreme["mmse"] = 0
    before = json.dumps(model)
    survival(extreme, model, [1095])
    assert json.dumps(model) == before


@pytest.mark.parametrize("change", ["duplicate", "negative", "inverted", "censored_upper", "event_flag", "units"])
def test_invalid_cohorts_rejected(change):
    frame = synthetic_cohort(40)
    event = frame.index[frame.event == 1][0]
    censor = frame.index[frame.event == 0][0]
    if change == "duplicate": frame.loc[1, "participant_id"] = frame.loc[0, "participant_id"]
    if change == "negative": frame.loc[0, "last_zero_days"] = -1
    if change == "inverted": frame.loc[event, "first_positive_days"] = frame.loc[event, "last_zero_days"]
    if change == "censored_upper": frame.loc[censor, "first_positive_days"] = 1000
    if change == "event_flag": frame.loc[0, "event"] = 2
    if change == "units": frame.loc[0, "hippocampus_icv_ratio"] = 7000
    with pytest.raises(ValueError): check_cohort(frame)


def test_all_missing_training_feature_rejected():
    frame = synthetic_cohort(200)
    frame["mmse"] = np.nan
    with pytest.raises(ValueError, match="entirely missing"): fit(frame, "clinical")


def test_published_synthetic_artifacts_are_consistent():
    report = json.loads((ROOT / "reports/synthetic-survival.json").read_text())
    models = json.loads((ROOT / "models/synthetic-survival.json").read_text())
    assert report["data_kind"] == "synthetic software validation"
    assert report["participants"] == report["training_participants"] + report["test_participants"]
    assert report["test_events"] + report["test_right_censored"] == report["test_participants"]
    assert set(models) == {"clinical", "clinical_mri"}
    assert all(m["data_kind"] == report["data_kind"] for m in models.values())
