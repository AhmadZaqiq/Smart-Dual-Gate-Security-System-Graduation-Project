from web_dashboard.config import Config
from web_dashboard.utils.pagination import build_pagination
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database import log_repository  # noqa: E402


def list_logs(page=1, per_page=50, level=None, search_text=None):
    search_text = sanitize_search_text(search_text)
    offset = (page - 1) * per_page

    items = log_repository.read_log_lines(
        log_path=Config.SYSTEM_LOG_PATH,
        level=level,
        search_text=search_text,
        offset=offset,
        limit=per_page,
    )

    total = log_repository.count_log_lines(
        log_path=Config.SYSTEM_LOG_PATH,
        level=level,
        search_text=search_text,
    )

    return {
        "items": items,
        "pagination": build_pagination(page, total, per_page),
    }


def tail_logs(lines=100, level=None, search_text=None):
    search_text = sanitize_search_text(search_text)

    return log_repository.tail_log_lines(
        log_path=Config.SYSTEM_LOG_PATH,
        lines=lines,
        level=level,
        search_text=search_text,
    )
