from web_dashboard.utils.pagination import build_pagination
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database.audit_repository import get_recent_audits  # noqa: E402
from database.database_manager import execute_query, execute_query_one  # noqa: E402


def list_audits(page=1, per_page=50, search_text=None, table_name=None, action_type=None):
    search_text = sanitize_search_text(search_text)
    offset = (page - 1) * per_page

    filters = []
    params = []

    if table_name:
        filters.append("AU.TableName = ?")
        params.append(table_name)

    if action_type:
        filters.append("AU.ActionType = ?")
        params.append(action_type)

    if search_text:
        filters.append(
            "(AU.Description LIKE ? OR AU.ActionType LIKE ? OR AD.UserName LIKE ?)"
        )
        value = f"%{search_text}%"
        params.extend([value, value, value])

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT
            AU.AuditID,
            AU.AdminUserID,
            AD.UserName,
            P.FirstName || ' ' || P.LastName AS AdminName,
            AU.ActionType,
            AU.TableName,
            AU.RecordID,
            AU.OldValue,
            AU.NewValue,
            AU.Description,
            AU.CreationDate
        FROM Audit AU
        LEFT JOIN AdminUser AD ON AD.AdminUserID = AU.AdminUserID
        LEFT JOIN Person P ON P.PersonID = AD.PersonID
        {where_clause}
        ORDER BY AU.AuditID DESC
        LIMIT ? OFFSET ?;
    """

    params.extend([per_page, offset])
    items = execute_query(query, tuple(params))

    count_query = f"""
        SELECT COUNT(*) AS Total
        FROM Audit AU
        LEFT JOIN AdminUser AD ON AD.AdminUserID = AU.AdminUserID
        {where_clause};
    """

    count_params = params[:-2]
    total_row = execute_query_one(count_query, tuple(count_params))
    total = total_row["Total"] if total_row else 0

    return {
        "items": items,
        "pagination": build_pagination(page, total, per_page),
    }
