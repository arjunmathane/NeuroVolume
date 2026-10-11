"""Build a source release excluding private records, environments and caches."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {"private", "data", "node_modules", ".git", ".wrangler", "__pycache__", ".pytest_cache", ".venv", ".venv-survival", ".vite", "dist"}


def public_file(path):
    parts = path.relative_to(ROOT).parts
    return (path.is_file() and not path.is_symlink() and not EXCLUDE.intersection(parts)
            and not any(p.startswith(".env") and p != ".env.example" for p in parts)
            and path.name != ".DS_Store" and path.suffix not in {".xlsx", ".zip", ".pyc", ".pem", ".key"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "neurovolume-github.zip")
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination.is_relative_to(ROOT):
        parser.error("Write archives outside the source tree.")
    files = sorted(p for p in ROOT.rglob("*") if public_file(p))
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, "neurovolume-github/" + str(p.relative_to(ROOT)))
        archive.writestr("neurovolume-github/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
    print(f"Packaged {len(files)} public files plus SHA-256 manifest: {destination}")


if __name__ == "__main__":
    main()
