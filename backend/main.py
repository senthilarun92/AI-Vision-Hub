from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.utils.responses import error_response


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="AI Vision Hub",
    description=(
        "AI-powered Vehicle Detection "
        "and Automatic Number Plate Recognition System"
    ),
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================
# Student project frontend using plain fetch() with Bearer token.
# No cookies are used, so credentialed CORS is not required.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# GLOBAL ERROR HANDLING
# =========================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.detail))
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    print("UNHANDLED ERROR:", repr(exc))

    return JSONResponse(
        status_code=500,
        content=error_response(
            "Internal server error. Please try again."
        )
    )


# =========================================================
# PROJECT PATHS
# =========================================================

# backend/
BASE_DIR = Path(__file__).resolve().parent

# ai_vision_hub_v2/
PROJECT_DIR = BASE_DIR.parent

# frontend/
FRONTEND_DIR = PROJECT_DIR / "frontend"

# frontend/css/
CSS_DIR = FRONTEND_DIR / "css"

# frontend/js/
JS_DIR = FRONTEND_DIR / "js"

# frontend/images/
IMAGES_DIR = FRONTEND_DIR / "images"

# backend/outputs/
OUTPUTS_DIR = BASE_DIR / "outputs"

# backend/uploads/
UPLOADS_DIR = BASE_DIR / "uploads"


# =========================================================
# CREATE REQUIRED DIRECTORIES
# =========================================================

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# FRONTEND STATIC FILES
# =========================================================
# Existing HTML files can continue using:
#
# css/style.css
# js/dashboard.js
# js/analytics.js
# js/anpr.js
#
# FastAPI will serve them directly.

if CSS_DIR.exists():
    app.mount(
        "/css",
        StaticFiles(directory=str(CSS_DIR)),
        name="css"
    )

if JS_DIR.exists():
    app.mount(
        "/js",
        StaticFiles(directory=str(JS_DIR)),
        name="js"
    )

if IMAGES_DIR.exists():
    app.mount(
        "/images",
        StaticFiles(directory=str(IMAGES_DIR)),
        name="images"
    )


# =========================================================
# OUTPUT STATIC FILES
# =========================================================
# Browser-accessible:
#
# http://127.0.0.1:8000/outputs/<filename>

app.mount(
    "/outputs",
    StaticFiles(directory=str(OUTPUTS_DIR)),
    name="outputs"
)


# =========================================================
# DATABASE TABLES
# =========================================================

from backend.database.init_db import init_database

init_database()


# =========================================================
# ROUTERS
# =========================================================

from backend.routes import vehicle
from backend.routes import plate
from backend.routes import history
from backend.routes import analytics
from backend.routes import auth
from backend.routes import dashboard
from backend.routes import anpr


# =========================================================
# INCLUDE ROUTERS
# =========================================================

app.include_router(vehicle.router)
app.include_router(plate.router)
app.include_router(history.router)
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(dashboard.router)

# ANPR
app.include_router(anpr.router)


# =========================================================
# FRONTEND PAGE HELPER
# =========================================================

def frontend_page(filename: str):
    """
    Return a frontend HTML page from the frontend folder.
    """

    page_path = FRONTEND_DIR / filename

    if not page_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Frontend page not found: {filename}"
        )

    return FileResponse(str(page_path))


# =========================================================
# ROOT - HOME PAGE
# =========================================================

@app.get("/")
def root():
    return frontend_page("index.html")


# =========================================================
# FRONTEND PAGES
# =========================================================

@app.get("/index.html")
def index_page():
    return frontend_page("index.html")


@app.get("/dashboard.html")
def dashboard_page():
    return frontend_page("dashboard.html")


@app.get("/vehicle.html")
def vehicle_page():
    return frontend_page("vehicle.html")


@app.get("/plate.html")
def plate_page():
    return frontend_page("plate.html")


@app.get("/history.html")
def history_page():
    return frontend_page("history.html")


@app.get("/analytics.html")
def analytics_page():
    return frontend_page("analytics.html")


@app.get("/anpr.html")
def anpr_page():
    return frontend_page("anpr.html")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Vision Hub API"
    }