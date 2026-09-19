// =========================================================
// AI VISION HUB - ANPR
// =========================================================

const API_BASE_URL = "http://127.0.0.1:8000";

// Elements
const anprFile = document.getElementById("anprFile");
const anprButton = document.getElementById("anprButton");

const anprError = document.getElementById("anprError");
const anprLoading = document.getElementById("anprLoading");
const anprResult = document.getElementById("anprResult");

const vehicleCount = document.getElementById("vehicleCount");
const plateCount = document.getElementById("plateCount");
const ocrStatus = document.getElementById("ocrStatus");

const vehicleResults = document.getElementById("vehicleResults");
const plateResults = document.getElementById("plateResults");

const outputImage = document.getElementById("outputImage");


// =========================================================
// SHOW ERROR
// =========================================================

function showError(message) {

    anprError.textContent = message;
    anprError.classList.remove("d-none");
}


// =========================================================
// HIDE ERROR
// =========================================================

function hideError() {

    anprError.textContent = "";
    anprError.classList.add("d-none");
}


// =========================================================
// LOADING STATE
// =========================================================

function setLoading(isLoading) {

    if (isLoading) {

        anprLoading.classList.remove("d-none");

        anprButton.disabled = true;

        anprButton.innerHTML = `
            <span
                class="spinner-border spinner-border-sm me-2"
                role="status"
            ></span>
            Processing...
        `;

    } else {

        anprLoading.classList.add("d-none");

        anprButton.disabled = false;

        anprButton.innerHTML = `
            <i class="fa-solid fa-magnifying-glass"></i>
            Run ANPR
        `;
    }
}


// =========================================================
// RUN ANPR
// =========================================================

async function runANPR() {

    hideError();

    // Check file
    if (!anprFile.files || anprFile.files.length === 0) {

        showError("Please select a vehicle image.");

        return;
    }

    const file = anprFile.files[0];

    // Allowed file types
    const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ];

    if (!allowedTypes.includes(file.type)) {

        showError(
            "Only JPG, JPEG, PNG and WEBP images are supported."
        );

        return;
    }


    // Create FormData
    const formData = new FormData();

    formData.append("file", file);


    // Start loading
    setLoading(true);


    try {

        console.log("Sending ANPR request...");


        // =====================================================
        // API CALL
        // =====================================================

        const response = await fetch(
            `${API_BASE_URL}/anpr/detect`,
            {
                method: "POST",
                body: formData
            }
        );


        console.log("HTTP Status:", response.status);


        // Read JSON
        const json = await response.json();


        console.log("ANPR Response:", json);


        // Check backend response
        if (!response.ok || !json.success) {

            throw new Error(
                json.message || "ANPR processing failed."
            );
        }


        // =====================================================
        // GET DATA
        // =====================================================

        const data = json.data || {};

        const vehicleData =
            data.vehicle_detection || {};

        const plateData =
            data.plate_detection || {};


        // =====================================================
        // SHOW RESULT SECTION
        // =====================================================

        anprResult.classList.remove("d-none");


        // =====================================================
        // SUMMARY
        // =====================================================

        const totalVehicles =
            vehicleData.total_vehicles || 0;

        const totalPlates =
            plateData.total_plates || 0;


        vehicleCount.textContent =
            totalVehicles;

        plateCount.textContent =
            totalPlates;


        // =====================================================
        // OCR STATUS
        // =====================================================

        const plates =
            plateData.plates || [];


        const successfulOCR =
            plates.filter(
                plate =>
                    plate.plate_number &&
                    plate.plate_number !== "Not Recognized"
            ).length;


        if (successfulOCR > 0) {

            ocrStatus.textContent = "Successful";

            ocrStatus.classList.remove(
                "text-danger",
                "text-warning"
            );

            ocrStatus.classList.add(
                "text-success"
            );

        } else if (totalPlates > 0) {

            ocrStatus.textContent = "Failed";

            ocrStatus.classList.remove(
                "text-success",
                "text-warning"
            );

            ocrStatus.classList.add(
                "text-danger"
            );

        } else {

            ocrStatus.textContent = "No Plate";

            ocrStatus.classList.remove(
                "text-success",
                "text-danger"
            );

            ocrStatus.classList.add(
                "text-warning"
            );
        }


        // =====================================================
        // VEHICLE RESULTS
        // =====================================================

        renderVehicleResults(
            vehicleData.detections || []
        );


        // =====================================================
        // PLATE RESULTS
        // =====================================================

        renderPlateResults(
            plates
        );


        // =====================================================
        // OUTPUT IMAGE
        // =====================================================

        const imageUrl =
            vehicleData.output_image;


        if (imageUrl) {

            outputImage.src =
                imageUrl + "?t=" + Date.now();

            outputImage.classList.remove(
                "d-none"
            );

        } else {

            outputImage.src = "";
        }


        // Scroll to result
        anprResult.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        console.error(
            "ANPR Error:",
            error
        );

        showError(
            error.message ||
            "Unable to process ANPR image."
        );


    } finally {

        setLoading(false);
    }
}


