from hardware import devices
from core.fsm import MantrapFSM
from database import system_logger


def main():
    try:
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


if __name__ == "__main__":
    main()
