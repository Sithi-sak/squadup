from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.supabase import get_supabase_client
from .routers import routers

settings = get_settings()

app = FastAPI(title="SquadUp API")

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
