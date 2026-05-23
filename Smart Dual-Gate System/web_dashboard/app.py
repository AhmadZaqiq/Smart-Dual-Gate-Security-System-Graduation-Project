from datetime import timedelta

from flask import Flask, render_template

from web_dashboard.config import Config
from web_dashboard.extensions import csrf
from web_dashboard.routes import register_blueprints
from web_dashboard.utils.path_setup import ensure_project_root_on_path


def create_app():
    ensure_project_root_on_path()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(hours=Config.PERMANENT_SESSION_LIFETIME_HOURS)

    csrf.init_app(app)
    register_blueprints(app)

    from web_dashboard.utils.filters import register_template_filters
    register_template_filters(app)

    @app.context_processor
    def inject_globals():
        from flask import session as flask_session
        from web_dashboard.services import admin_service

        def admin_profile():
            return {
                "username": flask_session.get("username"),
                "display_name": flask_session.get("display_name", "Administrator"),
                "initials": flask_session.get("initials", "AD"),
                "role_label": flask_session.get("role_label", "Security Administrator"),
            }

        return {
            "app_name": "Smart Dual-Gate Security",
            "admin_profile": admin_profile,
            "is_super_admin": admin_service.is_super_admin(flask_session.get("admin_id")),
        }

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=Config.DASHBOARD_HOST,
        port=Config.DASHBOARD_PORT,
        debug=False,
    )
