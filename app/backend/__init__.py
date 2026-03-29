from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.middleware import NoCacheMiddleware

from .constants import STATIC_DIR
from .routes import system, static


app: FastAPI = FastAPI()

# no actual need for caching when server and client interacts through localhost loopback
app.add_middleware(NoCacheMiddleware)

app.include_router(system.router)
app.include_router(static.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
