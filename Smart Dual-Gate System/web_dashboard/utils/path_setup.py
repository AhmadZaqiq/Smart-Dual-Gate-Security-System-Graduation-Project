import sys
from pathlib import Path

from web_dashboard.config import Config


def ensure_project_root_on_path():
    project_root = str(Config.PROJECT_ROOT)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)
