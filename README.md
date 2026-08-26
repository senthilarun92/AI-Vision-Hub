# AI Vision Hub — Complete Project Guide

Intelligent Vehicle Detection + Automatic Number Plate Recognition (ANPR)
Backend: FastAPI + SQLAlchemy + YOLO (Ultralytics) + PaddleOCR
Frontend: HTML5 + Bootstrap 5 + Vanilla JS + Chart.js + Font Awesome

---

## PHASE 1–3: Inspection Summary & Architecture

**What was already working:** auth, database connection, YOLO model loading,
core detection logic in `vehicle_detector.py` / `plate_detector.py`.

**What was broken:**
- `Detection` table had no `vehicle_type` / `detection_type` field, so
  vehicle detections were never saved — History/Analytics only ever
  reflected plate data.
- Every route returned a different JSON shape, so the frontend had to
  guess field names (`plate.text || plate.plate_text || plate.plate_number...`)
  — a major source of "no result appears" bugs.
- `ocr_engine.py` imported `easyocr`, which isn't in your `requirements.txt`
  (you use PaddleOCR) — this crashed the whole server on startup.
- `bcrypt` had no pinned version — a fresh install pulls bcrypt 5.x, which
  breaks `passlib` 1.7.4 and makes every register/login call fail.
- `auth` and `dashboard` routers were written but never registered in
  `main.py` (404s).
- No DB table auto-creation on startup.
- `plate.js` built a broken image URL from the wrong field (`image_path`
  instead of `image_url`), so plate crop images 404'd.
- Plate detector used `conf=0.10` (too low) and `max_det=10`, causing
  excess low-quality duplicate crop images.
- No standard error format — Python errors could leak to the frontend.
- Pages required by your spec (`index.html`, `history.html`,
  `analytics.html`, `vehicle.js`, `history.js`, `analytics.js`) didn't exist.

**New architecture:** one unified `detections` table (`detection_type` =
`"vehicle"` or `"plate"`) so History/Analytics need only one query. Every
API response now uses the exact same shape:

```json
{ "success": true, "message": "...", "data": { ... } }
```

Errors — validation, HTTP, or unexpected — all come back the same way
through a global FastAPI exception handler, with a proper HTTP status
code and no leaked Python stack trace.

---

## PHASE 4: "Detect Button Reloads the Page" — Investigation Result

I checked every `<button>` and `<form>` in your uploaded `vehicle.html`
and `plate.html` directly:

- **There is no `<form>` element on either page.**
- The Detect buttons are already `type="button"` (vehicle.html even has
  a comment explaining why).
- Element IDs are unique — no duplicate-`id` bug that could silently
  detach the click handler.

So the exact code you uploaded **cannot** page-reload from a native form
submission — that specific bug doesn't exist in what you sent me. Most
likely explanations for what you saw:

1. A local dev tool (e.g. VS Code "Live Server") auto-refreshing the page
   when you saved a file while testing — not a code bug.
2. An older/different local copy than what got uploaded here.

I still hardened every Detect button in the rewrite:
`event.preventDefault()` is called defensively in every click handler,
and buttons remain outside any `<form>`. If a reload still happens after
this, open the browser DevTools **Console** tab when it occurs and send
me the exact error — that will tell us definitively.

---

## PHASE 5: What Changed

