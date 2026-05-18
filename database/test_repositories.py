from database.dashboard_repository import get_dashboard_summary
from database.employee_repository import get_all_employees
from database.access_session_repository import get_recent_access_sessions
from database.authentication_attempt_repository import get_recent_authentication_attempts
from database.security_event_repository import get_recent_security_events


def main():
    print("[TEST] Employees:")
    print(get_all_employees())

    print("[TEST] Dashboard Summary:")
    print(get_dashboard_summary())

    print("[TEST] Recent Access Sessions:")
    print(get_recent_access_sessions())

    print("[TEST] Recent Authentication Attempts:")
    print(get_recent_authentication_attempts())

    print("[TEST] Recent Security Events:")
    print(get_recent_security_events())


if __name__ == "__main__":
    main()
