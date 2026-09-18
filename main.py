"""Entry point so the app can be started from the repo root.

The application itself lives in code/main.py; this just runs it so that
`python main.py` and `python code/main.py` behave identically.
"""

import runpy
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent / "code"

if __name__ == "__main__":
    sys.path.insert(0, str(CODE_DIR))
    runpy.run_path(str(CODE_DIR / "main.py"), run_name="__main__")
