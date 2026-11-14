"""Login / logout routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.deps import get_session_user
from app.auth.security import verify_password
from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models.user import User
from app.services.audit import write_audit

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_session_user(request, db):
        return RedirectResponse("/", status_code=303)
    settings = get_settings()
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "error": None,
        },
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "error": "Invalid email or password.",
            },
            status_code=401,
        )

    request.session["user_id"] = user.id
    # Auto-select first engagement if none set
    from app.auth.deps import user_engagements

    engagements = user_engagements(db, user)
    if engagements and not request.session.get("engagement_id"):
        request.session["engagement_id"] = engagements[0].id

    write_audit(
        db,
        action="login",
        user=user,
        detail=f"User {user.email} logged in",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user = get_session_user(request, db)
    if user:
        write_audit(db, action="logout", user=user, detail=f"User {user.email} logged out")
        db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
