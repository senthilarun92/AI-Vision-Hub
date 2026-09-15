// =========================================================
// AI VISION HUB - NUMBER PLATE DETECTION
// =========================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("========================================");
    console.log("[plate.js] JavaScript loaded successfully");
    console.log("========================================");

    const API_BASE_URL = "http://127.0.0.1:8000";

    const imageInput = document.getElementById("imageInput");
    const previewContainer = document.getElementById("previewContainer");
    const imagePreview = document.getElementById("imagePreview");
    const detectButton = document.getElementById("detectButton");
    const loading = document.getElementById("loading");
    const resultBox = document.getElementById("resultBox");
    const results = document.getElementById("results");

    // =========================================================
    // CHECK ELEMENTS
    // =========================================================

    console.log("[plate.js] imageInput:", imageInput);
    console.log("[plate.js] detectButton:", detectButton);
    console.log("[plate.js] resultBox:", resultBox);
    console.log("[plate.js] results:", results);

    if (
        !imageInput ||
        !previewContainer ||
        !imagePreview ||
        !detectButton ||
        !loading ||
        !resultBox ||
        !results
    ) {
        console.error(
            "[plate.js] ERROR: Required HTML elements are missing."
        );
        return;
    }

    // =========================================================
    // IMAGE SELECT
    // =========================================================

    imageInput.addEventListener("change", () => {

        console.log("[plate.js] File selection changed");

        const file = imageInput.files[0];

        if (!file) {

            previewContainer.classList.add("d-none");

            console.log("[plate.js] No file selected");

            return;
        }

        console.log("[plate.js] Selected file:", file.name);
        console.log("[plate.js] File type:", file.type);
        console.log("[plate.js] File size:", file.size);

        const reader = new FileReader();

        reader.onload = (event) => {

            imagePreview.src = event.target.result;

            previewContainer.classList.remove("d-none");

            console.log("[plate.js] Image preview displayed");
        };

        reader.onerror = () => {

            console.error(
                "[plate.js] Failed to read image file"
            );
        };

        reader.readAsDataURL(file);

        resultBox.classList.add("d-none");

        results.innerHTML = "";
    });

    // =========================================================
    // DETECT BUTTON
    // =========================================================

    detectButton.addEventListener("click", async (event) => {

        event.preventDefault();

        console.log("========================================");
        console.log("[plate.js] DETECT BUTTON CLICKED");
        console.log("========================================");

        const file = imageInput.files[0];

        // =====================================================
        // CHECK FILE
        // =====================================================

        if (!file) {

            console.error(
                "[plate.js] No image selected"
            );

            alert(
                "Please select a vehicle image first."
            );

            return;
        }

        console.log(
            "[plate.js] Sending file:",
            file.name
        );

        // =====================================================
        // FORM DATA
        // =====================================================

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        console.log(
            "[plate.js] FormData created successfully"
        );

        // =====================================================
        // UI LOADING
        // =====================================================

        detectButton.disabled = true;

        loading.classList.remove("d-none");

        resultBox.classList.add("d-none");

        results.innerHTML = "";

        // =====================================================
        // API REQUEST
        // =====================================================

        const API_URL =
            `${API_BASE_URL}/plate/detect`;

        console.log(
            "[plate.js] API URL:",
            API_URL
        );

        console.log(
            "[plate.js] Sending POST request..."
        );

        try {

            const response = await fetch(
                API_URL,
                {
                    method: "POST",
                    body: formData
                }
            );

            console.log(
                "[plate.js] Response received"
            );

            console.log(
                "[plate.js] HTTP status:",
                response.status
            );

            console.log(
                "[plate.js] Response OK:",
                response.ok
            );

            // =================================================
            // READ RESPONSE
            // =================================================

            const responseText =
                await response.text();

            console.log(
                "[plate.js] Raw server response:",
                responseText
            );

            let json;

            try {

                json = JSON.parse(
                    responseText
                );

            } catch (parseError) {

                console.error(
                    "[plate.js] JSON parse error:",
                    parseError
                );

                throw new Error(
                    "Backend returned an invalid response."
                );
            }

            console.log(
                "[plate.js] Parsed JSON:",
                json
            );

            // =================================================
            // CHECK API RESPONSE
            // =================================================

            if (!response.ok) {

                throw new Error(
                    json.detail ||
                    json.message ||
                    `Server error: ${response.status}`
                );
            }

            if (
                json.success === false
            ) {

                throw new Error(
                    json.message ||
                    "Plate detection failed."
                );
            }

            // =================================================
            // DISPLAY RESULT
            // =================================================

            console.log(
                "[plate.js] Displaying detection result..."
            );

            displayResult(
                json.message ||
                "Plate detection completed successfully.",
                json.data || {}
            );

        } catch (error) {

            console.error(
                "========================================"
            );

            console.error(
                "[plate.js] DETECTION ERROR:",
                error
            );

            console.error(
                "========================================"
            );

            showError(
                error.message ||
                "Unable to connect to backend server."
            );

        } finally {

            detectButton.disabled = false;

            loading.classList.add("d-none");

            console.log(
                "[plate.js] Loading finished"
            );
        }
    });

    // =========================================================
    // DISPLAY RESULT
    // =========================================================

    function displayResult(
        message,
        data
    ) {

        console.log(
            "[plate.js] displayResult() called"
        );

        console.log(
            "[plate.js] Data:",
            data
        );

        resultBox.classList.remove(
            "d-none"
        );

        const plates =
            Array.isArray(data.plates)
                ? data.plates
                : [];

        console.log(
            "[plate.js] Plates received:",
            plates.length
        );

        // =====================================================
        // NO PLATE
        // =====================================================

        if (plates.length === 0) {

            results.innerHTML = `
                <div class="alert alert-warning">
                    <strong>No Number Plate Detected.</strong>
                    <br>
                    Try another image where the number plate
                    is clearly visible.
                </div>
            `;

            resultBox.scrollIntoView({
                behavior: "smooth"
            });

            return;
        }

        // =====================================================
        // SUCCESS MESSAGE
        // =====================================================

        let html = `
            <div class="alert alert-success">
                <strong>${escapeHtml(message)}</strong>
                <br>
                ${plates.length} plate(s) found.
            </div>
        `;

        // =====================================================
        // EACH PLATE
        // =====================================================

        plates.forEach(
            (plate, index) => {

                console.log(
                    `[plate.js] Plate ${index + 1}:`,
                    plate
                );

                const confidence =
                    Number(
                        plate.confidence || 0
                    );

                const confidencePct =
                    Math.round(
                        confidence * 100
                    );

                const ocrStatus =
                    plate.ocr_status ||
                    "Failed";

                const isRecognized =
                    ocrStatus === "Successful";

                const plateNumber =
                    plate.plate_number ||
                    "Not Recognized";

                const className =
                    plate.class_name ||
                    "Number Plate";

                // =================================================
                // IMAGE URL
                // =================================================

                let imageUrl =
                    plate.image_url || "";

                console.log(
                    `[plate.js] Plate ${index + 1} image URL:`,
                    imageUrl
                );

                // =================================================
                // BUILD IMAGE
                // =================================================

                let imageHtml = "";

                if (imageUrl) {

                    imageHtml = `
                        <div class="mt-3">
                            <p class="mb-2">
                                <strong>Detected Plate Image:</strong>
                            </p>

                            <img
                                src="${escapeHtml(imageUrl)}"
                                class="img-fluid rounded border"
                                style="
                                    max-width: 500px;
                                    width: 100%;
                                    height: auto;
                                "
                                alt="Detected number plate"
                                onerror="
                                    console.error(
                                        '[plate.js] Failed to load plate image:',
                                        this.src
                                    );
                                "
                            >
                        </div>
                    `;
                }

                // =================================================
                // PLATE CARD
                // =================================================

                html += `
                    <div class="av-card p-4 mb-4 border rounded">

                        <h5 class="mb-3">
                            <i class="fa-solid fa-id-card text-primary"></i>
                            Plate #${index + 1}
                        </h5>

                        <p class="mb-2">
                            <strong>Class:</strong>
                            ${escapeHtml(className)}
                        </p>

                        <p class="mb-2">
                            <strong>Detection Confidence:</strong>
                            ${confidencePct}%
                        </p>

                        <p class="mb-2">
                            <strong>Plate Number:</strong>

                            ${
                                isRecognized
                                ? `
                                    <span
                                        class="badge bg-success fs-6 ms-2"
                                    >
                                        ${escapeHtml(plateNumber)}
                                    </span>
                                `
                                : `
                                    <span
                                        class="badge bg-secondary ms-2"
                                    >
                                        Not Recognized
                                    </span>
                                `
                            }
                        </p>

                        <p class="mb-2">
                            <strong>OCR Status:</strong>

                            <span
                                class="badge ${
                                    isRecognized
                                    ? "bg-success"
                                    : "bg-danger"
                                } ms-2"
                            >
                                ${escapeHtml(ocrStatus)}
                            </span>
                        </p>

                        ${
                            plate.ocr_confidence !== undefined
                            ? `
                                <p class="mb-2">
                                    <strong>OCR Confidence:</strong>
                                    ${Math.round(
                                        Number(
                                            plate.ocr_confidence
                                        ) * 100
                                    )}%
                                </p>
                            `
                            : ""
                        }

                        ${imageHtml}

                    </div>
                `;
            }
        );

        // =====================================================
        // INSERT HTML
        // =====================================================

        results.innerHTML = html;

        resultBox.classList.remove(
            "d-none"
        );

        resultBox.scrollIntoView({
            behavior: "smooth"
        });

        console.log(
            "[plate.js] Result displayed successfully"
        );
    }

    // =========================================================
    // ERROR DISPLAY
    // =========================================================

    function showError(message) {

        resultBox.classList.remove(
            "d-none"
        );

        results.innerHTML = `
            <div class="alert alert-danger">

                <strong>
                    Detection Error
                </strong>

                <br>

                ${escapeHtml(message)}

                <hr>

                <small>
                    Make sure the FastAPI backend is running
                    on port 8000.
                </small>

            </div>
        `;

        resultBox.scrollIntoView({
            behavior: "smooth"
        });
    }

    // =========================================================
    // HTML ESCAPE
    // =========================================================

    function escapeHtml(value) {

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

});