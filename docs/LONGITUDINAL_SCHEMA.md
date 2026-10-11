# Canonical longitudinal input contract

This is a dataset-neutral contract, not an ADNI adapter. ADNI field mappings, file versions, visit alignment, missing-value codes, hemisphere aggregation and units must be verified against the downloaded data dictionary before use.

`baseline.csv`: one row per participant, columns `participant_id`, `baseline_date`, `mri_date` (YYYY-MM-DD), `age` (years), `mmse` (0–30 or blank), `hippocampus_mm3` (bilateral volume or blank), `icv_mm3` (intracranial volume or blank), `mri_qc_pass` (0/1).

`visits.csv`: `participant_id`, `assessment_date` (YYYY-MM-DD), `cdr` (observed 0, 0.5, 1, 2 or 3). The baseline assessment must be present. Duplicate baseline participants, duplicate same-day visits, unknown identifiers, missing dates and invalid numeric measurements fail validation. Historical pre-baseline visits are ignored after validation. Do not supply raw missing-value sentinels as genuine measurements.

Ranges are broad unit/sanity checks, not clinical reference intervals. MRI QC is a supplied field: the program cannot verify the truth of source QC. Input rows must already represent the chosen most-recent eligible acquisition. Do not manually choose scans based on outcomes.

Run on synthetic data:

```sh
python -m neurovolume.longitudinal --baseline examples/longitudinal/baseline.csv --visits examples/longitudinal/visits.csv --synthetic --output private/synthetic-audit
```

For authorized research data, omit `--synthetic`. Default outputs are in ignored `private/longitudinal/`: `cohort.csv` (individual baseline predictors, event indicator, last-zero and first-positive times, censoring time) and `audit.json` (aggregate counts, missingness, follow-up histogram and checksums). Do not publish real-data outputs without a disclosure and data-use review. `--synthetic` is a user declaration and is not proof that data are synthetic.

For event observations, the interval is (last_zero_days, first_positive_days]; for right-censored observations, first_positive_days is missing and last_zero_days is the censoring time. No model is fitted by this command.
