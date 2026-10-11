# NeuroVolume: Evaluating the Incremental Value of MRI-Derived Brain Measurements

## A reproducible cognitive-impairment benchmark and longitudinal modeling workbench

Project lead: Arjun Mathane | Independent educational project, TAMS / University of North Texas

Technical report v0.2 | October 11, 2026 | Not peer reviewed

Prepared with OpenAI Codex. Project direction was provided by Arjun Mathane; Codex implemented the analyses, software, tests, interface, and this report. No independent manual implementation, institutional endorsement, or human scientific review is asserted.

## Abstract

Objective: Evaluate whether MRI-derived volume measurements add discrimination beyond demographic predictors for recorded cognitive impairment, and develop a transparent framework for later longitudinal work.

Methods: The OASIS-2 measurement workbook supplied 373 sessions from 150 people. One earliest visit per participant was used to classify Clinical Dementia Rating (CDR) > 0 versus CDR = 0. Four feature sets and three fixed model families yielded 12 benchmarks. A stratified participant split allocated 120 people to development and 30 to testing. A separate exploratory three-year pilot included 43 participants and eight events. An interval-censored Weibull framework was tested on 600 invented participants; this experiment was software validation only.

Results: In the primary logistic comparison, test ROC-AUC changed from 0.683 with demographics to 0.688 with demographics plus MRI. The paired difference was +0.005, with a 95% bootstrap interval of -0.158 to +0.167. The future-impairment pilot had mean repeated out-of-fold AUCs of 0.746 for age and 0.739 for age plus normalized brain volume; both models had zero sensitivity at the fixed threshold. In the synthetic survival experiment, the mean held-out observation log likelihood improved by 0.059 with MRI, but its interval included zero and the MRI effect was imposed by the generator.

Conclusion: These analyses do not establish incremental MRI value or clinical utility. The contribution is an auditable research workbench that preserves participant separation, missingness, censoring, and the distinction between real evidence and synthetic software tests. Real-data ADNI survival training and external validation remain unfinished.

## 1. Introduction

Brain measurements can be investigated as predictors without assuming that a successful benchmark is a diagnostic product. OASIS-2 provides longitudinal MRI-derived measurements and clinical assessments from older adults [1]. This project asks a narrower question: does adding volume information improve a predefined comparator on participants excluded from model fitting?

The work comprises three distinct evidence levels: a held-out classification analysis, an exploratory longitudinal pilot, and a synthetic survival experiment. Their outcomes, validation designs, and scientific interpretations are reported separately. Transparent reporting is informed by TRIPOD+AI [2]; this educational report does not claim formal checklist compliance or clinical validation.

---page---

## 2. Classification methods

### 2.1 Data and target

The official OASIS-2 workbook was retrieved on September 6, 2026. The actual earliest row for each participant was retained, preserving missing values. The operational target was baseline CDR > 0, including CDR 0.5. The workbook yielded 65 positive and 85 negative participants, ages 60-96. These counts describe the chosen workbook target and need not match the source publication's clinical diagnostic groups.

The model accepts precomputed numeric measurements, not MRI images. It classifies recorded impairment associated with the first visit; it does not establish a biomarker-confirmed Alzheimer diagnosis. The source study reports offsets between MRI and clinical assessments [1], so this is an associated-visit comparison rather than a precisely synchronized clinical experiment.

### 2.2 Predictors and leakage prevention

Demographics comprised age, recorded sex (F=0, M=1), education in years, and socioeconomic class. The MRI increment comprised estimated total intracranial volume (eTIV, cm3) and normalized whole-brain volume (nWBV, fraction). Cognition-inclusive analyses added the Mini-Mental State Examination (MMSE) score.

The four feature sets were demographics; demographics plus MRI; demographics plus cognition; and demographics plus MRI plus cognition. CDR, the longitudinal Group label, identifiers, visit number, timing, and future measurements were excluded from predictors. Group can encode subsequent conversion and would leak future information. Atlas scaling factor was omitted because it is redundant with intracranial scaling. Handedness offered no useful variation.

