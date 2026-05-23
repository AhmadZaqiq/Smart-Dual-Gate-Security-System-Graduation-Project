window.MantrapWorkflow = (function () {
    const STAGE_ICONS = {
        outer_door: "ti-door-enter",
        occupancy: "ti-users",
        rfid: "ti-credit-card",
        fingerprint: "ti-fingerprint",
        face: "ti-scan",
        behavior: "ti-activity",
        chamber: "ti-building-fortress",
        inner_door: "ti-door-exit",
        granted: "ti-circle-check",
        lockdown: "ti-alert-triangle",
    };

    function createNode(stage) {
        const node = document.createElement("div");
        node.className = "workflow-node";

        if (stage.active) {
            node.classList.add("active");
        }

        if (stage.completed) {
            node.classList.add("completed");
        }

        if (stage.id === "lockdown" && stage.active) {
            node.classList.add("lockdown-active");
        }

        const icon = document.createElement("div");
        icon.className = "workflow-node-icon";
        const iconClass = STAGE_ICONS[stage.id] || "ti-shield-check";
        icon.innerHTML = `<i class="ti ${iconClass}"></i>`;

        const label = document.createElement("div");
        label.className = "workflow-node-label";
        label.textContent = stage.label;

        node.appendChild(icon);
        node.appendChild(label);

        return node;
    }

    function createArrow() {
        const arrow = document.createElement("div");
        arrow.className = "workflow-arrow";
        arrow.innerHTML = '<i class="ti ti-arrow-right"></i>';
        return arrow;
    }

    function renderTrack(workflow) {
        const track = document.getElementById("workflow-track");
        const currentLabel = document.getElementById("workflow-current-label");

        if (!track || !workflow) {
            return;
        }

        if (currentLabel) {
            currentLabel.textContent = workflow.workflow_label || "Standby";
            currentLabel.dataset.state = workflow.workflow_state || "UNKNOWN";
            currentLabel.classList.toggle("bg-danger", workflow.active_stage === "lockdown");
        }

        track.innerHTML = "";

        workflow.stages.forEach((stage, index) => {
            track.appendChild(createNode(stage));

            if (index < workflow.stages.length - 1) {
                track.appendChild(createArrow());
            }
        });
    }

    return { renderTrack };
})();
