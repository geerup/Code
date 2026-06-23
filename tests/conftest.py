import sys
from pathlib import Path

# Make the src-layout package importable without an install step.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
