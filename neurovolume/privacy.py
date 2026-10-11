"""Keep participant-level outputs inside the current project's private directory."""
from pathlib import Path


def private_output(path):
    declared = Path.cwd() / "private"
    if declared.is_symlink():
        raise ValueError("Project private/ directory cannot be a symlink.")
    root = declared.resolve()
    destination = Path(path).resolve()
    if not destination.is_relative_to(root):
        raise ValueError("Real-data outputs must stay inside this project's private/ directory.")
    return destination
