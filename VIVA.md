# AI Vision Hub — Viva Preparation

## Project Objective
Build an end-to-end AI system that detects vehicles in an image, locates
their number plates, reads the plate text using OCR, and stores every
detection in a database with a web dashboard for monitoring and analytics.

## Problem Statement
Manual vehicle/plate identification (e.g. for parking access, toll
booths, traffic monitoring) is slow and error-prone. An automated
pipeline that detects vehicles, isolates plates, and extracts text
reduces manual effort and enables real-time record-keeping.

## Existing System
Traditional ANPR setups often rely on either expensive proprietary
hardware/software, or single-purpose scripts with no web interface,
no persistent history, and no analytics — making them hard to monitor
or audit over time.

## Proposed System
A modular web application:
- **YOLO** models detect vehicles and plates separately (two specialized
  models beat one general model trying to do both).
- **PaddleOCR** extracts text from the cropped plate image.
- **FastAPI** backend exposes clean REST endpoints and persists every
  detection to a **SQLite** database via **SQLAlchemy**.
- A **Bootstrap** frontend lets a user upload images, view results, and
  browse history/analytics — no manual DB queries needed.

## System Architecture
```
Browser (Bootstrap + JS)
        |  fetch() / multipart form-data
        v
FastAPI (main.py)
   |-- /vehicle/detect --> vehicle_detector.py (YOLO) --> DB
   |-- /plate/detect   --> plate_detector.py (YOLO) --> ocr_engine.py (PaddleOCR) --> DB
   |-- /history         --> reads DB
   |-- /analytics/*      --> aggregates DB
   |-- /auth/*           --> users table (JWT)
        |
        v
   SQLite (ai_vision_hub.db)
```

## Modules
1. **Vehicle Detection Module** — YOLO model trained on vehicle classes
   (car/motorcycle/truck/bus), draws bounding boxes, returns counts.
2. **Plate Detection Module** — separate YOLO model trained specifically
   on number plates; crops each detected plate region.
3. **OCR Module** — PaddleOCR reads text from each plate crop, cleans it
   (uppercase, strip noise characters), and reports "Not Recognized"
   rather than guessing when confidence is low.
4. **Database Module** — SQLAlchemy ORM, one `detections` table shared by
   both vehicle and plate rows (`detection_type` column distinguishes them).
5. **API Module** — FastAPI routers, each returning the same
   `{success, message, data}` JSON shape.
6. **Frontend Module** — Bootstrap pages: Dashboard, Vehicle Detection,
   Plate Detection, History, Analytics.
7. **Auth Module** — JWT-based register/login (bcrypt password hashing).

## Technology Stack — Why each choice
- **Why YOLO?** Real-time, single-pass object detection — fast enough
  for interactive web use, and Ultralytics' Python API is simple to
  integrate. Using two separate YOLO models (vehicle, plate) lets each
  one specialize and stay accurate, rather than one model juggling very
  different object scales (a whole car vs. a small plate).
- **Why FastAPI?** Async-native, automatic OpenAPI docs (`/docs`), built-in
  request validation via Pydantic, and it's fast to develop in — good fit
  for a student project that still needs to look production-quality.
- **Why OCR (PaddleOCR)?** YOLO only locates the plate region — it
  doesn't read text. OCR is a separate, specialized problem (text
  recognition), so a dedicated OCR engine is needed after detection.
- **Why SQLite?** Zero-configuration, file-based — no separate DB server
  needed, which is ideal for a self-contained student project/demo.
- **Why JWT auth?** Stateless — the server doesn't need to store session
  data, and it's the standard approach for API-based auth.

