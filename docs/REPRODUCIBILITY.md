# Reproduce and inspect NeuroVolume

## Run the product

Open `standalone/index.html` directly in a browser. It embeds portable model parameters and aggregate reports; no API key, patient files or installation is required. Alternatively, from the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory standalone
```

Open http://127.0.0.1:8765/ . The standalone application includes three separate evidence levels; the synthetic survival models are not clinical predictions.

## Reproduce the original studies

Use Python 3.12. Obtain your own authorized OASIS-2 workbook using `docs/DATA.md`; place it under ignored `data/oasis2.xlsx`. From the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m neurovolume.train --data data/oasis2.xlsx
python -m neurovolume.decline --data data/oasis2.xlsx
python scripts/build_standalone.py
python -m pytest -q
```

Consult `--help` and the fixed protocols before changing any options. These commands regenerate aggregate reports and model artifacts; no public raw records are supplied. Classification seed 42; development and bootstrap seeds 2026. The workbook SHA-256 is recorded in both reports. The notebook is an additional inspectable analysis artifact.

## Reproduce synthetic survival validation

Use a separate Python 3.12 environment. The classification environment pins pandas 3.0.5; lifelines uses pandas below 3.

```sh
python3.12 -m venv .venv-survival
source .venv-survival/bin/activate
pip install -r requirements-survival.txt
python -m neurovolume.survival --synthetic --output private/synthetic-survival
python -m pytest tests/test_survival.py tests/test_longitudinal.py tests/test_adni_import.py tests/test_adni_release.py tests/test_privacy.py -q
```

Node.js is required for JavaScript parity tests. Full supported-environment testing with Node and both study dependencies recorded 55 passes and one intentional private-data skip on October 9, 2026. CI configuration is supplied; a configuration file alone is not evidence that hosted CI has passed.

Bundled synthetic artifacts are `models/synthetic-survival.json` and `reports/synthetic-survival.json`. The report records package versions, seed 20261009, split size, generator assumptions and the implementation SHA-256. Do not replace them with private ADNI artifacts for public distribution.

## Rebuild the paper and source archive

Install `reportlab` (PDF generation only), then run:

```sh
python scripts/build_paper.py
python scripts/package_release.py --output ../neurovolume-github.zip
```

`paper/NeuroVolume.md` is the editable report. PDF tables use stored JSON metrics. The source archive carries a SHA-256 manifest; private records, original workbooks, secrets and dependencies are excluded. Audit an extracted source archive using `python scripts/audit_release.py /path/to/extracted/neurovolume-github`.

## Unfinished validation

No independently tested ADNI decline model, external cohort, calibrated clinical risk, formal publication, or prospective clinical evaluation is supplied. The existing test results are already observed: do not repeatedly tune against them and continue calling them an untouched test set.
