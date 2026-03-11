from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from utils import get_base_path, get_version, print_current_dir

app = FastAPI()

STATIC_DIR = get_base_path() / "frontend" / "static"
FAVICON_PATH = STATIC_DIR / "favicon.ico"

if not STATIC_DIR.exists():
    print(f"[!] Static dor not found at {STATIC_DIR}")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(FAVICON_PATH)


@app.get("/hello")
def hello():
    return {"status": "ok", "message": "Hello from FastAPI"}


@app.get("/", response_class=FileResponse)
def read_root():
    return get_base_path() / "frontend" / "index.html"


@app.get("/getVersion")
async def get_version_endpoint():
    return {"status": "ok", "version": get_version()}
