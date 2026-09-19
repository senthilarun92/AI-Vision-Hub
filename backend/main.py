from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

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

BASE_DIR = Path(__file__).resolve().parent

OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOADS_DIR = BASE_DIR / "uploads"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# STATIC OUTPUT IMAGES
# =========================================================
# Browser-accessible:
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
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "AI Vision Hub Backend is running",
        "status": "success"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Vision Hub API"
    }