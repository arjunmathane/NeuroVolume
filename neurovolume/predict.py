"""Predict from a JSON object using the portable logistic model; no pickle required."""
import argparse
import json
from pathlib import Path
from .core import predict_portable

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, help='Path to a JSON object with measurement fields')
    p.add_argument('--models', default='models/logistic.json')
    p.add_argument('--family', choices=['demographics', 'mri', 'cognition', 'combined'], default='mri')
    a = p.parse_args()
    model = json.loads(Path(a.models).read_text())[a.family]
    values = json.loads(Path(a.input).read_text())
    score = predict_portable(model, values)
    print(json.dumps({'model':a.family, 'score':score, 'threshold':.5,
                      'classification':'CDR > 0' if score >= .5 else 'CDR = 0',
                      'note':'Research classification score, not clinical risk or future decline.'}, indent=2))
