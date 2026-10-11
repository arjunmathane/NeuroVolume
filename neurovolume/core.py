from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (roc_auc_score, balanced_accuracy_score, accuracy_score,
                             confusion_matrix, precision_score, brier_score_loss)

DEMOGRAPHICS = ['Age', 'Sex', 'EDUC', 'SES']
MRI = ['eTIV', 'nWBV']
FEATURES = {
    'demographics': DEMOGRAPHICS,
    'mri': DEMOGRAPHICS + MRI,
    'cognition': DEMOGRAPHICS + ['MMSE'],
    'combined': DEMOGRAPHICS + MRI + ['MMSE'],
}
LABELS = {'demographics': 'Demographics', 'mri': 'Demographics + MRI',
          'cognition': 'Demographics + cognition', 'combined': 'Demographics + MRI + cognition'}
ALGORITHMS = ['logistic', 'forest', 'boosting']
BOUNDS = {'Age': (60, 96), 'Sex': (0, 1), 'EDUC': (0, 30), 'SES': (1, 5),
          'eTIV': (900, 2200), 'nWBV': (.55, .90), 'MMSE': (0, 30)}

def baseline(path):
    """Select actual first rows; never fill a baseline field with a future visit."""
    path = Path(path)
    df = pd.read_excel(path) if path.suffix.lower() == '.xlsx' else pd.read_csv(path)
    required = {'Subject ID', 'Visit', 'CDR', 'M/F', 'Age', 'EDUC', 'SES', 'eTIV', 'nWBV', 'MMSE'}
    if not required <= set(df):
        raise ValueError(f'Missing columns: {sorted(required - set(df))}')
    if df[['Subject ID', 'Visit', 'CDR']].isna().any().any():
        raise ValueError('Identifiers, visit order, and target must be present.')
    if df.duplicated(['Subject ID', 'Visit']).any():
        raise ValueError('Duplicate participant/visit pairs.')
    if not df['M/F'].isin(['F', 'M']).all():
        raise ValueError('Expected recorded sex encoded F or M.')
    if not df.CDR.isin([0, .5, 1, 2, 3]).all():
        raise ValueError('Unexpected CDR value.')
    first = df.sort_values(['Subject ID', 'Visit']).drop_duplicates('Subject ID').copy()
    first['Sex'] = first['M/F'].map({'F': 0, 'M': 1})
    first['target'] = (first.CDR > 0).astype(int)
    return first.reset_index(drop=True), df

def pipeline(algorithm):
    if algorithm == 'logistic':
        model = LogisticRegression(C=1, max_iter=3000, random_state=42)
    elif algorithm == 'forest':
        model = RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=5,
                                       random_state=42, n_jobs=1)
    elif algorithm == 'boosting':
        model = GradientBoostingClassifier(n_estimators=100, learning_rate=.05,
                                          max_depth=2, min_samples_leaf=5, random_state=42)
    else:
        raise ValueError(f'Unknown algorithm: {algorithm}')
    return Pipeline([('impute', SimpleImputer(strategy='median')),
                     ('scale', StandardScaler()), ('model', model)])

def metrics(y, p, threshold=.5):
    y = np.asarray(y); p = np.asarray(p); pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'auc': float(roc_auc_score(y, p)),
            'balanced_accuracy': float(balanced_accuracy_score(y, pred)),
            'accuracy': float(accuracy_score(y, pred)),
            'sensitivity': float(tp / (tp + fn)), 'specificity': float(tn / (tn + fp)),
            'precision': float(precision_score(y, pred, zero_division=0)),
            'brier': float(brier_score_loss(y, p)),
            'confusion': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}}

def export_logistic(fitted, columns):
    return {'features': columns,
            'medians': fitted['impute'].statistics_.tolist(),
            'means': fitted['scale'].mean_.tolist(),
            'scales': fitted['scale'].scale_.tolist(),
            'coefficients': fitted['model'].coef_[0].tolist(),
            'intercept': float(fitted['model'].intercept_[0])}

def predict_portable(model, values):
    values = validate_values(values, model['features'])
    x = np.array([model['medians'][i] if values.get(f) is None else values[f]
                  for i, f in enumerate(model['features'])])
    z = float(np.dot((x - model['means']) / model['scales'], model['coefficients']) + model['intercept'])
    return float(1 / (1 + np.exp(-np.clip(z, -700, 700))))

def validate_values(values, features):
    extra = set(values) - set(BOUNDS)
    if extra:
        raise ValueError(f'Unexpected fields: {sorted(extra)}')
    for key in features:
        value = values.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise ValueError(f'{key} must be a finite number or null.')
        lo, hi = BOUNDS[key]
        if not lo <= value <= hi:
            raise ValueError(f'{key} must be between {lo} and {hi}.')
        if key in ('Sex', 'SES') and value != int(value):
            raise ValueError(f'{key} must be an integer.')
    return values
