window.MantrapVisual = (function () {
    function normalizeDoor(value) {
        if (!value) return "UNKNOWN";
        return value.toUpperCase();
    }

    function applyDoor(panel, state) {
        if (!panel) return;
        const normalized = normalizeDoor(state);
        panel.dataset.state = normalized;
    }

    function renderPersonDots(container, count) {
        if (!container) return;

        container.innerHTML = "";
        const total = Math.max(0, Math.min(Number(count) || 0, 6));

        for (let index = 0; index < total; index += 1) {
            const dot = document.createElement("span");
            dot.className = "person-dot";
            dot.style.animationDelay = `${index * 0.15}s`;
            container.appendChild(dot);
        }
    }

    function resolveVisualMode(status) {
        if (status.alarm_level === "LOCKDOWN" || status.fsm_state === "SECURITY_LOCKDOWN") {
            return "lockdown";
        }

        if (status.alarm_level === "WARNING" || status.alarm_active) {
            return "warning";
        }

        return "normal";
    }

    return {
        update(status) {
            const stage = document.getElementById("mantrap-stage");
            const modeBadge = document.getElementById("mantrap-visual-mode-badge");
            const workflowLabel = document.getElementById("visual-workflow-label");
            const mode = resolveVisualMode(status);

            if (stage) stage.dataset.mode = mode;

            if (modeBadge) {
                modeBadge.textContent = mode.toUpperCase();
                modeBadge.className = `badge ${mode === "lockdown" ? "bg-danger" : mode === "warning" ? "bg-warning" : "bg-success"}`;
            }

            if (workflowLabel) {
                const label = window.MantrapLabels
                    ? window.MantrapLabels.workflowLabel(status.fsm_state, status.workflow)
                    : (status.workflow?.workflow_label || status.fsm_state || "--");
                workflowLabel.textContent = `Workflow: ${label}`;
            }

            applyDoor(document.getElementById("visual-outer-door"), status.outer_door);
            applyDoor(document.getElementById("visual-inner-door"), status.inner_door);
            renderPersonDots(document.getElementById("visual-person-dots"), status.yolo_person_count);
        },
    };
})();
