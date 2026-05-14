from datetime import datetime


def get_current_time_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log(event_type, message):
    time_string = get_current_time_string()
    log_line = f"[{time_string}] [{event_type}] {message}"

    print(log_line)

    with open("logs/system.log", "a") as log_file:
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
