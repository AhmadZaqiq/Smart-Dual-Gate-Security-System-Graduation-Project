from functools import wraps

from flask import abort, session

from web_dashboard.services.admin_service import is_super_admin


def super_admin_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        admin_id = session.get("admin_id")

        if not admin_id or not is_super_admin(admin_id):
            abort(403)

        return view_function(*args, **kwargs)

    return wrapper
