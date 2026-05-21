from datetime import datetime
from pathlib import Path

LOGS_DIRECTORY = Path("logs")
SYSTEM_LOG_FILE = LOGS_DIRECTORY / "system.log"


def ensure_logs_directory_exists():
    LOGS_DIRECTORY.mkdir(exist_ok=True)


def get_current_time_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_log_line(event_type, message):
    current_time = get_current_time_string()

    return f"[{current_time}] [{event_type}] {message}"


def write_log(event_type, message):
    ensure_logs_directory_exists()

    log_line = build_log_line(event_type, message)

    print(log_line, flush=True)

    with open(SYSTEM_LOG_FILE, "a") as log_file:
        log_file.write(log_line + "\n")


def log_info(message):
    write_log("INFO", message)


def log_warning(message):
    write_log("WARNING", message)


def log_error(message):
    write_log("ERROR", message)


def log_security(message):
    write_log("SECURITY", message)


def log_access(message):
    write_log("ACCESS", message)
