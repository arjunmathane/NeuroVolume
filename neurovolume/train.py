"""Run the fixed protocol: python -m neurovolume.train --data /path/to/oasis2.xlsx."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score, roc_curve
from .core import baseline, pipeline, metrics, export_logistic, FEATURES, LABELS, ALGORITHMS

def run(data, output):
    output = Path(output)
    for name in ['models', 'reports', 'private']:
        (output/name).mkdir(parents=True, exist_ok=True)
    base, all_visits = baseline(data)
    y = base.target.to_numpy()
    dev, test = train_test_split(np.arange(len(base)), test_size=.2, stratify=y, random_state=42)
    assert not set(base.iloc[dev]['Subject ID']) & set(base.iloc[test]['Subject ID'])
    cv = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=2026).split(dev, y[dev]))
    manifest = {'development': base.iloc[dev]['Subject ID'].tolist(), 'test': base.iloc[test]['Subject ID'].tolist(),
                'folds': [{'train': base.iloc[dev[a]]['Subject ID'].tolist(),
                           'validation': base.iloc[dev[b]]['Subject ID'].tolist()} for a,b in cv]}
    (output/'private/splits.json').write_text(json.dumps(manifest, indent=2))
    rng = np.random.default_rng(2026)
    # Stratified resampling ensures both classes occur in every test resample.
    groups = [np.flatnonzero(y[test] == k) for k in [0, 1]]
    boots = [np.concatenate([rng.choice(g, len(g), replace=True) for g in groups]) for _ in range(5000)]
    rows = []; portable = {}; test_predictions = {}; cv_rows = []
    for family, columns in FEATURES.items():
        X = base[columns]
        for algorithm in ALGORITHMS:
            key = family + '_' + algorithm
            print('Training', key, flush=True)
            fold_scores = []
            for fold, (a, b) in enumerate(cv):
                fitted = pipeline(algorithm).fit(X.iloc[dev[a]], y[dev[a]])
                score = metrics(y[dev[b]], fitted.predict_proba(X.iloc[dev[b]])[:, 1])
                fold_scores.append(score)
                cv_rows.append({'model': key, 'fold': fold, **{k:v for k,v in score.items() if k != 'confusion'}})
            fitted = pipeline(algorithm).fit(X.iloc[dev], y[dev])
            p = fitted.predict_proba(X.iloc[test])[:, 1]
            test_predictions[key] = p
            score = metrics(y[test], p)
            aucs = [roc_auc_score(y[test][b], p[b]) for b in boots]
            pred = p >= .5
            accuracies = [float(np.mean(pred[b] == y[test][b])) for b in boots]
            fpr, tpr, _ = roc_curve(y[test], p)
            rows.append({'key': key, 'family': family, 'label': LABELS[family], 'algorithm': algorithm,
                         'test': score, 'auc_ci': np.quantile(aucs, [.025,.975]).tolist(),
                         'accuracy_ci': np.quantile(accuracies, [.025,.975]).tolist(),
                         'cv_auc_mean': float(np.mean([s['auc'] for s in fold_scores])),
                         'cv_auc_sd': float(np.std([s['auc'] for s in fold_scores], ddof=1)),
                         'roc': {'fpr': fpr.tolist(), 'tpr': tpr.tolist()}})
            joblib.dump(fitted, output/'models'/f'{key}.joblib', compress=3)
            if algorithm == 'logistic':
                portable[family] = export_logistic(fitted, columns)
    differences = []
    for before, after, label in [('demographics', 'mri', 'MRI added to demographics'),
                                  ('cognition', 'combined', 'MRI added to demographics + cognition')]:
        pa, pb = test_predictions[before+'_logistic'], test_predictions[after+'_logistic']
        diffs = [roc_auc_score(y[test][b], pb[b])-roc_auc_score(y[test][b], pa[b]) for b in boots]
        differences.append({'label': label, 'before': before, 'after': after,
                            'auc_delta': float(roc_auc_score(y[test],pb)-roc_auc_score(y[test],pa)),
                            'ci': np.quantile(diffs,[.025,.975]).tolist()})
    dummy = np.repeat(float(y[dev].mean()), len(test))
    progression = all_visits.groupby('Subject ID').CDR.max().reindex(base['Subject ID']).to_numpy() > 0
    report = {'title': 'NeuroVolume', 'dataset': 'OASIS-2 official demographic workbook',
              'source_url': 'https://sites.wustl.edu/oasisbrains/home/oasis-2/',
              'source_sha256': hashlib.sha256(Path(data).read_bytes()).hexdigest(),
              'python': platform.python_version(), 'sklearn': sklearn.__version__,
              'cohort': {'participants': len(base), 'visits': len(all_visits), 'development': len(dev), 'test': len(test),
                         'baseline_positive': int(y.sum()), 'baseline_negative': int((y==0).sum()),
                         'test_positive': int(y[test].sum()), 'test_negative': int((y[test]==0).sum()),
                         'baseline_age_range': [int(base.Age.min()), int(base.Age.max())]},
              'protocol': {'split_seed': 42, 'cv_seed': 2026, 'cv_folds': 5, 'cv_repeats': 3,
                           'bootstrap_samples': 5000, 'threshold': .5, 'primary_algorithm': 'logistic'},
              'results': rows, 'differences': differences, 'dummy': metrics(y[test],dummy),
              'future_feasibility': {'initially_cdr_zero': int((y==0).sum()),
                                    'later_cdr_positive': int(((y==0)&progression).sum()),
                                    'status': 'Feasibility count only; no prognostic model trained.'}}
    (output/'reports/results.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    (output/'models/logistic.json').write_text(json.dumps(portable, indent=2, allow_nan=False))
    pd.DataFrame(cv_rows).to_csv(output/'reports/development_cv.csv', index=False)
    pd.DataFrame({'Subject ID':base.iloc[test]['Subject ID'].to_numpy(), 'target':y[test], **test_predictions}).to_csv(output/'private/test_predictions.csv', index=False)
    print(json.dumps({'differences': differences, 'cohort': report['cohort']}, indent=2), flush=True)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', default='.')
    args = parser.parse_args()
    run(args.data, args.output)
