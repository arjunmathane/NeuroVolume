# Regional MRI and later recorded cognitive impairment — protocol draft v0.2

Status: prepared before receipt of a larger cohort; not registered, not externally reviewed, and not a completed study. Changes after receipt must be logged with dates and rationale before outcome modeling. The OASIS pilot is exploratory context, not validation for this next study.

## Primary question
Do baseline regional MRI measurements add predictive information beyond age and baseline cognition for later recorded CDR > 0 among participants with baseline CDR = 0?

## Data and time origin
Use an authorized longitudinal research cohort. Baseline is a clinical assessment with observed CDR = 0 and documented baseline age. Select one documented, quality-controlled MRI acquisition from the 180 days before or on baseline; choose the most recent eligible acquisition with fixed QC rules. Do not use MRI or cognition collected after prediction time. Use actual assessment dates, not scan dates or nominal visit codes, to define follow-up. Preserve dataset release, processing version, source dictionaries and checksums locally.

Primary baseline predictors: age and MMSE; expanded set adds bilateral hippocampal volume divided by intracranial volume, both in mm³ from the same processing pipeline. Baseline missingness is retained; imputation must be fitted within development folds. Exclude failed MRI QC, missing baseline age, no baseline CDR, baseline CDR > 0, and no observed follow-up. Report each exclusion once in fixed order. Missing MMSE or volumes do not justify filling from future visits.

Regional cortical thickness and other regions are secondary candidates only after the chosen dataset's availability and measurement definitions are verified. Do not guess or mix atlas regions, hemispheric summaries, units, or processing versions.

## Endpoint and censoring
Primary operational endpoint: first later recorded CDR > 0. Retain both the last zero-CDR assessment and first positive assessment. These bound an observation interval; they do not prove exact disease onset. A subsequent return to zero does not erase the first endpoint. Participants without a positive assessment are right-censored at the last observed zero assessment. Death, withdrawal and treatment data must be audited if available; missing follow-up is not a negative outcome.

## Planned model and evaluation
After data feasibility review, lock the model specification and development/test membership in a dated manifest before fitting. Primary candidate: a regularized interval-censored survival model, compared with the same model using age + cognition alone. Select the exact supported implementation and regularization grid before outcome fitting; no custom unvalidated survival implementation is planned. A time-to-first-recorded-positive model treating visit time as an exact event is a separately labeled sensitivity analysis, not a replacement for interval uncertainty.

Use participant-separated development and a held-out test set; stratify by event observation when feasible and inspect site/phase overlap. Fit preprocessing and tune regularization only inside development folds. A 3-year horizon is primary; report test discrimination and calibration only with adequate events and follow-up support. Use censoring-appropriate Brier scores and time-dependent AUC with training-estimated censoring models where assumptions hold. Specify the exact interval-aware estimand and estimator before fitting; do not feed interval-censored times to exact-event metrics without justification. Compare MRI-added performance using paired participant resampling, accounting for the selected estimator's assumptions.

Do not proceed to a confirmatory claim if event counts, follow-up or site coverage are inadequate. Sample size planning must consider anticipated signal, predictor degrees of freedom and desired precision rather than a universal events-per-variable cutoff. External validation on a compatible independent cohort is a separate milestone. No external-validation claim is permitted before completion.

## Reporting and release
Publish code, protocol versions, aggregate findings and a model card subject to data-use/publication terms. Keep participant-level data, splits, predictions, dates and licensed derivatives private. Synthetic fixtures only test software. The workbench must distinguish synthetic audits, exploratory OASIS results, and future measured results. No clinical screening or treatment use.

## Completion gates
1. Authorized data acquired and dictionary-based adapter verified.
2. Provenance, QC, dates, unit harmonization and cohort audit reviewed.
3. Sample-size/precision assessment, model/metric implementation and evaluation protocol locked.
4. Models trained and independently tested; failures and uncertainty documented.
5. Publication/distribution terms reviewed and reproducible release built.

October 9 implementation update: [interval-censored Weibull software](SURVIVAL_FRAMEWORK.md) is implemented using lifelines 0.30.3 with fixed L2 penalizer 0.01 and training-only preprocessing. A synthetic 75/25 split experiment and matching portable explorer are tested. This selects an implemented candidate, not the final specification for the real cohort. Observation log likelihood is the synthetic evaluation metric; three-year discrimination/calibration estimators still require a real-cohort protocol decision. No real-cohort hyperparameter search has been performed.

ADNI approval is verified. The clinical export and 7.x MRI release have been acquired, dictionary-mapped and audited locally, but the strict-QC subset is not fit-ready. Gate 1 is therefore only partly satisfied for the intended study: an older release and its source review are still needed. Gates 2–5 are not complete. Codex authored the software and draft; this is not independent manual work by the project owner.