### 2.3 Models and evaluation

A stratified 80/20 participant split used seed 42. The 120-person development set used five-fold stratified cross-validation repeated three times (seed 2026), with identical folds across models. The independent 30-person test set contained 13 positives and 17 negatives. Median imputation and standardization were learned only from the relevant training fold.

Logistic regression was the primary model (L2 penalty, C=1, maximum 3,000 iterations). Random forest (200 trees, depth 4, minimum leaf size 5) and gradient boosting (100 estimators, learning rate 0.05, depth 2, minimum leaf size 5) were fixed benchmarks. The protocol recorded these settings before fitting results; it was not externally preregistered. No hyperparameter search, test-guided threshold selection, or model selection was performed.

ROC-AUC was primary; accuracy, balanced accuracy, sensitivity, specificity, precision, Brier score, and confusion counts were also saved. The threshold was fixed at 0.5. Test intervals used 5,000 stratified participant bootstrap resamples (seed 2026), paired across feature-set comparisons. These intervals condition on the fitted models and class balance; they do not include training or site uncertainty. Cross-validation standard deviations describe correlated fold variation, not confidence intervals.

### 2.4 Reproducibility scope

The four logistic demo models and all 12 saved classification pipelines retain development-only fitting. Public materials include aggregate metrics, model parameters, code, protocols, and synthetic examples. The source workbook, participant identifiers, split memberships, and individual predictions are excluded. Users must obtain their own authorized data copy under current OASIS terms.

---page---

## 3. Classification results

The primary demographic logistic model achieved test AUC 0.683; adding MRI yielded 0.688. The paired AUC gain was 0.005 (95% bootstrap interval -0.158 to +0.167). Development mean cross-validation AUC increased from 0.677 to 0.744, but the small held-out set did not clearly confirm an incremental benefit.

[Table 1: see the PDF or complete results](../reports/RESULTS.md)

Table 1. Fixed logistic models evaluated on the same 30 held-out participants. Intervals are stratified bootstrap intervals conditional on fitted models. These are contemporaneous CDR-based results, not future-risk estimates.

![Figure 1: held-out logistic model comparison](../reports/model-comparison.png)

Figure 1. Held-out AUCs and ROC curves for the four fixed logistic feature sets. Error bars express conditional test uncertainty; all 12 benchmark results are reported in Appendix A, without selecting the largest observed value as a validated winner.

Adding MRI to demographics plus MMSE changed logistic AUC from 0.919 to 0.891 (paired difference -0.027; interval -0.113 to +0.041). Cognitive scores measure a related clinical construct and must be interpreted separately from MRI-only incremental value.

The demographics-plus-MRI logistic confusion counts were 13 true negatives, four false positives, six false negatives, and seven true positives. Accuracy was 66.7%, sensitivity 53.8%, and specificity 76.5%. Some cognition-inclusive tree benchmarks classified 27 of 30 participants correctly (90%); this observation does not demonstrate detection before symptoms or generalizable clinical accuracy.

The training-majority comparator achieved 56.7% accuracy, 50.0% balanced accuracy, and AUC 0.500. The data do not support a broad conclusion that MRI is unhelpful; the result is an imprecise incremental-value estimate in one selected cohort. All benchmark metrics are provided in Appendix A and the machine-readable reports.

---page---

## 4. Exploratory longitudinal pilot

The separate endpoint was first recorded CDR > 0 within 1,095 MRI-delay days after baseline CDR = 0. Event participants had a first positive visit within the horizon. Non-events required an observed zero-CDR visit at or beyond the horizon before any first positive assessment. Short follow-up was not treated as a negative outcome; later return to CDR = 0 did not erase the first positive event.

Of 85 baseline-eligible participants, 43 were included: eight events and 35 non-events. The remaining 42 lacked sufficient observed follow-up. The three-year horizon was chosen after reviewing two-, three-, and four-year follow-up/event counts, before fitting. The data had already been explored in phase one, making this explicitly exploratory. MRI session intervals approximate, rather than precisely identify, clinical timing.

