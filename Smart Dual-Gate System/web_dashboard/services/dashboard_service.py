from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from database import dashboard_repository  # noqa: E402
from database.access_session_repository import get_recent_access_sessions  # noqa: E402
from database.security_event_repository import get_recent_security_events  # noqa: E402


def get_overview_summary():
    summary = dashboard_repository.get_dashboard_summary() or {}

    return {
        "total_employees": summary.get("TotalEmployees", 0),
        "active_employees": summary.get("ActiveEmployees", 0),
        "completed_sessions": summary.get("CompletedSessions", 0),
        "active_sessions": summary.get("ActiveSessions", 0),
        "successful_authentications": summary.get("SuccessfulAuthentications", 0),
        "failed_authentications": summary.get("FailedAuthentications", 0),
        "security_events": summary.get("SecurityEvents", 0),
        "today_access_count": dashboard_repository.get_today_access_count(),
        "today_failed_attempts": dashboard_repository.get_today_failed_attempts(),
        "today_security_events": dashboard_repository.get_today_security_events_count(),
    }


def get_recent_activity(limit=20):
    return dashboard_repository.get_recent_activity(limit)


def get_recent_access(limit=5):
    return get_recent_access_sessions(limit)


def get_recent_security(limit=5):
    return get_recent_security_events(limit)


def get_access_chart(days=7):
    return dashboard_repository.get_access_chart_data(days)


def get_security_chart(days=7):
    return dashboard_repository.get_security_chart_data(days)


def get_security_type_chart(days=7):
    return dashboard_repository.get_security_events_by_type_chart(days)
