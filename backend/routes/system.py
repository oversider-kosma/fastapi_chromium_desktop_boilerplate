from typing import Dict
from fastapi import APIRouter
from utils import get_version

router = APIRouter()

@router.get("/hello")
async def hello() -> Dict[str, str]:
    return {"status": "ok", "message": "Hello from FastAPI"}

@router.get("/getVersion")
async def get_version_endpoint() -> Dict[str, str]:
    return {"status": "ok", "version": get_version()}
