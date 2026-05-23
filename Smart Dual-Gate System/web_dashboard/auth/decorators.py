from functools import wraps

from flask import jsonify, redirect, request, session, url_for


def login_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Authentication required."}), 401
            return redirect(url_for("auth.login"))

        return view_function(*args, **kwargs)

    return wrapper
