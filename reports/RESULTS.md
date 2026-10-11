# Results

OASIS-2 first-visit CDR > 0 classification. 120 development and 30 test participants (13 positive, 17 negative).

## Primary finding

MRI added little on the held-out set: logistic AUC 0.683 → 0.688; paired delta +0.005 (95% bootstrap interval −0.158 to +0.167). Development cross-validation suggested improvement (0.677 → 0.744) that was not clearly replicated in testing. This is not evidence that MRI is generally unhelpful.

## All prespecified models

| Feature set | Algorithm | Dev CV AUC ± SD | Test AUC (95% CI) | Accuracy | Sensitivity | Specificity | Brier |
|---|---|---|---|---|---|---|---|
| Demographics | logistic | 0.677 ± 0.108 | 0.683 (0.475–0.860) | 66.7% | 61.5% | 70.6% | 0.225 |
| Demographics | forest | 0.679 ± 0.112 | 0.661 (0.452–0.846) | 56.7% | 53.8% | 58.8% | 0.229 |
| Demographics | boosting | 0.605 ± 0.105 | 0.719 (0.525–0.887) | 60.0% | 53.8% | 64.7% | 0.213 |
| Demographics + MRI | logistic | 0.744 ± 0.102 | 0.688 (0.489–0.864) | 66.7% | 53.8% | 76.5% | 0.229 |
| Demographics + MRI | forest | 0.703 ± 0.086 | 0.670 (0.466–0.851) | 60.0% | 46.2% | 70.6% | 0.219 |
| Demographics + MRI | boosting | 0.688 ± 0.096 | 0.638 (0.416–0.837) | 63.3% | 53.8% | 70.6% | 0.229 |
| Demographics + cognition | logistic | 0.882 ± 0.053 | 0.919 (0.801–0.991) | 80.0% | 76.9% | 82.4% | 0.123 |
| Demographics + cognition | forest | 0.894 ± 0.042 | 0.910 (0.778–1.000) | 86.7% | 76.9% | 94.1% | 0.106 |
| Demographics + cognition | boosting | 0.880 ± 0.055 | 0.905 (0.756–0.995) | 86.7% | 69.2% | 100.0% | 0.101 |
| Demographics + MRI + cognition | logistic | 0.898 ± 0.059 | 0.891 (0.738–1.000) | 80.0% | 69.2% | 88.2% | 0.130 |
| Demographics + MRI + cognition | forest | 0.886 ± 0.049 | 0.914 (0.783–1.000) | 90.0% | 76.9% | 100.0% | 0.115 |
| Demographics + MRI + cognition | boosting | 0.872 ± 0.067 | 0.919 (0.783–1.000) | 90.0% | 76.9% | 100.0% | 0.085 |

Some cognition-inclusive benchmarks classified 27/30 test cases correctly (90%). They were not selected as winners using this test set; their performance does not establish presymptomatic prediction or added MRI value.

Adding MRI to demographics + MMSE changed logistic AUC from 0.919 to 0.891 (delta −0.027; paired interval −0.113 to +0.041).

Training-majority baseline: 56.7% test accuracy, 50.0% balanced accuracy, AUC 0.500. Fixed threshold 0.5 throughout.

The MRI logistic model: TN=13, FP=4, FN=6, TP=7; accuracy 66.7%, sensitivity 53.8%, specificity 76.5%.

Intervals use 5,000 stratified bootstrap samples and condition on the fitted models and test class balance. CV standard deviations describe correlated fold scores, not statistical confidence. No external validation or causal inference.

![Model comparison](model-comparison.png)

Full metrics, confusion counts, source checksum and seeds: [results.json](results.json). Development fold results: [development_cv.csv](development_cv.csv).
