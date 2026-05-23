"""
Parse and query the file-based system log used by system_logger.
"""

import re
from pathlib import Path

LOG_LINE_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[A-Z]+)\]\s+(?P<message>.+)$"
)

DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "system.log"


def read_log_lines(log_path=None, level=None, search_text=None, offset=0, limit=50):
    path = Path(log_path) if log_path else DEFAULT_LOG_PATH

    if not path.exists():
        return []

    parsed_lines = []

    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            raw_line = raw_line.strip()

            if not raw_line:
                continue

            match = LOG_LINE_PATTERN.match(raw_line)

            if not match:
                continue

            entry = {
                "timestamp": match.group("timestamp"),
                "level": match.group("level"),
                "message": match.group("message"),
                "raw": raw_line,
            }

            if level and entry["level"] != level.upper():
                continue

            if search_text and search_text.lower() not in entry["message"].lower():
                continue

            parsed_lines.append(entry)

    parsed_lines.reverse()
    return parsed_lines[offset: offset + limit]


def count_log_lines(log_path=None, level=None, search_text=None):
    path = Path(log_path) if log_path else DEFAULT_LOG_PATH

    if not path.exists():
        return 0

    count = 0

    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            raw_line = raw_line.strip()

            if not raw_line:
                continue

            match = LOG_LINE_PATTERN.match(raw_line)

            if not match:
                continue

            if level and match.group("level") != level.upper():
                continue

            if search_text and search_text.lower() not in match.group("message").lower():
                continue

            count += 1

    return count


def tail_log_lines(log_path=None, lines=100, level=None, search_text=None):
    path = Path(log_path) if log_path else DEFAULT_LOG_PATH

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        all_lines = log_file.readlines()

    parsed_lines = []

    for raw_line in reversed(all_lines):
        raw_line = raw_line.strip()

        if not raw_line:
            continue

        match = LOG_LINE_PATTERN.match(raw_line)

        if not match:
            continue

        entry = {
            "timestamp": match.group("timestamp"),
            "level": match.group("level"),
            "message": match.group("message"),
            "raw": raw_line,
        }

        if level and entry["level"] != level.upper():
            continue

        if search_text and search_text.lower() not in entry["message"].lower():
            continue

        parsed_lines.append(entry)

        if len(parsed_lines) >= lines:
            break

    return parsed_lines
