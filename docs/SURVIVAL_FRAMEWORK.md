# Interval-censored survival framework — 2026-10-09

Implemented and tested software, with **synthetic-only** model artifacts. ADNI
tables have been acquired locally, mapped and audited; no ADNI survival model
has been trained. See [current status](STATUS.md).

## Reproduce

Use a separate Python 3.12 environment because lifelines 0.30.3 requires pandas
below 3, whereas the original classification study pins pandas 3.0.5.

```sh
python3.12 -m venv .venv-survival
source .venv-survival/bin/activate
pip install -r requirements-survival.txt
python -m neurovolume.survival --synthetic --output private/synthetic-survival
python -m pytest tests/test_survival.py tests/test_longitudinal.py -q
```

The fixed generator creates 600 invented participants with six-month assessment
intervals and independent censoring. MRI has an effect by construction. The model
learns from 450 participants and is evaluated on 150 unseen participants: 48
observed events and 102 right-censored observations. Generator seed and split seed
are 20261009. No synthetic participant is a disguised real participant.

The two Weibull accelerated failure-time models compare age + MMSE with age + MMSE
+ bilateral hippocampus/intracranial volume ratio. L2 penalization is fixed at 0.01;
shape is constant within each fitted model. Median imputation and standardization
use training participants only. No tuning or refit includes the held-out set.

See [lifelines model documentation](https://lifelines.readthedocs.io/en/latest/fitters/regression/WeibullAFTFitter.html).

## Evaluation and meaning

An event observed between L and U contributes `log(S(L) - S(U))`. A person
right-censored at L contributes `log(S(L))`. The held-out mean observation log
likelihood is -1.112 for age + cognition and -1.053 with MRI. Paired difference:
+0.059; 5,000 participant bootstrap resamples give a 95% interval of
[-0.004, +0.116]. Higher is better; these numbers are **not classification accuracy**.
The interval conditions on fitted models and omits training uncertainty.

These are probabilities for observations under the assumed event-time model,
conditional on assessment bounds. They require noninformative assessment and
censoring assumptions. CDR can fluctuate; the modeled first threshold crossing
is not an established latent biological disease onset. The true synthetic times
are not used as evaluation labels, and interval midpoints are never invented.

No time-dependent AUC, Brier score, calibration or clinical confidence interval is
claimed. Standard right-censored metrics cannot simply be fed uncertain interval
event times. Real-cohort estimators, support at three years, site separation and
sample-size precision must be decided before real-data outcome fitting.

## Portable explorer and verification

`models/synthetic-survival.json` contains training-only medians, means, scales,
log-scale coefficients, intercept and Weibull shape. `web/survival.mjs` is the
browser engine embedded by `scripts/build_standalone.py`. Tests compare native
lifelines, Python portable inference and JavaScript predictions on held-out
invented cases including missing values. Other tests check analytic interval
likelihood, monotonic curves, independent-seed recovery of the imposed MRI effect,
training-only preprocessing, invalid bounds, duplicates and unit mismatches.

## Controlled real data

After authorized data acquisition and dictionary review, use the canonical
longitudinal importer to create a local private cohort. The real-data entry point
is available for research execution **after protocol lock**, not an already
validated ADNI adapter:

```sh
python -m neurovolume.longitudinal --baseline private/baseline.csv --visits private/visits.csv --output private/longitudinal
python -m neurovolume.survival --cohort private/longitudinal/cohort.csv --output private/survival
```

Real-data models, participant split membership and reports stay in `private/`.
The minimum ten-event fit guard is a software guard, not proof of adequate sample
size. Do not replace bundled synthetic browser models with private artifacts until
data-use and publication/distribution rules have been reviewed.
