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

    const STAGE_TAGS = {
        outer_door: "Entry",
        occupancy: "AI Check",
        rfid: "Identity",
        fingerprint: "Identity",
        face: "Identity",
        behavior: "Risk Check",
        chamber: "Secure Area",
        inner_door: "Exit",
        granted: "Decision",
        lockdown: "Critical",
    };

    function createNode(stage) {
        const node = document.createElement("div");
        node.className = "workflow-node workflow-pro-node";

        if (stage.active) {
            node.classList.add("active");
        }

        if (stage.completed) {
            node.classList.add("completed");
        }

        if (stage.id === "lockdown" && stage.active) {
            node.classList.add("lockdown-active");
        }

        const iconClass = STAGE_ICONS[stage.id] || "ti-shield-check";
        const tagText = STAGE_TAGS[stage.id] || "Stage";

        const icon = document.createElement("div");
        icon.className = "workflow-node-icon workflow-pro-node-icon";
        icon.innerHTML = `<i class="ti ${iconClass}"></i>`;

        const content = document.createElement("div");
        content.className = "workflow-pro-node-content";

        const label = document.createElement("div");
        label.className = "workflow-node-label workflow-pro-node-label";
        label.textContent = stage.label;

        const tag = document.createElement("div");
        tag.className = "workflow-pro-node-tag";
        tag.textContent = tagText;

        content.appendChild(label);
        content.appendChild(tag);

        node.appendChild(icon);
        node.appendChild(content);

        return node;
    }

    function createConnector() {
        const connector = document.createElement("div");
        connector.className = "workflow-arrow workflow-pro-connector";
        connector.innerHTML = '<span></span><i class="ti ti-chevron-right"></i>';
        return connector;
    }

    function renderTrack(workflow) {
        const track = document.getElementById("workflow-track");
        const currentLabel = document.getElementById("workflow-current-label");

        if (!track || !workflow || !Array.isArray(workflow.stages)) {
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
                track.appendChild(createConnector());
            }
        });
    }

    return { renderTrack };
})();
