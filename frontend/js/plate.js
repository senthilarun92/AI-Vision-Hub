// =========================================================
// AI VISION HUB - NUMBER PLATE DETECTION
// =========================================================
// NOTE: response shape is now always
//   { success, message, data: { total_plates, plates: [...] } }
// and each plate now carries an explicit `image_url` (always correct —
// built server-side from the actual /outputs static mount) plus
// `plate_number` / `ocr_status` ("Successful" or "Failed").

document.addEventListener("DOMContentLoaded", function () {

    const API_BASE_URL = "http://127.0.0.1:8000";

    const imageInput = document.getElementById("imageInput");
    const previewContainer = document.getElementById("previewContainer");
    const imagePreview = document.getElementById("imagePreview");
    const detectButton = document.getElementById("detectButton");
    const loading = document.getElementById("loading");
    const resultBox = document.getElementById("resultBox");
    const results = document.getElementById("results");

    if (!imageInput || !detectButton) {
        console.error("Plate page: required elements missing.");
        return;
    }

    imageInput.addEventListener("change", function () {

        const file = imageInput.files[0];

        if (!file) {
            previewContainer.classList.add("d-none");
            return;
        }

        const reader = new FileReader();
        reader.onload = e => {
            imagePreview.src = e.target.result;
            previewContainer.classList.remove("d-none");
        };
        reader.readAsDataURL(file);

        resultBox.classList.add("d-none");
    });

    detectButton.addEventListener("click", async function (event) {

        event.preventDefault();

        const file = imageInput.files[0];

        if (!file) {
            alert("Please select a vehicle image first.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        detectButton.disabled = true;
        loading.classList.remove("d-none");
        resultBox.classList.add("d-none");

        try {

            const response = await fetch(`${API_BASE_URL}/plate/detect`, {
                method: "POST",
                body: formData
            });

            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.message || `Server error: ${response.status}`);
            }

            displayResult(json.message, json.data);

        } catch (error) {
            console.error("Plate detection error:", error);
            showError(error.message || "Unable to connect to the backend server.");

        } finally {
            detectButton.disabled = false;
            loading.classList.add("d-none");
        }
    });

    function displayResult(message, data) {

        resultBox.classList.remove("d-none");

        const plates = data.plates || [];

        if (plates.length === 0) {
            results.innerHTML = `
                <div class="alert alert-warning">
                    <strong>No Number Plate Detected.</strong> Try another image where the plate is clearly visible.
                </div>
            `;
            resultBox.scrollIntoView({ behavior: "smooth" });
            return;
        }

        let html = `<div class="alert alert-success">${message} — <strong>${plates.length}</strong> plate(s) found.</div>`;

        plates.forEach((plate, index) => {

            const confidencePct = Math.round((plate.confidence ?? 0) * 100);
            const isRecognized = plate.ocr_status === "Successful";

            html += `
                <div class="av-card p-3 mb-3">
                    <h6>Plate #${index + 1}</h6>
                    <p class="mb-1"><strong>Class:</strong> ${plate.class_name || "Number Plate"}</p>
                    <p class="mb-1"><strong>Detection Confidence:</strong> ${confidencePct}%</p>
                    <p class="mb-2">
                        <strong>Plate Number:</strong>
                        ${
                            isRecognized
                            ? `<span class="plate-chip">${plate.plate_number}</span>`
                            : `<span class="badge bg-secondary">Not Recognized</span>`
                        }
                        <span class="badge ${isRecognized ? "bg-success" : "bg-danger"} ms-2">
                            OCR: ${plate.ocr_status}
                        </span>
                    </p>
                    ${
                        plate.image_url
                        ? `<img src="${plate.image_url}" class="img-fluid rounded" style="max-width:320px;" alt="Detected plate crop">`
                        : ""
                    }
                </div>
            `;
        });

        results.innerHTML = html;
        resultBox.scrollIntoView({ behavior: "smooth" });
    }

    function showError(message) {
        resultBox.classList.remove("d-none");
        results.innerHTML = `
            <div class="alert alert-danger">
                <strong>Detection Error:</strong> ${message}
                <br><small>Make sure the FastAPI backend is running on port 8000.</small>
            </div>
        `;
        resultBox.scrollIntoView({ behavior: "smooth" });
    }

});
