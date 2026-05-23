import os
from pathlib import Path

from core.fsm import MantrapFSM
from database import system_logger
from hardware import devices

PID_FILE = Path(__file__).resolve().parent / "runtime" / "mantrap.pid"


def write_pid_file():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    system_logger.log_info(f"Mantrap PID registered: {os.getpid()}")


def remove_pid_file():
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass


def main():
    try:
        write_pid_file()
        system_logger.log_info("Initializing Mantrap System")

        devices.initialize_gpio()

        mantrap_system = MantrapFSM()
        mantrap_system.run_forever()

    except KeyboardInterrupt:
        system_logger.log_info("Program stopped by user")

    except Exception as error:
        system_logger.log_error(f"Main error: {error}")

    finally:
        system_logger.log_info("Cleaning GPIO")
        devices.cleanup_gpio()
        remove_pid_file()


if __name__ == "__main__":
    main()
