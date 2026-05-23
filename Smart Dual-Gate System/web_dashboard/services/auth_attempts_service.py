from web_dashboard.utils.pagination import build_pagination
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database.authentication_attempt_repository import (  # noqa: E402
    count_authentication_attempts,
    get_authentication_attempt_by_id,
    get_authentication_attempts_paginated,
)


def list_authentication_attempts(page=1, per_page=25, final_result=None,
                                 search_text=None, employee_id=None):
    search_text = sanitize_search_text(search_text)

    rows = get_authentication_attempts_paginated(
        page=page,
        limit=per_page,
        final_result=final_result,
        search_text=search_text,
        employee_id=employee_id,
    )

    total = count_authentication_attempts(
        final_result=final_result,
        search_text=search_text,
        employee_id=employee_id,
    )

    return {
        "items": rows,
        "pagination": build_pagination(page, total, per_page),
    }


def get_authentication_attempt_detail(attempt_id):
    return get_authentication_attempt_by_id(attempt_id)
