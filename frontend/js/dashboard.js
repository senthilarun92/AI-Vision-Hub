// =========================================================
// AI VISION HUB - DASHBOARD
// =========================================================
// NOTE: every backend response now has the SAME shape:
//   { success: true/false, message: "...", data: {...} }
// so we always check `json.success` and read from `json.data`.

const API_BASE_URL = "http://127.0.0.1:8000";

let vehicleChart = null;
let ocrChart = null;


async function apiGet(path) {
    const response = await fetch(`${API_BASE_URL}${path}`);
    const json = await response.json();

    if (!response.ok || !json.success) {
        throw new Error(json.message || `Request failed: ${response.status}`);
    }

    return json.data;
}


function showError(message) {
    const box = document.getElementById("dashboardError");
    if (!box) return;
    box.textContent = message;
    box.classList.remove("d-none");
}


async function loadDashboard() {

    try {
        const stats = await apiGet("/dashboard/stats");

        document.getElementById("totalDetections").textContent = stats.total_detections ?? 0;
        document.getElementById("totalVehicles").textContent = stats.total_vehicles ?? 0;
        document.getElementById("totalPlates").textContent = stats.total_plates ?? 0;
        document.getElementById("ocrSuccess").textContent = stats.ocr_success ?? 0;
        document.getElementById("todayDetections").textContent = stats.today_detections ?? 0;
        document.getElementById("latestPlate").textContent = stats.latest_plate || "----";

        await loadVehicleChart();
        await loadOcrChart();
        await loadRecentHistory();

    } catch (error) {
        console.error("Dashboard error:", error);
        showError(error.message || "Unable to load dashboard. Is the backend running?");
    }
}


async function loadVehicleChart() {

    const data = await apiGet("/analytics/vehicles");
    const distribution = data.distribution || {};

    const canvas = document.getElementById("vehicleChart");
    if (!canvas) return;

    if (vehicleChart) vehicleChart.destroy();

    vehicleChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: Object.keys(distribution),
            datasets: [{
                data: Object.values(distribution),
                backgroundColor: ["#087ff5", "#00c48c", "#ffb020", "#ff5a5f", "#8c54ff"]
            }]
        },
        options: { responsive: true }
    });
}


async function loadOcrChart() {

    const data = await apiGet("/analytics/plates");

    const canvas = document.getElementById("ocrChart");
    if (!canvas) return;

    if (ocrChart) ocrChart.destroy();

    ocrChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: ["OCR Success", "OCR Failure"],
            datasets: [{
                label: "Plates",
                data: [data.ocr_success ?? 0, data.ocr_failure ?? 0],
                backgroundColor: ["#00c48c", "#ff5a5f"]
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}


async function loadRecentHistory() {

    const data = await apiGet("/history/?page=1&page_size=8");
    const table = document.getElementById("historyTable");

    if (!table) return;

    const rows = data.history || [];

    if (rows.length === 0) {
        table.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No detection records found</td></tr>`;
        return;
    }

    table.innerHTML = rows.map(row => {
        const confidence = row.detection_type === "vehicle"
            ? row.vehicle_confidence
            : row.plate_confidence;

        return `
            <tr>
                <td>${row.id}</td>
                <td><span class="badge bg-secondary">${row.detection_type}</span></td>
                <td>${row.plate_number || "-"}</td>
                <td>${confidence != null ? Math.round(confidence * 100) + "%" : "-"}</td>
                <td>${new Date(row.created_at).toLocaleString()}</td>
            </tr>
        `;
    }).join("");
}


loadDashboard();
setInterval(loadDashboard, 15000);