// =========================================================
// VEHICLE RESULT TABLE
// =========================================================

function renderVehicleResults(detections) {

    if (!detections || detections.length === 0) {

        vehicleResults.innerHTML = `
            <div class="alert alert-warning mb-0">
                No vehicles detected.
            </div>
        `;

        return;
    }


    let html = `
        <table class="table table-hover align-middle">

            <thead>
                <tr>
                    <th>#</th>
                    <th>Vehicle Type</th>
                    <th>Confidence</th>
                    <th>Bounding Box</th>
                </tr>
            </thead>

            <tbody>
    `;


    detections.forEach(
        (vehicle, index) => {

            const confidence =
                vehicle.confidence != null
                    ? Math.round(
                        vehicle.confidence * 100
                    ) + "%"
                    : "-";


            const bbox =
                vehicle.bbox
                    ? vehicle.bbox.join(", ")
                    : "-";


            html += `
                <tr>

                    <td>${index + 1}</td>

                    <td>
                        <span class="badge bg-primary">
                            ${escapeHTML(
                                vehicle.vehicle_type || "Unknown"
                            )}
                        </span>
                    </td>

                    <td>
                        <strong>
                            ${confidence}
                        </strong>
                    </td>

                    <td>
                        <small class="text-muted">
                            ${bbox}
                        </small>
                    </td>

                </tr>
            `;
        }
    );


    html += `
            </tbody>
        </table>
    `;


    vehicleResults.innerHTML = html;
}


// =========================================================
// PLATE RESULT TABLE
// =========================================================

function renderPlateResults(plates) {

    if (!plates || plates.length === 0) {

        plateResults.innerHTML = `
            <div class="alert alert-warning mb-0">
                No number plate detected.
            </div>
        `;

        return;
    }


    let html = `
        <table class="table table-hover align-middle">

            <thead>
                <tr>
                    <th>#</th>
                    <th>Plate Number</th>
                    <th>Detection Confidence</th>
                    <th>OCR Confidence</th>
                    <th>OCR Status</th>
                    <th>Plate Image</th>
                </tr>
            </thead>

            <tbody>
    `;


    plates.forEach(
        (plate, index) => {

            const plateNumber =
                plate.plate_number ||
                "Not Recognized";


            const plateConfidence =
                plate.plate_confidence != null
                    ? Math.round(
                        plate.plate_confidence * 100
                    ) + "%"
                    : "-";


            const ocrConfidence =
                plate.ocr_confidence != null
                    ? Math.round(
                        plate.ocr_confidence * 100
                    ) + "%"
                    : "-";


            const isSuccess =
                plateNumber !== "Not Recognized";


            const statusBadge =
                isSuccess
                    ? `<span class="badge bg-success">
                           Successful
                       </span>`
                    : `<span class="badge bg-danger">
                           Not Recognized
                       </span>`;


            const imageUrl =
                plate.image_url || "";


            const imageButton =
                imageUrl
                    ? `
                        <a
                            href="${imageUrl}"
                            target="_blank"
                            class="btn btn-sm btn-outline-primary"
                        >
                            <i class="fa-solid fa-image"></i>
                            View
                        </a>
                      `
                    : "-";


            html += `
                <tr>

                    <td>${index + 1}</td>

                    <td>
                        <strong
                            class="text-primary"
                            style="font-size: 1.1rem;"
                        >
                            ${escapeHTML(
                                plateNumber
                            )}
                        </strong>
                    </td>

                    <td>
                        ${plateConfidence}
                    </td>

                    <td>
                        ${ocrConfidence}
                    </td>

                    <td>
                        ${statusBadge}
                    </td>

                    <td>
                        ${imageButton}
                    </td>

                </tr>
            `;
        }
    );


    html += `
            </tbody>
        </table>
    `;


    plateResults.innerHTML = html;
}


// =========================================================
// HTML SAFETY
// =========================================================

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// =========================================================
// BUTTON EVENT
// =========================================================

if (anprButton) {

    anprButton.addEventListener(
        "click",
        runANPR
    );
}


// =========================================================
// FILE CHANGE
// =========================================================

if (anprFile) {

    anprFile.addEventListener(
        "change",
        function () {

            hideError();

            // Reset old results
            anprResult.classList.add("d-none");

            vehicleCount.textContent = "0";
            plateCount.textContent = "0";
            ocrStatus.textContent = "-";

            vehicleResults.innerHTML = "";
            plateResults.innerHTML = "";

            outputImage.src = "";

        }
    );
}