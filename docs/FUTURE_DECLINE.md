# Phase two: exploratory future recorded-impairment pilot

## Question and endpoint
Can baseline age and normalized whole-brain volume classify first recorded CDR > 0 within 1095 MRI-delay days among participants with baseline CDR = 0?

This is prediction of a later recorded outcome, not contemporaneous classification. It is not prediction of exact onset, all forms of decline, or biomarker-confirmed Alzheimer disease. MRI session intervals only approximate clinical assessment intervals.

## Cohort rules
- One actual first visit per participant; baseline CDR must equal zero.
- Event: first later recorded CDR > 0 occurs within 1095 days.
- Non-event: a CDR = 0 visit occurs at or beyond 1095 days, before any first positive CDR visit.
- Otherwise exclude as insufficient observed follow-up. Never turn short follow-up into an assumed three-year negative.
- Later return to CDR = 0 does not erase the first positive event.

85 initially eligible participants yielded 43 included: 8 events and 35 non-events. 42 were excluded. This selection can bias estimates; excluded people are not necessarily exchangeable with included people.

## Analysis decisions
The three-year horizon was chosen after reviewing event/follow-up counts at two, three, and four years, before fitting these models. The two fixed feature sets are age alone and age + nWBV. Fixed L2-regularized logistic regression (C=0.1), without hyperparameter search, uses fold-local median imputation and standardization. The small event count motivated a two-feature maximum.

Three-fold stratified cross-validation repeated ten times uses identical splits for the paired comparisons. Each repeat produces one out-of-fold score per participant; metrics are computed per repeat and averaged. Repeat ranges are split variability, not statistical confidence intervals. There is no independent test cohort. The data were already explored in phase one, so this is explicitly exploratory.

## Measured results
- Age-only mean out-of-fold ROC-AUC: 0.746.
- Age + nWBV mean out-of-fold ROC-AUC: 0.739.

At the fixed 0.5 threshold, both models classified every participant as a non-event in every repeat: sensitivity 0%, specificity 100%, balanced accuracy 50%. Their ranking AUC does not establish a useful screening decision rule.

MRI did not improve average discrimination in this pilot. Eight events are insufficient for a strong performance or clinical-use claim. AUC is not accuracy. Full metrics and source checksum: `reports/decline-results.json`.

The portable models in `models/decline-logistic.json` are refitted on all 43 included people for illustrative inference. The cross-validation estimates are not independent test results for those final refits. Their numeric outputs are not calibrated personal risk estimates.

## Reproduce
From the repository root, with dependencies installed and your own authorized workbook:

```sh
python -m neurovolume.decline --data data/oasis2.xlsx
python scripts/build_standalone.py
python -m pytest -q
```

No participant-level data are exported by this script. Training only exports aggregate reports and portable model parameters. Narrative documentation must be reviewed if the protocol or dataset changes.

## Larger-cohort extension
A stronger study should use a larger authorized longitudinal cohort, a protocol fixed before outcome modeling, careful assessment dates, interval/right-censoring-aware methods, and external validation. ADNI access is now approved; a local source-specific importer and feasibility audit are implemented, but real-data survival training remains unfinished. See [current status](STATUS.md).

## Contributions
This exploratory pilot has no external validation or established clinical use. No scientific novelty is claimed.
