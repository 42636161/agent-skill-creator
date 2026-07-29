import sys
from pathlib import Path

# Add the project root to sys.path so that 'scripts' is importable
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.skillctl.cli import main

sys.exit(main())
