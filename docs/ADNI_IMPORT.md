# Controlled-data importer

The generic `neurovolume.adni_import` adapter converts explicitly mapped source
tables into the canonical longitudinal schema and performs a feasibility audit.
It does not train a model. Mapping configuration supplies the source columns,
date formats, volume units, QC pass/fail values, missing codes, processing version
and a checksum for the reviewed dictionary. A checksum proves artifact identity,
not that a human interpretation or data-use authorization is correct.

`neurovolume.adni_release` implements one reviewed source: the October 9, 2026
clinical export and UCSFFSX7 FreeSurfer **7.4.1** cross-sectional measurements.
It cannot be reused for another MRI release without source review.

From the repository root, with the survival environment installed:

```sh
python -m neurovolume.adni_release --raw private/adni/raw --output private/adni/prepared7
```

Check the command's `--help` before use. All real-data outputs are constrained to
the current project's `private/` directory, including protection against a
symlink redirect. Public release packaging excludes that directory.

## Reviewed decisions

- CDR `CDGLOBAL`: 0, 0.5, 1, 2, 3; -1 and missing values are unavailable.
- MMSE `MMSCORE`: 0–30; -1 or a procedure marked not done becomes missing.
- Clinical rows marked `HAS_QC_ERROR=1` are excluded.
- Clinical `VISDATE` is an assessment date where supplied and otherwise a
  registry date according to the phase dictionary. It is not universally an
  exact assessment date; timing uncertainty remains a study limitation.
- MRI `EXAMDATE` is acquisition date. Left/right hippocampus fields are `ST29SV`
  and `ST88SV`; intracranial volume is `ST10CV`. Dictionary units are mm3.
- Retain only `STATUS=complete`, `OVERALLQC=Pass`, `HIPPOQC=Pass`, `FSVER=7.4.1`.
  The 2014 PDF supplies historical QC context, not full 7.4.1 pipeline validation.
- Same-day conflicting CDR observations exclude the participant. Identical
  duplicates collapse. Conflicting same-day MMSE scores become missing.
- Among passing same-date scans choose the smallest numeric IMAGEUID, then the
  latest RUNDATE for the same image. This rule is independent of outcomes.
- Actual PTDOB values are month/year despite broader dictionary date metadata.
  Age is approximate, calculated using the midpoint of that month; uncertainty
  is about half a month. Only demographic information available by baseline is
  used. No exact birthday is inferred and no future correction fills baseline.

The default baseline is the earliest observed CDR assessment. MRI must be on or
before baseline within 180 days; MMSE is the most recent assessment on or before
baseline within 30 days. A missing score is retained for later training-only
imputation, never filled using a later visit.

The generic adapter also supports a **first eligible** baseline for sensitivity
audits: the first zero-CDR visit with a prior passing MRI in the timing window,
with no prior positive CDR. This starts a different prediction population and
time origin; making it primary requires a documented protocol amendment before
fitting. It must never rebaseline a participant after observed impairment.

Invented-export tests cover conflicting outcomes, scan tie handling, QC failure,
future demographics, missing cognition and identifier preservation. No real
records or split membership are test fixtures or public deliverables.
