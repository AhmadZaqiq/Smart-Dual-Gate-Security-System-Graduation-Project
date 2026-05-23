def register_blueprints(app):
    from web_dashboard.routes.auth_routes import auth_bp
    from web_dashboard.routes.dashboard_routes import dashboard_bp
    from web_dashboard.routes.live_routes import live_bp
    from web_dashboard.routes.access_routes import access_bp
    from web_dashboard.routes.auth_attempts_routes import auth_attempts_bp
    from web_dashboard.routes.security_routes import security_bp
    from web_dashboard.routes.employees_routes import employees_bp
    from web_dashboard.routes.settings_routes import settings_bp
    from web_dashboard.routes.logs_routes import logs_bp
    from web_dashboard.routes.audit_routes import audit_bp

    from web_dashboard.api.system_api import system_api_bp
    from web_dashboard.api.dashboard_api import dashboard_api_bp
    from web_dashboard.api.access_api import access_api_bp
    from web_dashboard.api.auth_attempts_api import auth_attempts_api_bp
    from web_dashboard.api.security_api import security_api_bp
    from web_dashboard.api.employees_api import employees_api_bp
    from web_dashboard.api.settings_api import settings_api_bp
    from web_dashboard.api.logs_api import logs_api_bp
    from web_dashboard.api.audit_api import audit_api_bp
    from web_dashboard.routes.admins_routes import admins_bp

    from web_dashboard.api.streams_api import streams_api_bp
    from web_dashboard.api.enrollment_api import enrollment_api_bp
    from web_dashboard.api.admins_api import admins_api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(auth_attempts_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(admins_bp)

    app.register_blueprint(system_api_bp)
    app.register_blueprint(dashboard_api_bp)
    app.register_blueprint(access_api_bp)
    app.register_blueprint(auth_attempts_api_bp)
    app.register_blueprint(security_api_bp)
    app.register_blueprint(employees_api_bp)
    app.register_blueprint(settings_api_bp)
    app.register_blueprint(logs_api_bp)
    app.register_blueprint(audit_api_bp)
    app.register_blueprint(streams_api_bp)
    app.register_blueprint(enrollment_api_bp)
    app.register_blueprint(admins_api_bp)
