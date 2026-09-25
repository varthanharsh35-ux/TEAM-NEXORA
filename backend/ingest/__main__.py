"""Entry point for python -m backend.ingest"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
