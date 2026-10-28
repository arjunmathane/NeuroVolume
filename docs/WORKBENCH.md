# Offline scenario workbench — v0.3.0

Open `standalone/index.html` directly in a browser. The single file contains its
scripts, model parameters and aggregate evidence; no server, installation or
internet connection is required. This is the current workbench. The separate
React demo remains the original classification-only application.

## Compare an invented pair

1. Choose **Current recorded impairment** or **Future recorded impairment · pilot**.
2. Choose the measurement set. Enter invented numeric measurements only.
3. Select **Pin as reference A**. A is an independent snapshot of those inputs.
4. Edit B. The comparison shows both model scores, their difference, and each
   feature's change in log-odds contribution. Differences use unrounded scores.
5. Download the scenario JSON. To replay it, select the file with **Restore a
   NeuroVolume scenario JSON**. Scores are recomputed from the saved measurements.

A and B always use the same study, model and preprocessing. Switching the study
or measurement set clears A. Resetting B preserves A so you can compare the
reference against the default example. A single example can also be exported
without pinning a reference.

Missing inputs remain `null` in the export. Each model uses its own training
median; the interface shows the value actually used. All-missing examples are
explicitly labeled as a training-median reference profile. Invalid numeric edits
suppress predictions and exports; they are not silently converted to missingness.

Scores are associations under a fitted model. A change in score is not a change
in clinical risk, the effect of an intervention, or evidence that changing brain
volume would change an outcome. Cross-sectional and longitudinal scores answer
different questions and must not be compared as the same endpoint.

## What a scenario file contains

- `format: "neurovolume-scenario"` and `schema_version: 1`.
- `study` (`current` or `future`) and the measurement-set key in `family`.
- `model_sha256`: SHA-256 of the exact bytes of `models/logistic.json` or
  `models/decline-logistic.json`, respectively. This identifies the parameter
  collection; it does not validate the scientific model or authenticate a file.
- A fixed research-use statement in `purpose`.
- `scenarios.a` (a reference or `null`) and `scenarios.b` (the editable example),
  each containing only that model's measurement keys and numeric/null values.

The app accepts only this schema, rejects extra fields and unsupported versions,
validates ranges/types, and refuses files whose model identity differs from the
bundled parameters. Invalid imports leave the current examples unchanged. The
file limit is 64 KB. Files contain inputs rather than a trusted cached score.
An export from a different parameter version must be reviewed separately rather
than silently reinterpreted by a newer model.

## Evidence and accessibility

The original held-out OASIS table now includes sensitivity and specificity at the
fixed 0.5 threshold. The pilot table shows mean repeated out-of-fold sensitivity
and specificity beside AUC: both pilot models had zero sensitivity at that
threshold. No model selection, retraining or new clinical validation occurred.

Synthetic survival curves have distinct solid/dashed line styles and numeric
one-, three- and five-year event-free fractions. Invalid inputs remove both the
curves and the numeric table. These are synthetic software demonstrations only.

The workbench includes a keyboard skip link, explicit field labels and hints,
visible focus states, invalid-field markers, live score/error announcements,
semantic table captions/headers, responsive layouts and print styles. Browser
checks are documented in `RELEASE_CHECKS.md`; full accessibility certification,
exhaustive cross-browser testing and clinical usability validation are not claimed.

## Privacy and development

The workbench makes no network requests and automatically stores no scenario
state. Selected files are read locally. Downloads include the entered numeric
measurements, so use invented examples and review a file before sharing it. The
external source-repository link opens only when you select it. Closing/reloading
the page clears the current examples; use an export to retain them.

Maintained sources are `web/workbench.html`, `web/workbench.js`,
`web/scenarios.mjs` and `web/survival.mjs`. Rebuild the single-file app with:

```sh
python scripts/build_standalone.py
python -m pytest -q
node --test tests/scenarios.test.mjs
```

The scenario engine is independently compared against Python portable inference
for all six OASIS logistic models on 606 invented/missing-value profiles. The
Node contract tests cover round trips, independent reference snapshots, model
mismatches, malformed files and invalid values. The generated app's actual
scripts are also exercised for comparison, atomic restore, stale-output removal,
study switching, evidence, survival tables, reset and export behavior. These
source integration tests complement browser checks; they do not replace them.
