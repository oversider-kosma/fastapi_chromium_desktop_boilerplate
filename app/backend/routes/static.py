from fastapi import APIRouter
from fastapi.responses import FileResponse
from ..constants import FAVICON_PATH, INDEX_PATH

router = APIRouter()

@router.get('/favicon.ico', include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)

@router.get("/", response_class=FileResponse)
def read_root():
    return INDEX_PATH
