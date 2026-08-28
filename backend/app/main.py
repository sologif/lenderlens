import os
import sys

# Ensure backend/app directory is on sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from database import init_db
from config import PROTOTYPE_DISCLAIMER
from routers import analyze, cases, lenders, demo

# Initialize SQLite database schema
init_db()

# Auto-train ML models on first startup (Render deploy / fresh clone)
import os as _os
_weights_dir = _os.path.join(APP_DIR, "models", "weights")
_iso_path = _os.path.join(_weights_dir, "lstm_iso_forest.pkl")
_gnn_path = _os.path.join(_weights_dir, "gnn_classifier.pkl")
if not (_os.path.exists(_iso_path) and _os.path.exists(_gnn_path)):
    print("ML weights not found — training models now...")
    try:
        from train_ml_models import train_all
        train_all()
        print("ML models trained successfully.")
    except Exception as _e:
        print(f"Warning: ML model training failed ({_e}). Falling back to heuristic scoring.")

app = FastAPI(
    title="LenderLens API",
    description="AI-powered Loan Fraud Detection & Early-Warning System Backend",
    version="1.0.0"
)

# Configure CORS for Chrome Extension & Dashboard Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analyze.router)
app.include_router(cases.router)
app.include_router(lenders.router)
app.include_router(demo.router)

# Mount Static Folders
BASE_DIR = os.path.dirname(APP_DIR)
DEMO_DIR = os.path.join(BASE_DIR, "demo_sites")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DASHBOARD_DIR = os.path.join(os.path.dirname(BASE_DIR), "extension", "dashboard")

os.makedirs(DEMO_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/demo", StaticFiles(directory=DEMO_DIR, html=True), name="demo_sites")
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if os.path.exists(DASHBOARD_DIR):
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")

@app.get("/")
def home_page():
    landing_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(landing_file):
        return FileResponse(landing_file)
    return {
        "system": "LenderLens AI Fraud Detection Platform",
        "version": "1.0.0",
        "status": "ONLINE",
        "disclaimer": PROTOTYPE_DISCLAIMER
    }

@app.get("/download-extension")
def download_extension():
    zip_path = os.path.join(STATIC_DIR, "lenderlens-extension.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="lenderlens-extension.zip", media_type="application/zip")
    return RedirectResponse(url="/static/lenderlens-extension.zip")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "lenderlens-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
