from web_dashboard.utils.pagination import build_pagination
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database.access_session_repository import (  # noqa: E402
    count_access_sessions,
    get_access_session_by_id,
    get_access_sessions_paginated,
)
from database.database_manager import execute_query  # noqa: E402


def list_access_sessions(page=1, per_page=25, final_status=None, search_text=None,
                         date_from=None, date_to=None):
    search_text = sanitize_search_text(search_text)

    rows = get_access_sessions_paginated(
        page=page,
        limit=per_page,
        final_status=final_status,
        search_text=search_text,
        date_from=date_from,
        date_to=date_to,
    )

    total = count_access_sessions(
        final_status=final_status,
        search_text=search_text,
        date_from=date_from,
        date_to=date_to,
    )

    return {
        "items": rows,
        "pagination": build_pagination(page, total, per_page),
    }


def get_access_session_detail(access_session_id):
    session_row = get_access_session_by_id(access_session_id)

    if not session_row:
        return None

    attempts = execute_query(
        """
        SELECT *
        FROM AuthenticationAttempt
        WHERE AccessSessionID = ?
        ORDER BY AuthenticationAttemptID DESC;
        """,
        (access_session_id,),
    )

    return {
        "session": session_row,
        "attempts": attempts,
    }
