window.MantrapWorkflow = (function () {
    const STAGE_TAGS = {
        outer_door: "Entry",
        occupancy: "AI Check",
        rfid: "Card",
        fingerprint: "Biometric",
        face: "Vision",
        behavior: "Risk",
        chamber: "Confirm",
        inner_door: "Release",
        granted: "Success",
        lockdown: "Critical",
    };

    const FLOW_GROUPS = [
        {
            title: "Main Security Flow",
            className: "main-flow",
            stages: ["outer_door", "occupancy", "rfid", "fingerprint", "face", "behavior"],
        },
        {
            title: "Final Access Flow",
            className: "final-flow",
            stages: ["chamber", "inner_door", "granted"],
        },
        {
            title: "Emergency State",
            className: "emergency-flow",
            stages: ["lockdown"],
        },
    ];

    const STAGE_SVGS = {
        outer_door: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 21V3h10v18"></path>
                <path d="M5 21h14"></path>
                <path d="M11 12h.01"></path>
                <path d="M19 12h-5"></path>
                <path d="M17 10l2 2-2 2"></path>
            </svg>
        `,
        occupancy: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="8" r="3"></circle>
                <circle cx="17" cy="10" r="2.5"></circle>
                <path d="M3 19c0-3 3-5 6-5s6 2 6 5"></path>
                <path d="M14 19c.2-1.9 1.8-3.5 4-4"></path>
            </svg>
        `,
        rfid: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="6" width="14" height="12" rx="2"></rect>
                <path d="M7 10h4"></path>
                <path d="M7 14h6"></path>
                <path d="M19 8c1.5 1.2 2 2.5 2 4s-.5 2.8-2 4"></path>
            </svg>
        `,
        fingerprint: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3c-3.5 0-6 2.6-6 6"></path>
                <path d="M18 9c0-3.5-2.5-6-6-6"></path>
                <path d="M8 10c0-2.2 1.5-4 4-4s4 1.8 4 4"></path>
                <path d="M7 14c0 4 2 7 5 7"></path>
                <path d="M12 10v4"></path>
                <path d="M16 13c0 3-1 6-3 8"></path>
                <path d="M5 12c0 5 2.5 9 6 9"></path>
            </svg>
        `,
        face: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 3H6a2 2 0 0 0-2 2v2"></path>
                <path d="M16 3h2a2 2 0 0 1 2 2v2"></path>
                <path d="M20 16v2a2 2 0 0 1-2 2h-2"></path>
                <path d="M4 16v2a2 2 0 0 0 2 2h2"></path>
                <circle cx="12" cy="10" r="3.5"></circle>
                <path d="M9 16c.9.7 1.9 1 3 1s2.1-.3 3-1"></path>
            </svg>
        `,
        behavior: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 12h3l2-4 4 8 2-4h7"></path>
            </svg>
        `,
        chamber: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="16" rx="2"></rect>
                <path d="M8 12h8"></path>
                <path d="M12 8v8"></path>
            </svg>
        `,
        inner_door: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21V3h10v18"></path>
                <path d="M5 12h5"></path>
                <path d="M7 10l-2 2 2 2"></path>
                <path d="M9 21H3"></path>
                <path d="M15 12h.01"></path>
            </svg>
        `,
        granted: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M8 12l2.5 2.5L16 9"></path>
            </svg>
        `,
        lockdown: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3l7 3v5c0 5-3.5 8-7 10-3.5-2-7-5-7-10V6l7-3z"></path>
                <path d="M9.5 9.5l5 5"></path>
                <path d="M14.5 9.5l-5 5"></path>
            </svg>
        `,
    };

    function createNode(stage) {
        const node = document.createElement("div");
        node.className = "workflow-node workflow-pro-node workflow-timeline-node";

        if (stage.active) {
            node.classList.add("active");
        }

        if (stage.completed) {
            node.classList.add("completed");
        }

        if (stage.id === "lockdown") {
            node.classList.add("lockdown-node");
        }

        if (stage.id === "lockdown" && stage.active) {
            node.classList.add("lockdown-active");
        }

        const tagText = STAGE_TAGS[stage.id] || "Stage";

        const icon = document.createElement("div");
        icon.className = "workflow-node-icon workflow-pro-node-icon workflow-stage-logo";
        icon.innerHTML = STAGE_SVGS[stage.id] || STAGE_SVGS.outer_door;

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

    function createGroup(group, stagesById) {
        const section = document.createElement("div");
        section.className = `workflow-timeline-section ${group.className}`;

        const title = document.createElement("div");
        title.className = "workflow-timeline-title";
        title.textContent = group.title;

        const row = document.createElement("div");
        row.className = "workflow-timeline-row";

        const visibleStages = group.stages
            .map((stageId) => stagesById.get(stageId))
            .filter(Boolean);

        visibleStages.forEach((stage) => {
            row.appendChild(createNode(stage));
        });

        section.appendChild(title);
        section.appendChild(row);

        return section;
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

        const stagesById = new Map();

        workflow.stages.forEach((stage) => {
            stagesById.set(stage.id, stage);
        });

        track.innerHTML = "";

        FLOW_GROUPS.forEach((group) => {
            track.appendChild(createGroup(group, stagesById));
        });
    }

    return { renderTrack };
})();
