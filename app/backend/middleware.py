from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request,
                       call_next: Callable[[Request], Response]) -> Response:
        response: Response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
