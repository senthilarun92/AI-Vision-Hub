// =========================================================
// AI VISION HUB - VEHICLE DETECTION
// =========================================================
// NOTE ON THE "PAGE RELOAD" BUG:
// The Detect button below is explicitly type="button" and lives
// OUTSIDE any <form> element, so clicking it can never trigger a
// native form submission (which is the #1 cause of "page reloads
// after clicking a button" in plain HTML/JS apps). If a reload
// still happens for you, it's most likely one of these — not a
// form submit:
//   - A dev tool like VS Code "Live Server" auto-refreshing the
//     page when it detects a file save while you were testing.
//   - Opening this file directly as file:// and clicking a link
//     styled to look like a button.
//   - Pressing Enter inside the file input in some browsers.
// This script also guards against the file-input Enter-key case
// below just in case.

document.addEventListener("DOMContentLoaded", function () {

    const API_BASE_URL = "http://127.0.0.1:8000";

    const fileInput = document.getElementById("vehicleImage");
    const detectButton = document.getElementById("detectButton");
    const previewContainer = document.getElementById("previewContainer");
    const previewImage = document.getElementById("previewImage");
    const resultSection = document.getElementById("resultSection");
    const resultImage = document.getElementById("resultImage");
    const totalVehicles = document.getElementById("totalVehicles");
    const classCounts = document.getElementById("classCounts");
    const vehicleResults = document.getElementById("vehicleResults");
    const loading = document.getElementById("loading");
    const successMessage = document.getElementById("successMessage");
    const errorMessage = document.getElementById("errorMessage");

    if (!fileInput || !detectButton) {
        console.error("Vehicle page: required elements missing.");
        return;
    }

    // Defensive guard: never let Enter-key-in-input submit anything
    fileInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") e.preventDefault();
    });

    fileInput.addEventListener("change", function () {

        const file = this.files[0];
        if (!file) return;

        previewImage.src = URL.createObjectURL(file);
        previewContainer.classList.remove("d-none");

        resultSection.classList.add("d-none");
        errorMessage.classList.add("d-none");
    });

    detectButton.addEventListener("click", async function (event) {

        event.preventDefault();

        const file = fileInput.files[0];

        if (!file) {
            errorMessage.textContent = "Please select a vehicle image first.";
            errorMessage.classList.remove("d-none");
            return;
        }

        errorMessage.classList.add("d-none");
        resultSection.classList.add("d-none");
        loading.classList.remove("d-none");
        detectButton.disabled = true;

        const formData = new FormData();
        formData.append("file", file);

        try {

            const response = await fetch(`${API_BASE_URL}/vehicle/detect`, {
                method: "POST",
                body: formData
            });

            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.message || `Server error: ${response.status}`);
            }

            renderResult(json.message, json.data);

        } catch (error) {
            console.error("Vehicle detection error:", error);
            errorMessage.textContent = error.message || "Unable to connect to the backend server.";
            errorMessage.classList.remove("d-none");

        } finally {
            loading.classList.add("d-none");
            detectButton.disabled = false;
        }
    });

    function renderResult(message, data) {

        successMessage.textContent = message;
        resultImage.src = `${data.output_image}?t=${Date.now()}`;
        totalVehicles.textContent = data.total_vehicles ?? 0;

        const counts = data.class_counts || {};
        classCounts.innerHTML = Object.keys(counts).length
            ? Object.entries(counts).map(
                ([cls, count]) => `<span class="badge bg-primary me-2">${cls}: ${count}</span>`
              ).join("")
            : `<span class="text-muted">No vehicle classes detected.</span>`;

        const detections = data.detections || [];

        vehicleResults.innerHTML = detections.length
            ? detections.map((d, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${d.vehicle_type}</td>
                    <td>${Math.round(d.confidence * 100)}%</td>
                    <td>${d.bbox.join(", ")}</td>
                </tr>
              `).join("")
            : `<tr><td colspan="4" class="text-center text-muted">No vehicles detected</td></tr>`;

        resultSection.classList.remove("d-none");
        resultSection.scrollIntoView({ behavior: "smooth" });
    }

});