| File | Change |
|---|---|
| `backend/models/detection.py` | Unified schema: `detection_type`, `vehicle_type`, `vehicle_confidence`, `plate_number`, `plate_confidence`, `image_path`, `plate_image_path` |
| `backend/utils/responses.py` | **New** — `success_response()` / `error_response()` helpers used everywhere |
| `backend/ai/ocr_engine.py` | Switched EasyOCR → PaddleOCR; cleans OCR text; returns `"Not Recognized"` instead of guessing |
| `backend/ai/plate_detector.py` | `conf` raised 0.10→0.35, `max_det` 10→5 (fewer junk crops), UUID filenames |
| `backend/ai/vehicle_detector.py` | UUID filenames, per-class counts, returns ready-to-use image URL |
| `backend/routes/vehicle.py` | Saves each detection to DB, standard response, proper status codes |
| `backend/routes/plate.py` | OCR status per plate, saves to DB, standard response |
| `backend/routes/history.py` | Filter by type, search, pagination, delete |
| `backend/routes/analytics.py` | `/summary`, `/vehicles`, `/plates`, `/timeline` |
| `backend/routes/dashboard.py` | Updated for unified schema |
| `backend/routes/auth.py` | Standard response format |
| `backend/main.py` | Global error handler, `/health`, DB init on startup, all routers registered, open CORS |
| `frontend/*` | Rebuilt in Bootstrap 5 + Chart.js + Font Awesome; all JS updated for the new `{success, message, data}` format |
| `backend/ai/plate_detector.py` (2nd pass) | Added debug logging (raw detection count, per-box confidence/size/aspect ratio, accept/reject reason) + geometric sanity filters (min size 40x14px, aspect ratio 1.3–8.0) instead of relying only on a high confidence threshold — see "Problem B & C" below |
| `backend/routes/plate.py` (2nd pass) | Response now includes both `plate_number` and `ocr` fields (same value) to match your requested structure exactly |

---

## Problem B: Tiny 16x16 output images — root cause & fix

The old code used `conf=0.10` (too low) with only a weak size filter
(`< 20x8px`). That let near-noise boxes through, which got saved as
tiny, useless crop files.

**Fix:** confidence is now a moderate `0.25` (not raised too high — see
Problem C below), and rejection is now handled by **geometric checks**:
minimum 40×14px, and aspect ratio between 1.3–8.0 (a real plate is
always noticeably wider than tall — never a 16×16 square). Every
rejected box prints exactly why to your terminal, so you can verify
this against your own model's real output.

## Problem C: "No Number Plate Detected" on a clearly visible plate

The most likely cause of this — coming right after Problem B was
probably fixed by *raising* confidence too far in an earlier attempt —
is `conf` being set too high for your specific trained model's actual
confidence output on real photos. There's no universal "correct"
threshold; it depends entirely on how your model was trained.

**Fix:** confidence reset to a moderate `0.25` (not the very low `0.10`
that caused Problem B, and not an aggressively high value that would
cause Problem C). Junk is filtered by shape/size instead of by
confidence alone. **Debug logging was added specifically so you can
diagnose this yourself with your real model**: run a detection and read
your terminal — it will show you exactly:
- how many raw boxes YOLO found at all
- each box's confidence, size, and aspect ratio
- whether each was accepted or rejected, and why

If YOLO reports **zero raw detections** even before filtering, the issue
is the model/image (try a closer, well-lit photo, or the model may need
retraining on similar photos). If YOLO finds boxes but they all get
rejected, the printed reason (too small / bad aspect ratio) tells you
exactly which constant to relax in `plate_detector.py` (`CONF_THRESHOLD`,
`MIN_PLATE_WIDTH`, `MIN_PLATE_HEIGHT`, `MIN_ASPECT_RATIO`,
`MAX_ASPECT_RATIO` — all defined at the top of the file with comments).

---

## PHASE 6: requirements.txt

See `requirements.txt` in this package — same as your original, with
`bcrypt==4.0.1` pinned (fixes the passlib crash) and `python-multipart`
confirmed present (needed for file uploads).

---

## PHASE 7: Database Setup

