# NeuroVolume release checks

## October 9, 2026 acquisition and browser update

- Full supported-environment suite: **55 passed, one intentionally skipped private-data audit**. Added invented-export cleaning, dictionary mapping, missing-code, timing, QC and private-path protection tests.
- Clinical tables, cross-sectional FreeSurfer 7.x data, the matching dictionary and historical QC guide acquired into local ignored storage. The 7.4.1 adapter performed a feasibility audit; no ADNI model was fitted.
- Older 5.1 MRI release selected in the authenticated archive. Individual and batch download actions did not produce a confirmed local file. Further acquisition remains unfinished.
- Standalone application served at localhost and visually inspected in Chrome. Interactive MRI changes, invalid-age handling, reset and study switching verified. A synthetic report saved to Downloads was confirmed on disk.
- Public app status now distinguishes approved access/import software from pending real-data survival validation.
- Synthetic artifacts regenerated after private-output protection changed, preserving deterministic model results and refreshing implementation hashes.
- Public source archive rebuilt with a manifest and independently audited for private-data exclusions and checksum consistency.

## Earlier October 9, 2026 framework milestone

- Interval-censored Weibull framework and held-out synthetic experiment implemented. 600 invented participants; 450 training and 150 test. No ADNI model or external validation claimed.
- Twelve additional survival tests cover likelihood/censoring, browser/Python/lifelines parity, training-only preprocessing, curve validity, independent-seed imposed-effect recovery, invalid records and artifact consistency.
- Generated standalone scripts are exercised in Node with a minimal DOM adapter: real study switching, synthetic curve changes, missing MMSE, invalid age, reset and download handler. This is source integration testing, not visual browser verification or a confirmed saved download.
- Optional survival dependencies have a separate environment and CI job, preserving original-study dependencies.
- ADNI approval verified from the September 9 approval email. Controlled acquisition blocked at IDA sign-in because Cloudflare Turnstile failed to load.
- Local HTTP-server launch was denied by the execution sandbox; automated browser navigation to local file URLs was blocked by the browser's security policy. No alternate browser route was used. New page layout has not received visual browser QA in this session.
- Final supported-environment suite: 38 passed, one private-data split audit intentionally skipped. Standalone source integration and Python/browser/native survival parity passed.
- Release packaging includes a SHA-256 manifest and excludes raw workbooks, private records, environments, dependencies and secrets. The extracted archive receives a separate exclusion audit.

## September 9 pilot checks

- 17 automated tests passed; one private-data split audit was skipped in the public package as intended.
- Synthetic longitudinal cases verify short follow-up exclusion, later positive-visit uncertainty, return-to-zero handling, and preservation of baseline predictors.
- Portable prognostic inference agrees with fitted sklearn logistic regression.
- Browser checks verified study switching, future-model rendering, invalid-age handling, and reset behavior.
- The displayed future example score (age 75, nWBV 0.74) was 0.175, matching Python inference to the displayed precision.
- Desktop layout was visually inspected. Exhaustive cross-browser/accessibility testing has not been performed.
- Standalone source embeds all model parameters and aggregate reports; no external resource requests or patient upload features are present.
- The original hosted React app remains phase one only. The new standalone application contains both studies.

## Next-study preparation checks
- 25 tests passed; one private-data audit skipped as intended in the public bundle.
- New synthetic tests cover interval bounds, censoring, reversion, unavailable baseline assessment, follow-up exclusions, future MRI exclusion, QC, duplicate records, unknown IDs, missing dates, invalid CDR and unit mismatches.
- Standalone JavaScript passed syntax checking.
- No larger-cohort prognostic fit or external validation is claimed.
- Browser audit rendering was verified. The automated download-event check timed out; saving the exported report has not been confirmed through the browser tool. The same audit is available in reports/synthetic-longitudinal-audit.json.