## How Vehicle Detection Works
1. User uploads an image.
2. Backend saves it with a unique filename (never overwrites another
   user's file).
3. YOLO (`vehicle.pt`) runs inference, returning bounding boxes, class
   IDs, and confidence scores.
4. Backend draws boxes/labels on the image, saves an annotated copy with
   a UUID filename, and returns counts + a browser-accessible image URL.
5. Each detected vehicle is saved as a row in the `detections` table.

## How Number Plate Detection Works
1. User uploads a vehicle image.
2. YOLO (`plate.pt`) detects plate regions (confidence ≥ 0.35 to avoid
   noisy/duplicate boxes).
3. Each valid plate region is cropped and saved as its own image.
4. The crop is passed to OCR.
5. Results (plate text or "Not Recognized", confidence, image URL) are
   returned and saved to the DB.

## How OCR Works
PaddleOCR performs two steps internally: **text detection** (finds where
text is in the crop) and **text recognition** (reads the characters).
The raw output is cleaned (uppercased, non-alphanumeric characters
stripped) and checked against a confidence threshold — low-confidence or
malformed results are reported as "Not Recognized" instead of a guess,
since a wrong plate number is worse than admitting uncertainty.

## Database Design
Single `detections` table:
| Column | Type | Meaning |
|---|---|---|
| id | Integer PK | |
| detection_type | String | `"vehicle"` or `"plate"` |
| vehicle_type | String, nullable | car/motorcycle/etc. (vehicle rows only) |
| vehicle_confidence | Float, nullable | |
| plate_number | String, nullable | OCR result or "Not Recognized" |
| plate_confidence | Float, nullable | |
| plate_image_path | String, nullable | cropped plate image URL |
| image_path | String, nullable | annotated/original image URL |
| created_at | DateTime | |

A single `users` table backs authentication (id, full_name, email,
password_hash, phone, role, created_at).

## API Architecture
REST endpoints, each returning `{success, message, data}`:
- `GET /`, `GET /health`
- `POST /vehicle/detect`, `POST /plate/detect`
- `GET /history/`, `GET /history/search`, `DELETE /history/{id}`
- `GET /analytics/summary`, `/vehicles`, `/plates`, `/timeline`
- `POST /auth/register`, `POST /auth/login`

## Frontend Architecture
Five pages sharing one navbar and stylesheet (`css/style.css`), each with
its own JS file that talks to the backend via `fetch()`. No frontend
framework — plain JS keeps it simple to explain and demo, per your
requirement. Bootstrap 5 handles layout/responsiveness; Chart.js renders
analytics; Font Awesome supplies icons.

## Advantages
- Fully automated pipeline — no manual plate reading.
- Persistent history + analytics for auditing.
- Modular — vehicle detection, plate detection, and OCR can each be
  swapped/retrained independently.
- Clean REST API — could plug into a mobile app or another system later.

## Limitations
- OCR accuracy depends on image quality, lighting, and plate condition.
- YOLO models need to be retrained/fine-tuned for new plate formats or
  regions.
- SQLite isn't suited for high-concurrency production use (fine for a
  student project/demo).
- No user-facing authentication is currently wired into the detection
  pages themselves (auth exists as an API but isn't enforced on
  `/vehicle/detect` etc. — a reasonable next step).

## Future Enhancements
- Enforce JWT auth on detection endpoints (multi-user system).
- Video stream support (real-time detection from a live camera feed).
- Multi-region plate format validation.
- Deploy with PostgreSQL for production scale.
- Add a confidence-based review queue for low-confidence OCR results.

---

## Likely Viva Questions & Simple Answers

**Q: Why two separate YOLO models instead of one?**
A: A vehicle and a plate are very different scales/shapes in an image.
Two specialized models are each simpler to train well than one model
trying to detect both accurately.

**Q: What happens if OCR can't read the plate?**
A: The system returns `"Not Recognized"` instead of guessing — inventing
a wrong plate number would be worse than admitting the OCR failed.

**Q: How do you prevent duplicate/junk plate crops?**
A: The plate model's confidence threshold was raised to 0.35 and results
are capped at 5 detections per image, filtering out low-quality boxes.

**Q: How does the frontend talk to the backend?**
A: Via `fetch()` calls to REST endpoints, sending images as
`multipart/form-data` and receiving JSON back in a consistent
`{success, message, data}` shape.

**Q: Why store everything in one `detections` table instead of two?**
A: History and Analytics need to show both types of detections together
(e.g., total detections, today's detections) — one table with a
`detection_type` column keeps those queries simple, instead of joining
or unioning two separate tables everywhere.

**Q: How is a user's password protected?**
A: Hashed with bcrypt (via passlib) before storage — the plaintext
password is never saved, only its hash.

**Q: What's returned if the uploaded file isn't an image?**
A: A `400 Bad Request` with a clear message (`"Only JPG, JPEG, PNG and
WEBP images are supported."`) — validated before any processing happens.

**Q: How would you scale this for production?**
A: Swap SQLite for PostgreSQL, add authentication on detection routes,
move image storage to cloud storage (e.g. S3) instead of local disk, and
run the YOLO models on a GPU-backed server for faster inference.