Age-only and age-plus-nWBV logistic models used fixed C=0.1, fold-local imputation and standardization, and identical three-fold stratified splits repeated ten times. Each repeat supplied one out-of-fold prediction per person. Mean repeated out-of-fold AUC was 0.746 for age and 0.739 with nWBV; Brier scores were 0.146 and 0.145, respectively.

At the fixed 0.5 threshold, both models predicted every participant as a non-event in every repeat: sensitivity 0%, specificity 100%, and balanced accuracy 50%. Thus the ranking AUC does not establish a usable screening classifier. Repeat ranges are split variation, not confidence intervals. There was no independent test cohort. The illustrative browser models were subsequently refitted on all 43 included participants; internal-validation estimates are not independent evaluations of those final refits.

## 5. Synthetic interval-censored survival experiment

The implemented framework preserves uncertainty between the last zero-CDR assessment (L) and first positive assessment (U). Right-censored observations contribute follow-up without inventing an event time. Weibull accelerated failure-time models were fitted using lifelines [3]. They compare age plus MMSE with age plus MMSE plus bilateral hippocampal volume divided by intracranial volume, using fixed L2 penalization 0.01 and training-only imputation/scaling.

The fixed generator created 600 invented participants, six-month assessments, independent censoring, and a deliberately imposed MRI association. A stratified 75/25 split (seed 20261009) allocated 450 participants to training and 150 to testing; the test set had 48 interval-observed events and 102 censored observations. These records do not represent actual patients.

Held-out event observations were scored as log[S(L)-S(U)]; censored observations as log[S(L)]. Mean log likelihood was -1.112 for age plus cognition and -1.053 with MRI. The paired mean difference was 0.059; 5,000 test-participant bootstrap resamples yielded an interval of -0.004 to +0.116. This interval conditions on fitted models and omits training uncertainty.

Higher observation likelihood is better under the model assumptions; it is not percent accuracy or a calibrated clinical risk. No interval midpoint labels, exact latent onset times, standard right-censored AUC, or horizon Brier scores were substituted. The imposed effect and Weibull assumptions make this software verification, not evidence for biological predictive value.

---page---

## 6. Software and controlled-data extension

The standalone HTML workbench contains the OASIS models, pilot, synthetic cohort audit, and interactive survival curves. Inference runs locally without a ChatGPT account, API key, or participant-upload feature. Portable JSON parameters support browser inference. Python, JavaScript, and native lifelines predictions are compared in automated tests. Source protocols, input schemas, dependency files, and CI configuration accompany the code.

The October 9 supported-environment check recorded 55 passing tests and one intentionally skipped private-data audit. Tests cover training-only preprocessing, participant separation, interval likelihood, missing scores, unit constraints, invalid records, scan quality, date ordering, duplicate outcomes, and output-path protection. Chrome desktop checks confirmed study switching, curve changes, invalid-input handling, reset, and a saved synthetic report. This is not comprehensive usability, accessibility, security, or cross-browser validation.

ADNI access has been approved and a local dictionary-reviewed importer implemented. It checks scan acquisition dates, clinical dates, field definitions, missing codes, QC status, processing version, and private output paths. The reviewed cross-sectional MRI subset did not support the planned decline fit under the declared rules. An older release is needed; no ADNI model or ADNI performance result is reported. Controlled records, cohort rows, split membership, and derived private models are excluded from this public report and repository. Source-specific decisions and remaining acquisition work are documented in the repository [4].

## 7. Discussion and limitations

The principal empirical finding is that MRI did not show a clear held-out increment over demographics in this small analysis. The longitudinal pilot likewise did not demonstrate added nWBV value, and its fixed-threshold sensitivity was zero. A defensible negative or inconclusive comparison is more informative than selecting a favorable benchmark headline.