Nothing manual needed — `main.py` calls `init_database()` on startup,
which runs `Base.metadata.create_all()` and creates `users` and
`detections` tables in `ai_vision_hub.db` automatically if they don't
exist yet. Your existing `ai_vision_hub.db` (2 users, 456 detections)
was **not** included in this package (kept out to avoid overwriting your
real data / it's correctly `.gitignore`d) — copy it back into the
project root if you want to keep that history, otherwise a fresh one is
created automatically.

⚠️ Note: your old DB rows won't have `detection_type` set — old rows will
show as blank/"vehicle" default in History until you generate new
detections with the updated app.

---

## PHASE 8: How to Run the Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Run from the PROJECT ROOT (not inside backend/) so relative paths
# like "backend/weights/..." resolve correctly:
uvicorn backend.main:app --reload
```

Place your trained models at `backend/weights/vehicle.pt` and
`backend/weights/plate.pt` first (not included — see below).

Backend runs at: **http://127.0.0.1:8000**
Interactive API docs: **http://127.0.0.1:8000/docs**

---

## PHASE 9: How to Run the Frontend

The frontend is plain HTML/JS — no build step. Simplest option:

```bash
cd frontend
python -m http.server 5500
```

Then open **http://127.0.0.1:5500/index.html**. (VS Code's "Live Server"
extension works too — right-click `index.html` → "Open with Live Server".)

---

## PHASE 10: Test Vehicle Detection

1. Go to **Vehicle Detection** page.
2. Choose an image with visible vehicles → click **Detect Vehicles**.
3. Expect: annotated image with bounding boxes, total count, a
   per-class table. Each detection is saved to the DB automatically
   (check the **History** page afterward).

## PHASE 11: Test Plate Detection + OCR

1. Go to **Plate Detection** page.
2. Choose a clear vehicle/plate image → click **Detect Number Plate**.
3. Expect: cropped plate image(s), OCR status badge (Successful/Failed),
   plate text or "Not Recognized". Every valid detection is saved to the DB.

## PHASE 12: Test History

Go to **History**. Filter by type (vehicle/plate), search a plate number,
paginate, click "View" to open a saved image, delete a record.

## PHASE 13: Test Analytics

Go to **Analytics**. All four stat cards and three charts (vehicle type
pie, OCR success/failure bar, 14-day timeline) should populate from real
DB data — generate a few detections first if the DB is empty.

---

## PHASE 14: Common Errors & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'easyocr'` | Already fixed — `ocr_engine.py` now uses PaddleOCR | — |
| `ValueError: password cannot be longer than 72 bytes` on register/login | bcrypt/passlib mismatch | Already fixed via `bcrypt==4.0.1` pin — re-run `pip install -r requirements.txt` |
| `RuntimeError: Form data requires "python-multipart"` | Missing package | Already in requirements.txt — reinstall |
| `sqlite3.OperationalError: no such table` | DB not initialized | Already fixed — `init_database()` runs on startup |
| Images 404 in the browser | Wrong static path | Already fixed — every image URL now comes straight from the backend's `/outputs/` mount |
| "Failed to fetch" in browser console | Backend not running, or wrong port | Confirm `uvicorn` is running and `http://127.0.0.1:8000/health` returns `{"status":"ok"}` |
| Vehicle/plate model fails to load | `backend/weights/vehicle.pt` or `plate.pt` missing | Place your trained `.pt` files there — see below |

---

## Still needed from you

Nothing — **your trained models (`vehicle.pt`, `plate.pt`) are included in
this package** at `backend/weights/`. Verified against your actual
files in this session:

```
vehicle.pt classes: {0: 'cars', 1: 'motorcycle', 2: 'tricycle', 3: 'truck_and_bus'}
plate.pt classes:   {0: 'License Plate - v1 2024-06-18 8-24pm'}
```

Both models were loaded for real (not stubbed) and run end-to-end
through the actual `/vehicle/detect` and `/plate/detect` API endpoints
on a real photo — detections came back correctly, saved to the
database, and showed up in `/dashboard/stats` and `/analytics/vehicles`.
(The test photo had no license plate in it, so plate detection correctly
returned "No number plate detected" with zero false positives — that's
the expected, correct behavior, not a bug.)

If you want to keep your existing 456-detection history, copy your old
`ai_vision_hub.db` into the project root yourself — it wasn't included
here to avoid overwriting anything.

See **VIVA.md** in this package for the project explanation, module
breakdown, and likely viva questions with answers.
