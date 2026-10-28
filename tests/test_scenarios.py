"""Run the offline scenario contract tests with Node's built-in test runner."""
from pathlib import Path
import json
import subprocess
import numpy as np
import pytest
from neurovolume.core import predict_portable

ROOT = Path(__file__).resolve().parents[1]


def test_scenario_contract_and_roundtrips():
    subprocess.run(['node', '--test', 'tests/scenarios.test.mjs'], cwd=ROOT,
                   check=True, capture_output=True, text=True)


@pytest.mark.parametrize('study,family', [
    ('current', 'demographics'), ('current', 'mri'), ('current', 'cognition'),
    ('current', 'combined'), ('future', 'age'), ('future', 'age_mri'),
])
def test_workbench_engine_matches_python(study, family):
    filename = 'logistic.json' if study == 'current' else 'decline-logistic.json'
    model = json.loads((ROOT / 'models' / filename).read_text())[family]
    rng = np.random.default_rng(20261028)
    cases = []
    for i in range(100):
        row = {'Age': int(rng.integers(60, 97)), 'Sex': int(rng.integers(0, 2)),
               'EDUC': int(rng.integers(0, 31)), 'SES': int(rng.integers(1, 6)),
               'eTIV': float(rng.uniform(900, 2200)), 'nWBV': float(rng.uniform(.55, .9)),
               'MMSE': int(rng.integers(0, 31))}
        if i % 3 == 0:
            row[model['features'][i % len(model['features'])]] = None
        cases.append(row)
    cases.append({feature: None for feature in model['features']})
    script = "import {inferScenario} from './web/scenarios.mjs';let text='';for await(const chunk of process.stdin)text+=chunk;const {model,cases}=JSON.parse(text);console.log(JSON.stringify(cases.map(row=>inferScenario(model,row).score)));"
    actual = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                            input=json.dumps({'model': model, 'cases': cases}),
                            capture_output=True, text=True, check=True)
    np.testing.assert_allclose(json.loads(actual.stdout),
                               [predict_portable(model, row) for row in cases],
                               rtol=1e-12, atol=1e-12)
