# Understand and present the project

## A two-minute explanation
This project asks whether MRI-derived whole-brain measurements improve classification of recorded cognitive impairment beyond demographics. It uses OASIS-2, selects one actual baseline visit per participant, and compares the same algorithms across four sets of measurements. The primary model is logistic regression, with tree-based methods as additional benchmarks.

The development data suggested an MRI improvement. The held-out data did not clearly confirm it. Cognitive scores provided stronger contemporaneous classification, but they already measure impairment. The result shows why a model's scientific question, validation design, and limitations matter alongside its accuracy.

## Questions you should be able to answer
1. **Why 150 participants instead of 373 examples?** Sessions repeat people. We use one baseline each so no person appears in both training and testing, and people with more visits receive no extra weight.
2. **Why exclude Group?** A “Converted” label can reflect future visits. Using it could turn a baseline classification task into a task containing future information.
3. **Why is CDR not an input?** CDR defines the answer. Using it as a predictor would give the model the answer directly.
4. **What is nWBV?** A precomputed fraction describing normalized whole-brain tissue volume. It is not a region-specific measurement or a raw scan.
5. **Why compare four feature sets?** To isolate the incremental contribution of MRI both before and after including a cognitive assessment.
6. **What does AUC mean?** A ranking measure: how often a randomly chosen positive example scores above a negative one, with ties given half credit. It is not accuracy.
7. **Why might 90% accuracy mislead?** It is 27 correct predictions out of only 30 for certain benchmarks. Selecting that number after comparing models is optimistic. It also includes MMSE, so it does not establish MRI improvement or presymptomatic detection.
8. **What is cross-validation doing?** Repeatedly withholding parts of development data to assess behavior without consulting final test participants.
9. **What do the intervals mean?** Approximate uncertainty for the fixed fitted models and this small test cohort. They do not establish performance in a different hospital.
10. **What did AI do?** Codex implemented this release's code, training, documentation, and tests. Describe your own actual role and learning accurately.

## Resume wording
After reviewing the project and being able to explain it, a conservative description is:

“Built an AI-assisted computational neuroscience project comparing 12 models across demographic, MRI-derived, and cognitive features in 150 OASIS-2 participants; implemented a reproducible evaluation workflow and interactive model explorer.”

If you have not personally reviewed or modified the implementation, use a narrower description:

“Directed an AI-assisted OASIS-2 classification project investigating the added value of MRI measurements, with participant-separated evaluation and an interactive research demo.”

Do not claim independent manual coding, clinical use, a novel Alzheimer diagnostic, prediction before symptoms, or a proven MRI performance improvement. Do not claim a best-model percentage without the cohort size, input features, and selection caveat.

## Make the next contribution yours
Review a wrong-prediction example locally without publishing participant information. Explain why the input features might be insufficient. Propose a change on scientific grounds, then evaluate it under a new protocol with new validation data. The existing test set is now observed and should not become an endlessly reused development target.
