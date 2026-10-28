"""Embed audited model files and local scripts into a dependency-free offline app."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = {
    'current': 'models/logistic.json', 'future': 'models/decline-logistic.json',
    'report': 'reports/results.json', 'decline': 'reports/decline-results.json',
    'audit': 'reports/synthetic-longitudinal-audit.json',
    'survivalModels': 'models/synthetic-survival.json', 'survivalReport': 'reports/synthetic-survival.json',
}


def build():
    data = {name: json.loads((ROOT / path).read_text()) for name, path in ARTIFACTS.items()}
    data['models'] = {name: data.pop(name) for name in ('current', 'future')}
    data['model_sha256'] = {
        name: hashlib.sha256((ROOT / ARTIFACTS[name]).read_bytes()).hexdigest()
        for name in ('current', 'future')
    }
    # Escape HTML delimiters in embedded JSON. The page never needs a network fetch.
    serialized = json.dumps(data, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    replacements = {'DATA': serialized}
    for key, name in [('LOGISTIC_ENGINE', 'scenarios.mjs'), ('SURVIVAL_ENGINE', 'survival.mjs'),
                      ('WORKBENCH_SCRIPT', 'workbench.js')]:
        replacements[key] = re.sub(r'^export (?=(?:function|const)\b)', '',
                                   (ROOT / 'web' / name).read_text(), flags=re.MULTILINE)
    html = (ROOT / 'web/workbench.html').read_text()
    for key, content in replacements.items():
        html = html.replace('__' + key + '__', content)
    destination = ROOT / 'standalone/index.html'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(html)
    print(f'Built offline workbench: {destination}')


if __name__ == '__main__':
    build()
