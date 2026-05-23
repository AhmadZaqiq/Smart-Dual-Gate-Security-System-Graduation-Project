from web_dashboard.utils.pagination import build_pagination
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database.audit_repository import create_audit  # noqa: E402
from database.security_event_repository import (  # noqa: E402
    count_security_events,
    get_security_event_by_id,
    get_security_events_paginated,
    resolve_security_event,
)


def list_security_events(page=1, per_page=25, severity=None, event_type=None,
                         resolved=None, search_text=None):
    search_text = sanitize_search_text(search_text)

    rows = get_security_events_paginated(
        page=page,
        limit=per_page,
        severity=severity,
        event_type=event_type,
        resolved=resolved,
        search_text=search_text,
    )

    total = count_security_events(
        severity=severity,
        event_type=event_type,
        resolved=resolved,
        search_text=search_text,
    )

    return {
        "items": rows,
        "pagination": build_pagination(page, total, per_page),
    }


def get_security_event_detail(event_id):
    return get_security_event_by_id(event_id)


def resolve_event(event_id, admin_user_id, notes=None):
    success = resolve_security_event(event_id, admin_user_id, notes)

    if success:
        create_audit(
            admin_user_id=admin_user_id,
            action_type="RESOLVE_SECURITY_EVENT",
            table_name="SecurityEvent",
            record_id=event_id,
            description=notes or "Security event marked as resolved.",
        )

    return success
