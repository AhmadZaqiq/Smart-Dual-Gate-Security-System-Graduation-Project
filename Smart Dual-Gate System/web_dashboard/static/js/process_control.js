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

    function updateProcessUi(process) {
        const lifecycle = process?.lifecycle || "UNKNOWN";

        document.querySelectorAll("#process-lifecycle-badge, #card-process-state, #nav-process-badge, #live-process-badge").forEach((element) => {
            if (!element) return;

            if (element.id === "nav-process-badge" || element.id === "live-process-badge") {
                const span = element.querySelector("span");

                if (span) {
                    span.textContent = `Process: ${lifecycle}`;
                } else {
                    element.textContent = `Process: ${lifecycle}`;
                }
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
        const labels = {
            start: "start the mantrap system",
            stop: "stop the mantrap system",
        };

        if (!labels[action]) {
            return;
        }

        if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) {
            return;
        }

        setButtonsDisabled(true);

        try {
            const response = await fetch(`/api/system/${action}`, {
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

                if (message) {
                    message.textContent = payload.data.message;
                }
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

                if (action) {
                    callAction(action);
                }
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
