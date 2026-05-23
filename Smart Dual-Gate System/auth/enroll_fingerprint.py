"""
Fingerprint enrollment status simulator for dashboard wizard.
On Pi, replace with real PyFingerprint enrollment integration.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "runtime" / "enrollment_status.json"

STEPS = [
    ("waiting", "Place finger on sensor"),
    ("scan_1", "Remove finger"),
    ("scan_2", "Place same finger again"),
    ("processing", "Processing fingerprint template"),
    ("success", "Fingerprint enrolled successfully"),
]


def write_status(state, message, step=None, total=None, position=None):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "fingerprint",
        "state": state,
        "message": message,
        "step": step,
        "total": total,
        "position": position,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)


def main():
    total = len(STEPS)

    for index, (state, message) in enumerate(STEPS, start=1):
        write_status(state, message, step=index, total=total)
        time.sleep(2)

    write_status("success", "Fingerprint enrolled successfully.", step=total, total=total, position=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
