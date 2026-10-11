from pathlib import Path
import subprocess


def test_generated_standalone_behaviors():
    root = Path(__file__).resolve().parents[1]
    subprocess.run(["node", "tests/standalone_smoke.mjs"], cwd=root, check=True, capture_output=True, text=True)
