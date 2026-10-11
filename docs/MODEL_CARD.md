> This card describes phase one. The separate future-impairment pilot is documented in [FUTURE_DECLINE.md](FUTURE_DECLINE.md).

# NeuroVolume model card

## Intended use
An educational research comparison of predefined feature sets on OASIS-2. Users can inspect aggregate results and experiment with synthetic measurement values. Not intended for diagnosis, screening, treatment, individual medical advice, or future-risk prediction. The model accepts precomputed numeric measurements, not MRI images.

## Target and population
Binary first-visit Clinical Dementia Rating (CDR) > 0 versus CDR = 0. CDR 0.5 is included in the positive class, so use “recorded cognitive impairment” or “CDR-based classification,” not “confirmed Alzheimer’s.” The workbook yields 65 positive and 85 negative baseline participants, ages 60–96. The source paper’s clinical diagnostic counts can differ from this operational CDR target; this project follows workbook CDR values without silently altering records to match published totals.

OASIS-2 is a selected research cohort, not a representative clinical or population sample. Results should not be generalized to younger people, new hospitals, new scanners, or other demographic populations without validation. Recorded sex is encoded using the source F/M field; broader gender categories are not represented. The dataset does not support a comprehensive subgroup fairness assessment.

## Inputs
- Age: years at baseline.
- Sex: source recorded sex, F=0 and M=1.
- EDUC: education in years.
- SES: socioeconomic class 1–5 (lower number corresponds to higher status in source coding).
- eTIV: estimated total intracranial volume, cm³.
- nWBV: normalized whole-brain volume, a fraction (e.g., 0.73, not 73).
- MMSE: Mini-Mental State Examination score, 0–30; included only in cognition feature sets.

CDR and Group are never predictors. Group can incorporate subsequent conversion and would leak future information. ASF is omitted because it is redundant with intracranial scaling; handedness has no useful variation here. Identifiers and visit timing are excluded.

## Training and evaluation
See PROTOCOL.md for fixed parameters and seeds. 120 baseline participants for model development, 30 held out for final evaluation. The same 15 development CV folds are reused across four feature sets and three algorithms. Imputation and standardization are learned within each fold. No resampling, feature selection, hyperparameter search, or threshold optimization using test data. Models saved in this release remain trained on development participants only.

Primary analysis uses logistic regression. Random forest and gradient boosting are prespecified benchmarks, not models selected after observing test accuracy. The interactive demo exposes four logistic models; all twelve sklearn pipelines are included for research inference.

95% test intervals use 5,000 stratified bootstrap resamples. Paired resamples estimate AUC differences. They reflect sampling variation conditional on fitted models and class balance, not variation in training, dataset choice, or site. CV fold SD is not a confidence interval. Multiple benchmark inspection means the highest observed accuracy should not be treated as a validated winner.

## Results and failure modes
Read ../reports/RESULTS.md and the full machine-readable results.json. MRI did not show a clear held-out increment over demographics. Adding cognition produces substantially stronger contemporaneous classification but does not establish presymptomatic detection. nWBV is a coarse whole-brain measure and cannot capture all disease-related regional changes.

A score between 0 and 1 is a model output, not a validated or calibrated individual probability. Brier scores are reported, but no external calibration was performed. Missing inputs are median-imputed; numerous missing inputs or unusual feature combinations make the demo less informative. Explanatory contributions are associations on the log-odds scale, not biological causes.

## Data, security, and distribution
Original workbook obtained from the official OASIS-2 page on 2026-09-06; checksum is in results.json. Public materials contain aggregate results and trained models, not participant records, split identifiers, or individual predictions. Follow OASIS terms independently before obtaining data. No upload or patient-input storage is implemented. User-edited synthetic scenarios are calculated locally in the browser; only an explicit download saves a scenario on the user's device.

Joblib files can execute code when loaded. Only load files from a source you trust. The portable logistic JSON format and Python/TypeScript inference functions avoid pickle loading for the default demo.

## Contributions
The project direction was selected by the user. OpenAI Codex implemented the analysis protocol, code, model training, tests, documentation, and interface during an AI-assisted build. This release does not claim independent manual implementation by the user, clinical validation, peer review, novelty, or deployment in patient care. Update contributions when actual review, analysis, experiments, or user testing occur.

MRI and clinical assessments were associated by the original study and were not necessarily acquired on the same day. This is an associated-visit classification task; the source publication describes temporal offsets that further limit precise temporal interpretation.
