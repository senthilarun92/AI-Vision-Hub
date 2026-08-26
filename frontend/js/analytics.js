// =========================================================
// AI VISION HUB - ANALYTICS PAGE
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const API_BASE_URL = "http://127.0.0.1:8000";
    const errorBox = document.getElementById("analyticsError");

    let vehicleChart = null, ocrChart = null, timeChart = null;

    async function apiGet(path) {
        const response = await fetch(`${API_BASE_URL}${path}`);
        const json = await response.json();
        if (!response.ok || !json.success) {
            throw new Error(json.message || `Request failed: ${response.status}`);
        }
        return json.data;
    }

    async function loadAnalytics() {

        try {

            const summary = await apiGet("/analytics/summary");

            document.getElementById("totalDetections").textContent = summary.total_detections ?? 0;
            document.getElementById("totalVehicles").textContent = summary.total_vehicles ?? 0;
            document.getElementById("ocrSuccess").textContent = summary.ocr_success ?? 0;
            document.getElementById("ocrFailure").textContent = summary.ocr_failure ?? 0;

            const vehicles = await apiGet("/analytics/vehicles");
            renderVehicleChart(vehicles.distribution || {});

            const plates = await apiGet("/analytics/plates");
            renderOcrChart(plates.ocr_success ?? 0, plates.ocr_failure ?? 0);

            const timeline = await apiGet("/analytics/timeline");
            renderTimeChart(timeline.timeline || []);

        } catch (error) {
            console.error("Analytics error:", error);
            errorBox.textContent = error.message || "Unable to load analytics.";
            errorBox.classList.remove("d-none");
        }
    }

    function renderVehicleChart(distribution) {
        const canvas = document.getElementById("vehicleChart");
        if (!canvas) return;
        if (vehicleChart) vehicleChart.destroy();
        vehicleChart = new Chart(canvas, {
            type: "pie",
            data: {
                labels: Object.keys(distribution),
                datasets: [{
                    data: Object.values(distribution),
                    backgroundColor: ["#087ff5", "#00c48c", "#ffb020", "#ff5a5f", "#8c54ff"]
                }]
            }
        });
    }

    function renderOcrChart(success, failure) {
        const canvas = document.getElementById("ocrChart");
        if (!canvas) return;
        if (ocrChart) ocrChart.destroy();
        ocrChart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: ["Success", "Failure"],
                datasets: [{ data: [success, failure], backgroundColor: ["#00c48c", "#ff5a5f"] }]
            },
            options: { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    function renderTimeChart(timeline) {
        const canvas = document.getElementById("timeChart");
        if (!canvas) return;
        if (timeChart) timeChart.destroy();
        timeChart = new Chart(canvas, {
            type: "line",
            data: {
                labels: timeline.map(t => t.date),
                datasets: [{
                    label: "Detections",
                    data: timeline.map(t => t.count),
                    borderColor: "#087ff5",
                    backgroundColor: "rgba(8,127,245,.1)",
                    fill: true,
                    tension: 0.3
                }]
            },
            options: { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
    }

    loadAnalytics();
});
