# ADNI acquisition plan

Application approval was verified on October 9, 2026. Approval is distinct from
download, dictionary review, cohort eligibility and permission to distribute
particular derived artifacts. No account email, password or approval message is
bundled in this public repository.

Access through the official [IDA sign-in](https://ida.loni.usc.edu/login.jsp?project=ADNI&page=HOME).
Select ADNI → Download → Study Data. Obtain the clinical data dictionary from
Study info → Data & Database, plus the dictionaries and methods for chosen imaging
tables. The [ADNI FAQ](https://adni.loni.usc.edu/help-faqs/faqs/) documents this path.

Acquire the following locally into ignored `private/adni/raw/`:

- Longitudinal CDR assessments with actual assessment dates and stable participant IDs.
- MMSE assessments, demographic/birth or baseline-age information, and enrollment/visit metadata.
- Cross-sectional MRI numeric measurements, acquisition dates and quality-control fields.
- Matching clinical and imaging dictionaries, imaging methods/QC guide, release date and data-use/publication terms.

Prefer the cross-sectional UCSF FreeSurfer 7.x table (`UCSFFSX7`) for candidate
baseline MRI measurements, subject to actual coverage and QC review. Do not
substitute longitudinal FreeSurfer output that may incorporate later scans into
a baseline prediction study. ADNI's [MRI table guide](https://adni.loni.usc.edu/quick-start-guide-asset/MRI_tables.html)
distinguishes cross-sectional versus longitudinal processing and warns that
versions are not necessarily comparable.

Verify left/right hippocampal and intracranial-volume field definitions, units,
acquisition dates and QC values from the **matching** dictionary before writing an
adapter. Do not hard-code a remembered region number or use upload date as scan
date. Keep one processing version per primary analysis. Nominal visit codes alone
are insufficient to establish follow-up times.

The importer expects the [canonical schema](LONGITUDINAL_SCHEMA.md). Map IDs,
baseline CDR/MMSE dates, MRI acquisition dates and processing QC to it, then audit
duplicates, eligible follow-up, exclusions, missingness, sites and study phases.
Review precision and hold-out strategy before fitting. Never publish raw CSVs,
individual predictions, dates or real split membership.

## October 9 acquisition update

Authenticated access is working. The owner-provided archive was extracted locally
into ignored `private/adni/raw/`. It contains CDR, MMSE, PTDEMOG, ROSTER,
UCSFFSX7, DATADIC and the historical FreeSurfer methods/QC PDF. Source hashes,
dictionary definitions, missing codes and cleaning decisions are recorded locally.

The strict finalized/pass-QC FreeSurfer 7.4.1 subset is not suitable for training
the planned decline model with the declared baseline rule. The older **UCSF
Cross-Sectional FreeSurfer 5.1 [ADNI1,GO,2], November 8, 2019** release was selected
in the signed-in archive, but no completed local download was confirmed. Its
fields, quality codes and version must be reviewed before using it. Do not
substitute it into the 7.x adapter or combine the two versions.

See [importer methods](ADNI_IMPORT.md). No new ADNI model has been trained.
