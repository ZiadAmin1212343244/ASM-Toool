"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.exceptions import EngagementRequired, NotAuthenticated
from app.config import BASE_DIR, get_settings
from app.database import init_db
from app.routers import auth, dashboard, vendors


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=False,
    )

    static_dir = BASE_DIR / "app" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(vendors.router)

    @app.on_event("startup")
    def _startup() -> None:
        Path(settings.file_storage_path).mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
        init_db()

    @app.exception_handler(NotAuthenticated)
    async def _not_authenticated(_request: Request, _exc: NotAuthenticated):
        return RedirectResponse(url="/login", status_code=303)

    @app.exception_handler(EngagementRequired)
    async def _engagement_required(_request: Request, _exc: EngagementRequired):
        return RedirectResponse(url="/", status_code=303)

    return app


app = create_app()
