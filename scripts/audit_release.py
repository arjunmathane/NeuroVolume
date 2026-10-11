"""Inspect a clean release tree for accidental private files before upload."""
import sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
forbidden={'private','data','node_modules','.git','.env','.wrangler','__pycache__','.pytest_cache','.venv','.venv-survival'}
bad=[]
for p in root.rglob('*'):
 if p.is_file() and (p.is_symlink() or set(p.relative_to(root).parts)&forbidden or any(x.startswith('.env') and x!='.env.example' for x in p.relative_to(root).parts) or p.suffix in {'.xlsx','.pem','.key'}):
  bad.append(str(p.relative_to(root)))
if bad:raise SystemExit('Excluded material found: '+', '.join(bad[:20]))
print('Clean release: no raw workbook, private audit records, dependency directories, or local secrets.')
