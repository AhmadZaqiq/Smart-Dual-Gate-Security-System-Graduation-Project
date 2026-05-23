window.MantrapProcessControl = (function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    function setButtonsDisabled(disabled) {
        document.querySelectorAll(".system-control-btn").forEach((button) => {
            button.disabled = disabled;
        });
    }

    function setLifecycleBadge(element, state) {
        if (!element) return;

        const normalized = (state || "UNKNOWN").toUpperCase();
        element.textContent = normalized;
        element.dataset.state = normalized;
    }

    function updateProcessUi(process) {
        const lifecycle = process?.lifecycle || "UNKNOWN";

        document.querySelectorAll("#process-lifecycle-badge, #card-process-state, #nav-process-badge, #live-process-badge").forEach((element) => {
            if (!element) return;

            if (element.id === "nav-process-badge" || element.id === "live-process-badge") {
                element.querySelector("span").textContent = `Process: ${lifecycle}`;
            } else {
                element.textContent = lifecycle;
            }

            element.dataset.state = lifecycle;
        });

        const message = document.getElementById("process-control-message");

        if (message && process?.message) {
            message.textContent = process.message;
        }
    }

    async function callAction(action) {
        if (action === "reset-idle") {
            if (!window.confirm("Return the security workflow to idle standby mode?")) {
                return;
            }
        } else {
            const labels = {
                start: "start the mantrap system",
                stop: "stop the mantrap system",
                restart: "restart the mantrap system",
            };

            if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) {
                return;
            }
        }

        setButtonsDisabled(true);

        try {
            const endpoint = action === "reset-idle" ? "/api/system/reset-idle" : `/api/system/${action}`;
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "Content-Type": "application/json",
                },
            });

            const payload = await response.json();

            if (!payload.success) {
                window.alert(payload.error || "Control action failed.");
                return;
            }

            updateProcessUi(payload.data?.process);

            if (payload.data?.message) {
                const message = document.getElementById("process-control-message");
                if (message) message.textContent = payload.data.message;
            }
        } catch (error) {
            window.alert("Unable to reach the control API.");
            console.error(error);
        } finally {
            setButtonsDisabled(false);
        }
    }

    async function refreshProcessStatus() {
        try {
            const response = await fetch("/api/system/process-status");
            const payload = await response.json();
            updateProcessUi(payload.data);
        } catch (error) {
            console.warn("Process status refresh failed", error);
        }
    }

    function bindButtons() {
        document.querySelectorAll(".system-control-btn").forEach((button) => {
            button.addEventListener("click", () => {
                const action = button.dataset.action;
                if (action) callAction(action);
            });
        });
    }

    return {
        init() {
            bindButtons();
            refreshProcessStatus();
            setInterval(refreshProcessStatus, 3000);
        },
        refreshProcessStatus,
        updateProcessUi,
    };
})();
