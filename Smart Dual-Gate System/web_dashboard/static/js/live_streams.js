window.MantrapLiveStreams = (function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    function normalizeStreamUrl(url) {
        if (!url) {
            return null;
        }

        try {
            const streamUrl = new URL(url, window.location.origin);

            if (
                streamUrl.hostname === "127.0.0.1"
                || streamUrl.hostname === "localhost"
                || streamUrl.hostname === "0.0.0.0"
            ) {
                streamUrl.hostname = window.location.hostname;
            }

            return streamUrl.toString();
        } catch (error) {
            return url;
        }
    }

    function setHealthBadge(element, health) {
        if (!element) {
            return;
        }

        const normalized = (health || "OFFLINE").toUpperCase();
        element.textContent = normalized;
        element.dataset.state = normalized;
    }

    function setButtonLoading(button, loading) {
        if (!button) {
            return;
        }

        button.disabled = loading;

        if (loading) {
            button.dataset.originalHtml = button.innerHTML;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Working...';
            return;
        }

        if (button.dataset.originalHtml) {
            button.innerHTML = button.dataset.originalHtml;
            delete button.dataset.originalHtml;
        }
    }

    async function callStreamAction(camera, action) {
        const response = await fetch(`/api/streams/${camera}/${action}`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
                "Content-Type": "application/json",
            },
        });

        return response.json();
    }

    function showImageError(cameraKey) {
        const healthBadge = document.getElementById(`${cameraKey}-stream-health`);
        const statusText = document.getElementById(`${cameraKey}-stream-status-text`);
        const image = document.getElementById(`${cameraKey}-stream-image`);
        const offline = document.getElementById(`${cameraKey}-stream-offline`);
        const loading = document.getElementById(`${cameraKey}-stream-loading`);

        setHealthBadge(healthBadge, "OFFLINE");

        if (statusText) {
            statusText.textContent = "Stream URL is not reachable from browser";
        }

        if (loading) {
            loading.classList.add("d-none");
        }

        if (image) {
            image.classList.add("d-none");
            image.removeAttribute("src");
            image.dataset.src = "";
        }

        if (offline) {
            offline.classList.remove("d-none");
        }
    }

    function renderStream(cameraKey, streamData) {
        const healthBadge = document.getElementById(`${cameraKey}-stream-health`);
        const statusText = document.getElementById(`${cameraKey}-stream-status-text`);
        const image = document.getElementById(`${cameraKey}-stream-image`);
        const offline = document.getElementById(`${cameraKey}-stream-offline`);
        const loading = document.getElementById(`${cameraKey}-stream-loading`);
        const sourceLabel = document.getElementById(`${cameraKey}-stream-source`);

        const health = streamData.health || "OFFLINE";
        const browserUrl = normalizeStreamUrl(streamData.url);
        const isOnline = health === "ONLINE" && browserUrl;

        setHealthBadge(healthBadge, health);

        if (statusText) {
            if (streamData.running && isOnline) {
                statusText.textContent = "Stream active";
            } else if (streamData.running) {
                statusText.textContent = "Starting stream...";
            } else {
                statusText.textContent = "Stream offline";
            }
        }

        if (sourceLabel) {
            if (streamData.source) {
                sourceLabel.textContent = streamData.source === "yolo" ? "YOLO Monitor" : "Preview Server";
                sourceLabel.classList.remove("d-none");
            } else {
                sourceLabel.classList.add("d-none");
            }
        }

        if (loading) {
            loading.classList.toggle("d-none", !streamData.running || isOnline);
        }

        if (offline) {
            offline.classList.toggle("d-none", isOnline);
        }

        if (image) {
            image.onerror = function () {
                showImageError(cameraKey);
            };

            if (isOnline) {
                image.classList.remove("d-none");

                if (image.dataset.src !== browserUrl) {
                    image.src = `${browserUrl}?ts=${Date.now()}`;
                    image.dataset.src = browserUrl;
                }
            } else {
                image.classList.add("d-none");
                image.removeAttribute("src");
                image.dataset.src = "";
            }
        }
    }

    async function refreshStatus() {
        try {
            const response = await fetch("/api/streams/status");
            const payload = await response.json();
            const streams = payload.data || {};

            renderStream("face", streams.face || {});
            renderStream("inner", streams.inner || {});
        } catch (error) {
            console.warn("Stream status refresh failed", error);
        }
    }

    async function handleAction(event) {
        const button = event.currentTarget;
        const camera = button.dataset.camera;
        const action = button.dataset.action;

        if (!camera || !action) {
            return;
        }

        setButtonLoading(button, true);

        try {
            const payload = await callStreamAction(camera, action);

            if (!payload.success) {
                window.alert(payload.error || "Stream action failed.");
            }

            await refreshStatus();
        } catch (error) {
            window.alert("Unable to reach stream control API.");
            console.error(error);
        } finally {
            setButtonLoading(button, false);
        }
    }

    function bindControls() {
        document.querySelectorAll("[data-stream-action]").forEach((button) => {
            button.addEventListener("click", handleAction);
        });
    }

    return {
        init() {
            bindControls();
            refreshStatus();
            setInterval(refreshStatus, 3000);
        },
        refreshStatus,
    };
})();
