from pathlib import Path
from utils import get_base_path

STATIC_DIR: Path = get_base_path() / "frontend" / "static"
FAVICON_PATH: Path = STATIC_DIR / "favicon.ico"
INDEX_PATH: Path = get_base_path() / "frontend" / "index.html"

if not STATIC_DIR.exists():
    print(f"[!] Static dir not found at {STATIC_DIR}")
