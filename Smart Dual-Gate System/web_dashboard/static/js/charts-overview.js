(async function () {
    const accessCanvas = document.getElementById("accessChart");
    const securityCanvas = document.getElementById("securityChart");

    if (!accessCanvas || !securityCanvas || !window.Chart) return;

    Chart.defaults.color = "#94a3b8";
    Chart.defaults.borderColor = "rgba(148, 163, 184, 0.12)";

    try {
        const [accessRes, securityRes] = await Promise.all([
            fetch("/api/dashboard/charts/access?days=7"),
            fetch("/api/dashboard/charts/security?days=7"),
        ]);

        const accessPayload = await accessRes.json();
        const securityPayload = await securityRes.json();

        const accessData = accessPayload.data || [];
        const securityData = securityPayload.data || [];

        new Chart(accessCanvas, {
            type: "line",
            data: {
                labels: accessData.map((row) => row.DayLabel),
                datasets: [{
                    label: "Access Sessions",
                    data: accessData.map((row) => row.SessionCount),
                    borderColor: "#22d3ee",
                    backgroundColor: "rgba(34, 211, 238, 0.18)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 3,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#cbd5e1" } } },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.08)" } },
                    y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.08)" }, beginAtZero: true },
                },
            },
        });

        new Chart(securityCanvas, {
            type: "doughnut",
            data: {
                labels: securityData.map((row) => row.Severity || "Unknown"),
                datasets: [{
                    data: securityData.map((row) => row.EventCount),
                    backgroundColor: ["#64748b", "#f59e0b", "#ef4444", "#22d3ee", "#10b981"],
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: { legend: { position: "bottom", labels: { color: "#cbd5e1", boxWidth: 12 } } },
            },
        });
    } catch (error) {
        console.error("Failed to load charts", error);
    }
})();
