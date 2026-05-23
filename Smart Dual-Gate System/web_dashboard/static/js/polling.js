window.MantrapPolling = (function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    async function fetchStatus() {
        const response = await fetch("/api/system/status");
        const payload = await response.json();
        return payload.data || {};
    }

    function formatDoor(value) {
        if (!value) {
            return "Unknown";
        }

        return window.MantrapLabels
            ? window.MantrapLabels.humanize(value)
            : value.toUpperCase();
    }

    function workflowText(status) {
        if (window.MantrapLabels) {
            return window.MantrapLabels.workflowLabel(status.fsm_state, status.workflow);
        }

        return status.workflow?.workflow_label || status.fsm_state || "--";
    }

    function applyStatusPill(element, text, state) {
        if (!element) {
            return;
        }

        const normalized = (state || "UNKNOWN").toUpperCase();

        if (
            element.id === "nav-workflow-badge"
            || element.id === "nav-count-badge"
            || element.id === "nav-stream-badge"
            || element.id === "nav-process-badge"
        ) {
            const span = element.querySelector("span");
            if (span) {
                span.textContent = text;
            }
        } else {
            element.textContent = text;
        }

        element.dataset.state = normalized;
    }

    function applyNavbar(status) {
        const process = status.process || {};
        const lifecycle = process.lifecycle || status.process_lifecycle || "UNKNOWN";

        applyStatusPill(
            document.getElementById("nav-process-badge"),
            `Process: ${lifecycle}`,
            lifecycle,
        );
        applyStatusPill(
            document.getElementById("nav-workflow-badge"),
            `Workflow: ${workflowText(status)}`,
            status.fsm_state || "UNKNOWN",
        );
        applyStatusPill(
            document.getElementById("nav-count-badge"),
            `Persons: ${status.yolo_person_count ?? 0}`,
            "NORMAL",
        );
        applyStatusPill(
            document.getElementById("nav-stream-badge"),
            `Stream: ${status.stream_health || "Inactive"}`,
            status.stream_health || "INACTIVE",
        );

        const alarmLabel = status.alarm_level === "LOCKDOWN"
            ? "Lockdown"
            : status.alarm_level === "WARNING"
                ? "Warning"
                : "Normal";
        applyStatusPill(
            document.getElementById("nav-alarm-badge"),
            `Alarm: ${alarmLabel}`,
            status.alarm_level || "NORMAL",
        );

        if (window.MantrapProcessControl) {
            window.MantrapProcessControl.updateProcessUi(process);
        }
    }

    function applyOverview(status) {
        applyStatusPill(
            document.getElementById("card-workflow-state"),
            workflowText(status),
            status.fsm_state || "UNKNOWN",
        );

        const process = status.process || {};
        applyStatusPill(
            document.getElementById("card-process-state"),
            process.lifecycle || "UNKNOWN",
            process.lifecycle || "UNKNOWN",
        );

        const personCount = document.getElementById("card-person-count");
        if (personCount) {
            personCount.textContent = status.yolo_person_count ?? 0;
        }

        applyStatusPill(
            document.getElementById("card-outer-door"),
            formatDoor(status.outer_door),
            formatDoor(status.outer_door),
        );
        applyStatusPill(
            document.getElementById("card-inner-door"),
            formatDoor(status.inner_door),
            formatDoor(status.inner_door),
        );
        applyStatusPill(
            document.getElementById("card-stream-health"),
            status.stream_health || "Inactive",
            status.stream_health || "INACTIVE",
        );

        if (window.MantrapVisual) {
            window.MantrapVisual.update(status);
        }

        if (window.MantrapWorkflow && status.workflow) {
            window.MantrapWorkflow.renderTrack(status.workflow);
        }
    }

    function applyLive(status) {
        applyStatusPill(
            document.getElementById("live-workflow-state"),
            workflowText(status),
            status.fsm_state || "UNKNOWN",
        );

        const person = document.getElementById("live-person-count");
        if (person) {
            person.textContent = status.yolo_person_count ?? 0;
        }

        applyStatusPill(
            document.getElementById("live-outer-door"),
            formatDoor(status.outer_door),
            formatDoor(status.outer_door),
        );
        applyStatusPill(
            document.getElementById("live-inner-door"),
            formatDoor(status.inner_door),
            formatDoor(status.inner_door),
        );
        applyStatusPill(
            document.getElementById("live-alarm-status"),
            status.alarm_level || "Normal",
            status.alarm_level || "NORMAL",
        );

        const process = status.process || {};
        applyStatusPill(
            document.getElementById("live-process-badge"),
            `Process: ${process.lifecycle || "UNKNOWN"}`,
            process.lifecycle || "UNKNOWN",
        );
    }

    return {
        startNavbarStatus() {
            const tick = async () => {
                try {
                    const status = await fetchStatus();
                    applyNavbar(status);
                } catch (error) {
                    console.warn("Navbar status poll failed", error);
                }
            };
            tick();
            setInterval(tick, 2000);
        },
        startOverviewStatus() {
            const tick = async () => {
                try {
                    const status = await fetchStatus();
                    applyNavbar(status);
                    applyOverview(status);
                } catch (error) {
                    console.warn("Overview status poll failed", error);
                }
            };
            tick();
            setInterval(tick, 2000);
        },
        startLiveMonitor() {
            const tick = async () => {
                try {
                    const status = await fetchStatus();
                    applyNavbar(status);
                    applyLive(status);
                } catch (error) {
                    console.warn("Live status poll failed", error);
                }
            };
            tick();
            setInterval(tick, 2000);
        },
    };
})();
