"""Copy aggregate outputs and logistic parameters into the demo after training."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
out=root/'demo/lib/generated'
out.mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'reports/results.json',out/'results.json')
shutil.copyfile(root/'models/logistic.json',out/'models.json')
print('Demo synchronized with trained artifacts.')
