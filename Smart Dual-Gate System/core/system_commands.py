"""
Dashboard-to-FSM command bridge (read by mantrap process only).
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
COMMANDS_FILE = RUNTIME_DIR / "system_commands.json"


def _ensure_runtime_dir():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def publish_command(command_type, payload=None):
    _ensure_runtime_dir()

    command = {
        "type": command_type,
        "payload": payload or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "consumed": False,
    }

    fd, temp_path = tempfile.mkstemp(dir=str(RUNTIME_DIR), suffix=".tmp")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(command, temp_file, indent=2)
        os.replace(temp_path, COMMANDS_FILE)
    except OSError:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def consume_pending_command():
    _ensure_runtime_dir()

    if not COMMANDS_FILE.exists():
        return None

    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as command_file:
            command = json.load(command_file)
    except (json.JSONDecodeError, OSError):
        return None

    if command.get("consumed"):
        return None

    command["consumed"] = True

    with open(COMMANDS_FILE, "w", encoding="utf-8") as command_file:
        json.dump(command, command_file, indent=2)

    return command
