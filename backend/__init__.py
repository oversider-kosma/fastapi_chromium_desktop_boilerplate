from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .constants import STATIC_DIR
from .routes import system, static

app: FastAPI = FastAPI()

app.include_router(system.router)
app.include_router(static.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
