"""Keep mutable databases on a persistent volume, separate from bundled datasets."""
import os
from pathlib import Path
import config  # Load local development settings before reading environment variables.


def database_path(filename, root=None):
    root = root or Path(__file__).resolve().parents[1]
    directory = Path(os.environ.get('DATA_DIR') or root / 'data').expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename
