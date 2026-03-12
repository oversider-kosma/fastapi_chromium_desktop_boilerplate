from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from utils import get_base_path, get_version


app: FastAPI = FastAPI()


STATIC_DIR: Path = get_base_path() / "frontend" / "static"
FAVICON_PATH: Path = STATIC_DIR / "favicon.ico"

if not STATIC_DIR.exists():
    print(f"[!] Static dir not found at {STATIC_DIR}")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)


@app.get("/hello")
async def hello() -> Dict[str, str]:
    return {"status": "ok", "message": "Hello from FastAPI"}


@app.get("/", response_class=FileResponse)
def read_root() -> Path:
    return get_base_path() / "frontend" / "index.html"


@app.get("/getVersion")
async def get_version_endpoint() -> Dict[str, str]:
    return {"status": "ok", "version": get_version()}
