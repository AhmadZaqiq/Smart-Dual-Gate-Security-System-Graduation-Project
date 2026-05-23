(function () {
    const toggle = document.getElementById("logs-live-toggle");
    const tableBody = document.getElementById("logs-table-body");

    if (!toggle || !tableBody) return;

    let timer = null;

    async function refreshTail() {
        const level = new URLSearchParams(window.location.search).get("level") || "";
        const q = new URLSearchParams(window.location.search).get("q") || "";
        const params = new URLSearchParams({ lines: "80" });
        if (level) params.set("level", level);
        if (q) params.set("q", q);

        const response = await fetch(`/api/logs/tail?${params.toString()}`);
        const payload = await response.json();
        const lines = payload.data || [];

        tableBody.innerHTML = lines.map((log) => `
            <tr>
                <td class="text-nowrap">${log.timestamp}</td>
                <td><span class="badge bg-secondary">${log.level}</span></td>
                <td class="font-monospace">${log.message}</td>
            </tr>
        `).join("");
    }

    toggle.addEventListener("change", function () {
        if (toggle.checked) {
            refreshTail();
            timer = setInterval(refreshTail, 5000);
        } else if (timer) {
            clearInterval(timer);
            timer = null;
        }
    });
})();
