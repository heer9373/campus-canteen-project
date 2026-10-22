"""
main.py
Campus Canteen Dynamic Smart-Menu & Analytics Engine — FastAPI Entry Point
Implements FR-1..FR-6 and NFR-1..NFR-3 per the SRS.

Run with:  uvicorn app.main:app --reload --port 8000
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.utils.slots import ensure_slots_for_today
from app.routers import auth, menu, slots, orders, analytics, ws

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Campus Canteen Smart-Menu & Analytics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(slots.router)
app.include_router(orders.router)
app.include_router(analytics.router)
app.include_router(ws.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


# --- Startup: init DB, generate today's slots, start background tasks ---
@app.on_event("startup")
async def on_startup():
    init_db()
    ensure_slots_for_today()
    asyncio.create_task(_slot_refresh_loop())
    asyncio.create_task(_daily_backup_loop())


async def _slot_refresh_loop():
    """NFR: keep slot windows rolling forward every 15 minutes."""
    while True:
        await asyncio.sleep(15 * 60)
        ensure_slots_for_today()


async def _daily_backup_loop():
    """NFR-3: simple daily backup, checks once a minute for 23:59."""
    backup_dir = BASE_DIR.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    last_backup_date = None
    db_path = BASE_DIR.parent / "canteen.db"

    while True:
        now = datetime.now()
        if now.hour == 23 and now.minute == 59 and last_backup_date != now.date():
            try:
                dest = backup_dir / f"canteen-{now.strftime('%Y%m%d-%H%M%S')}.db"
                shutil.copyfile(db_path, dest)
                last_backup_date = now.date()
                print(f"[backup] Daily backup created: {dest}")
            except Exception as e:
                print(f"[backup] Failed: {e}")
        await asyncio.sleep(60)


# --- Serve the frontend (plain HTML/CSS/JS) ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
