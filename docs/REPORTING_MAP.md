# Reporting and evidence map

This is a practical map of the reporting and evidence supplied by the project, not a certified compliance checklist.

- Question, target and population: paper sections 1-2; MODEL_CARD.md.
- Data access, provenance and source checksum: DATA.md; reports/results.json.
- Predictor definitions, units, exclusions, leakage controls: PROTOCOL.md; core.py.
- Sample size and outcome counts: paper sections 2 and 4; both real-data aggregate reports.
- Training, preprocessing, tuning decisions and fixed seeds: PROTOCOL.md; FUTURE_DECLINE.md; train.py and decline.py.
- Evaluation design and uncertainty: paper sections 2-5; reports/results.json and decline-results.json.
- Missingness, scan quality and temporal ordering for the extension: ADNI_IMPORT.md; adni_import.py and adni_release.py.
- Full model comparisons: paper Appendix A; reports/RESULTS.md; development_cv.csv.
- Synthetic generation and censoring: SURVIVAL_FRAMEWORK.md; survival.py; synthetic-survival.json.
- Intended use, failure modes and clinical limits: MODEL_CARD.md; paper section 7.
- Project contributions, review status, ethics and licensing: CONTRIBUTIONS.md; paper section 8; LICENSE.
- Availability and reproducibility: REPRODUCIBILITY.md; tests; CI workflow.
- Independent/external validation, comprehensive fairness, clinical utility and horizon calibration: not completed. They must not be implied by this repository or report.

