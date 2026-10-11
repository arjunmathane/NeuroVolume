# Resume evidence and claim boundaries

## Suggested extended-resume entry

**NeuroVolume | Project Lead, AI-assisted Computational Neuroscience**

Directed development of a reproducible research workbench comparing 12 classifiers on 150 OASIS-2 participants, with participant-separated evaluation and an exploratory 43-person longitudinal pilot. Extended the software with interval-censored survival modeling validated on 600 synthetic participants, portable browser inference, and 55 passing automated tests. Documented inconclusive MRI gains, model limitations, data provenance, and AI contributions in a public technical report and repository.

Repository: https://github.com/arjunmathane/NeuroVolume

Report: https://github.com/arjunmathane/NeuroVolume/blob/main/paper/NeuroVolume.pdf

## Compact entry

Directed NeuroVolume, an AI-assisted neuroscience workbench comparing 12 models across 150 OASIS-2 participants; released reproducible code, a browser explorer and a technical report with transparent validation and limitations.

## What the evidence supports

- Inspectable code, learned OASIS models, aggregate results and synthetic examples.
- Original classification: 120 development and 30 held-out participants; MRI logistic AUC changed 0.683 to 0.688, with uncertainty spanning zero added value.
- Exploratory future pilot: 43 included participants, eight events, no independent test. Both fixed-threshold models had zero sensitivity.
- Synthetic survival framework: 600 invented participants, 150 held out. No real-patient prediction performance inferred from this test.
- 55 passing checks and one intentional private-data audit skip in the supported local environment. Tests are software verification, not clinical validation.
- Public technical report and GitHub repository; no peer review or DOI.

## Claims to avoid

Do not claim independent manual implementation, a clinically validated Alzheimer detector, presymptomatic detection, demonstrated MRI improvement, ADNI model accuracy, independent future-prediction validation, peer-reviewed publication, or deployment in patient care. Do not list selected 90% test accuracy without explaining that it arose from cognition-inclusive benchmarks on only 30 test participants.

The repository documents the work; it does not independently certify what the project lead knows. Describe personal review, modifications, research interpretation or user testing only if actually performed.
