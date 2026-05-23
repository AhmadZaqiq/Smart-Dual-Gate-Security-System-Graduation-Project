def register_template_filters(app):
    from web_dashboard.utils.labels import humanize, workflow_state_label

    @app.template_filter("humanize")
    def humanize_filter(value):
        return humanize(value)

    @app.template_filter("workflow_label")
    def workflow_label_filter(value):
        return workflow_state_label(value)

    @app.template_filter("badge_class")
    def badge_class(value):
        mapping = {
            "ACCESS_GRANTED": "bg-success",
            "ACCESS_DENIED": "bg-danger",
            "COMPLETED": "bg-success",
            "ACTIVE": "bg-azure",
            "HIGH": "bg-danger",
            "MEDIUM": "bg-warning",
            "LOW": "bg-secondary",
            "INFO": "bg-blue",
            "WARNING": "bg-warning",
            "ERROR": "bg-danger",
            "SECURITY": "bg-red",
            "ACCESS": "bg-green",
            "ONLINE": "bg-success",
            "OFFLINE": "bg-secondary",
            "INACTIVE": "bg-secondary",
        }
        return mapping.get(str(value).upper(), "bg-secondary")

    @app.template_filter("workflow_badge")
    def workflow_badge(state):
        danger_states = {"SECURITY_LOCKDOWN", "ERROR_STATE", "MULTI_PERSON_WARNING"}
        success_states = {"INNER_DOOR_UNLOCKED", "WAIT_INNER_BUTTON_CONFIRM"}
        auth_states = {"AUTHENTICATION_READY", "AUTHENTICATION_PROCESSING"}

        if state in danger_states:
            return "bg-danger"
        if state in success_states:
            return "bg-success"
        if state in auth_states:
            return "bg-azure"
        return "bg-secondary"
