// =========================================================
// AI VISION HUB - HISTORY PAGE
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const API_BASE_URL = "http://127.0.0.1:8000";

    const table = document.getElementById("historyTable");
    const pagination = document.getElementById("pagination");
    const errorBox = document.getElementById("historyError");
    const searchInput = document.getElementById("searchPlate");
    const typeFilter = document.getElementById("typeFilter");
    const searchBtn = document.getElementById("searchBtn");
    const clearBtn = document.getElementById("clearBtn");

    const PAGE_SIZE = 10;
    let currentPage = 1;

    async function loadHistory(page = 1) {

        currentPage = page;
        errorBox.classList.add("d-none");

        try {

            const type = typeFilter.value;
            let url = `${API_BASE_URL}/history/?page=${page}&page_size=${PAGE_SIZE}`;
            if (type) url += `&detection_type=${type}`;

            const response = await fetch(url);
            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.message || `Request failed: ${response.status}`);
            }

            renderTable(json.data.history || []);
            renderPagination(json.data.total_records || 0, page);

        } catch (error) {
            console.error("History error:", error);
            errorBox.textContent = error.message || "Unable to load history.";
            errorBox.classList.remove("d-none");
        }
    }

    async function searchPlate(plate) {

        errorBox.classList.add("d-none");

        try {
            const response = await fetch(`${API_BASE_URL}/history/search?plate=${encodeURIComponent(plate)}`);
            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.message || `Request failed: ${response.status}`);
            }

            renderTable(json.data.history || []);
            pagination.innerHTML = "";

        } catch (error) {
            console.error("Search error:", error);
            errorBox.textContent = error.message || "Search failed.";
            errorBox.classList.remove("d-none");
        }
    }

    function renderTable(rows) {

        if (rows.length === 0) {
            table.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No records found</td></tr>`;
            return;
        }

        table.innerHTML = rows.map(row => {

            const confidence = row.detection_type === "vehicle"
                ? row.vehicle_confidence
                : row.plate_confidence;

            const imageUrl = row.plate_image_path || row.image_path;

            return `
                <tr>
                    <td>${row.id}</td>
                    <td><span class="badge bg-secondary">${row.detection_type}</span></td>
                    <td>${row.vehicle_type || "-"}</td>
                    <td>${row.plate_number || "-"}</td>
                    <td>${confidence != null ? Math.round(confidence * 100) + "%" : "-"}</td>
                    <td>${new Date(row.created_at).toLocaleString()}</td>
                    <td>${imageUrl ? `<a href="${imageUrl}" target="_blank"><i class="fa-solid fa-image"></i> View</a>` : "-"}</td>
                    <td><button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${row.id})"><i class="fa-solid fa-trash"></i></button></td>
                </tr>
            `;
        }).join("");
    }

    function renderPagination(totalRecords, page) {

        const totalPages = Math.ceil(totalRecords / PAGE_SIZE);
        pagination.innerHTML = "";

        if (totalPages <= 1) return;

        for (let p = 1; p <= totalPages; p++) {
            const li = document.createElement("li");
            li.className = `page-item ${p === page ? "active" : ""}`;
            li.innerHTML = `<a class="page-link" href="#">${p}</a>`;
            li.addEventListener("click", e => { e.preventDefault(); loadHistory(p); });
            pagination.appendChild(li);
        }
    }

    window.deleteRecord = async function (id) {

        if (!confirm("Delete this record?")) return;

        try {
            const response = await fetch(`${API_BASE_URL}/history/${id}`, { method: "DELETE" });
            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.message || "Delete failed.");
            }

            loadHistory(currentPage);

        } catch (error) {
            alert(error.message || "Unable to delete record.");
        }
    };

    searchBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const value = searchInput.value.trim();
        if (value) searchPlate(value); else loadHistory(1);
    });

    clearBtn.addEventListener("click", function (e) {
        e.preventDefault();
        searchInput.value = "";
        typeFilter.value = "";
        loadHistory(1);
    });

    typeFilter.addEventListener("change", () => loadHistory(1));

    loadHistory(1);
});
