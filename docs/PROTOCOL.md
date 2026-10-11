# Analysis protocol — v1, fixed before model results

Question: Do MRI-derived volume measures improve classification of contemporaneous CDR > 0 versus CDR = 0 in OASIS-2?

Use the actual earliest row by visit order for each participant, preserving missing feature values (do not use groupby.first, which can borrow later values). Do not exclude converters or relabel baseline using later outcomes. CDR > 0 includes very mild/questionable impairment; this is not biomarker-confirmed Alzheimer disease or future decline.

Primary comparison: fixed logistic regression using demographics + MRI versus demographics alone. Secondary comparison: add MRI to demographics + MMSE. Two fixed tree models are benchmarks, not a search for a better headline.

- Demographics: age, recorded sex, education, socioeconomic status.
- MRI: estimated total intracranial volume (eTIV, cm³), normalized whole-brain volume (nWBV, fraction). Exclude ASF because it is redundant with intracranial scaling.
- Cognition: MMSE, evaluated separately because it measures the same clinical construct as the target.
- Exclude CDR, Group, identifiers, visit number, timing, future measurements, and handedness from predictors.
- Deterministic stratified 80/20 participant split, seed 42; 120 development and 30 test participants.
- Development: repeated stratified five-fold CV, three repeats, seed 2026. Identical folds across all comparisons. No hyperparameter search or test-guided changes.
- Median imputation and standardization are fit inside every training fold. Sex uses an explicit F=0 / M=1 mapping.
- Logistic regression: C=1, L2, max_iter=3000. Random forest: 200 trees, max_depth=4, min_samples_leaf=5. Gradient boosting: 100 estimators, learning_rate=.05, max_depth=2, min_samples_leaf=5. No class reweighting; threshold .5 fixed.
- Report ROC-AUC (primary), balanced accuracy, ordinary accuracy, sensitivity, specificity, precision, Brier score and confusion counts. Include a training-majority dummy baseline.
- Test confidence intervals: 5,000 stratified participant bootstrap resamples, seed 2026. Paired resamples for differences. Intervals condition on the fitted model and observed class balance, and do not capture model-training or site uncertainty. No formal significance claim and no multiple-comparison correction.
- Retain models fitted on development participants so demo and reported test metrics refer to the same models. Do not refit on test participants.

Public deliverables contain aggregate results, learned model parameters, code, and synthetic examples. Raw records, participant identifiers, split lists, and individual predictions stay in local ignored files. Include OASIS attribution and independent access instructions.

Future decline: a separate later protocol must define a baseline, prediction horizon, censoring, and enough progression events. Phase one must not be described as prognostic.
