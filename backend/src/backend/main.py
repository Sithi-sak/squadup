import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .core.supabase import get_supabase_client
from .routers import routers

settings = get_settings()

app = FastAPI(title="SquadUp API")

logger = logging.getLogger(__name__)


@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    """Turns an unhandled exception into a plain 500 JSON body. Starlette's own error handler sits
    *outside* the CORS middleware, so its response carries no `Access-Control-Allow-Origin` and
    the browser reports the whole request as "Failed to fetch" with no status or message. This
    runs inside CORS (registered first = inner), so the frontend gets the real status and can
    show something better than a network error."""
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Something went wrong on our end"}, status_code=500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/supabase", tags=["health"])
def health_supabase() -> dict[str, str]:
    get_supabase_client().auth.admin.list_users()
    return {"status": "ok"}
