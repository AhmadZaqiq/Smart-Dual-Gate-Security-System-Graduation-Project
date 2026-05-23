window.MantrapLabels = (function () {
    const WORKFLOW_STATE_LABELS = {
        SYSTEM_OFF: "System Off",
        IDLE_OUTER_OPEN: "Standby — Outer Access",
        AI_START_DELAY: "Preparing Detection",
        PERSON_COUNTING: "Occupancy Detection",
        MULTI_PERSON_WARNING: "Multi-Person Warning",
        MULTI_PERSON_EXIT_RELEASE: "Exit Release",
        AUTHENTICATION_READY: "Authentication Ready",
        AUTHENTICATION_PROCESSING: "Authentication In Progress",
        AUTHENTICATION_FAILED_WAIT_BACK: "Authentication Failed",
        WAIT_INNER_BUTTON_CONFIRM: "Awaiting Inner Confirmation",
        INNER_DOOR_UNLOCKED: "Inner Access Granted",
        CANCEL_AND_EXIT: "Cancel & Exit",
        SECURITY_LOCKDOWN: "Security Lockdown",
        ERROR_STATE: "System Error",
    };

    function humanize(value) {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const text = String(value).trim();

        if (WORKFLOW_STATE_LABELS[text]) {
            return WORKFLOW_STATE_LABELS[text];
        }

        if (/^[A-Z0-9_]+$/.test(text) && text.includes("_")) {
            return text
                .split("_")
                .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
                .join(" ");
        }

        return text;
    }

    function workflowLabel(state, workflowPayload) {
        if (workflowPayload && workflowPayload.workflow_label) {
            return workflowPayload.workflow_label;
        }

        return humanize(state);
    }

    return { humanize, workflowLabel };
})();