Limits include the small single-cohort test set, a selected older population, coarse whole-brain measurements, imperfect assessment timing, correlated internal-validation folds, incomplete follow-up selection, and uncertainty conditional on fitted models. Comprehensive subgroup fairness, external validity, horizon calibration, clinical net benefit, and prospective usefulness were not established. CDR-based recorded impairment is not exact disease onset or biomarker-confirmed Alzheimer disease. Associative predictors do not identify biological causes.

The survival framework assumes a Weibull time distribution, independent censoring, and a noninformative assessment schedule. CDR can fluctuate; first recorded threshold crossing is not an established latent biological transition. Synthetic validation cannot resolve these real-cohort assumptions. Before real outcome fitting, event counts, site coverage, prediction origin, horizon support, baseline amendments, evaluation design, and precision targets must be documented.

## 8. Contributions, ethics, and availability

Arjun Mathane selected and directed the project. Codex implemented the protocol documents, analysis, training, tests, application, and report. No completed independent human scientific review or manuscript approval is asserted. The original cohort investigators collected the data. This is a self-published technical report, not a journal publication, peer-reviewed discovery, or clinically deployed product.

No participants were recruited by this project. Original study ethics oversight is described by its investigators [1]; no new IRB approval, exemption, or institutional sponsorship is claimed here. No external project funding or conflict-of-interest review is documented in the project records. These statements should be revisited if the project is submitted for formal publication.

Code and evidence: https://github.com/arjunmathane/NeuroVolume . The original code is MIT licensed; dataset, model-artifact, and third-party terms remain separate. A reproducibility guide, provenance record, model card, contribution statement, reporting map, and claim boundaries are supplied. No DOI has been assigned.

---page---

## References

[1] Marcus DS, Fotenos AF, Csernansky JG, Morris JC, Buckner RL. Open Access Series of Imaging Studies (OASIS): Longitudinal MRI Data in Nondemented and Demented Older Adults. Journal of Cognitive Neuroscience. 2010;22(12):2677-2684. https://doi.org/10.1162/jocn.2009.21407

[2] Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. https://doi.org/10.1136/bmj-2023-078378

[3] lifelines contributors. WeibullAFTFitter, lifelines 0.30.3 documentation. https://lifelines.readthedocs.io/en/latest/fitters/regression/WeibullAFTFitter.html . Accessed October 11, 2026.

[4] NeuroVolume project. Source code, protocols, model cards, and aggregate reports, v0.2. https://github.com/arjunmathane/NeuroVolume . Technical report prepared October 11, 2026.

## Required OASIS acknowledgement

Data were provided by OASIS. OASIS-2: Longitudinal: Principal Investigators: D. Marcus, R. Buckner, J. Csernansky, J. Morris; P50 AG05681, P01 AG03991, P01 AG026276, R01 AG021910, P20 MH071616, U24 RR021382.

## Appendix A. Complete classification benchmark

[Table A1: complete classification results](../reports/RESULTS.md)

Table A1. D = demographics; M = MRI; C = cognition. All values are held-out results; sensitivity and specificity use the fixed 0.5 threshold. Full bootstrap intervals, confusion counts, development folds, source checksum, and seeds are in reports/results.json and reports/development_cv.csv. Forest and boosting are benchmarks, not selected winners.

## Appendix B. Evidence inventory

Classification: reports/results.json and docs/PROTOCOL.md. Longitudinal pilot: reports/decline-results.json and docs/FUTURE_DECLINE.md. Synthetic survival: reports/synthetic-survival.json and docs/SURVIVAL_FRAMEWORK.md. Source provenance: docs/DATA.md. Controlled-data adapter: docs/ADNI_IMPORT.md. Reproduction: docs/REPRODUCIBILITY.md. Contributions: docs/CONTRIBUTIONS.md. Claim boundaries and resume wording: docs/RESUME_EVIDENCE.md. Status and verification: docs/STATUS.md and docs/RELEASE_CHECKS.md.

