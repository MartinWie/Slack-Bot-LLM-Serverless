import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# This file exists, because pytest is not able to locate the handlers module when running tests.
