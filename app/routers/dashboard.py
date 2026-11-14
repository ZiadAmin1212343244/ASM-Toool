"""Engagement dashboard and engagement switcher."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import require_user, user_engagements
from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models.enums import FindingSeverity, FindingStatus
from app.models.finding import Finding
from app.models.user import User
from app.models.vendor import Vendor
from app.services.audit import write_audit

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _base_ctx(request: Request, db: Session, user: User) -> dict:
    settings = get_settings()
    engagements = user_engagements(db, user)
    engagement_id = request.session.get("engagement_id")
    current = next((e for e in engagements if e.id == engagement_id), None)
    if current is None and engagements:
        current = engagements[0]
        request.session["engagement_id"] = current.id
    return {
        "request": request,
        "app_name": settings.app_name,
        "user": user,
        "engagements": engagements,
        "current_engagement": current,
        "active_nav": "dashboard",
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    ctx = _base_ctx(request, db, user)
    engagement = ctx["current_engagement"]
    vendors: list[Vendor] = []
    grade_counts: Counter = Counter()
    top_findings: list[Finding] = []
    open_critical = 0

    if engagement:
        vendors = (
            db.query(Vendor)
            .filter(Vendor.engagement_id == engagement.id, Vendor.is_active.is_(True))
            .order_by(Vendor.name)
            .all()
        )
        for v in vendors:
            grade_counts[v.grade or "N/A"] += 1

        top_findings = (
            db.query(Finding)
            .join(Vendor)
            .options(joinedload(Finding.vendor))
            .filter(
                Vendor.engagement_id == engagement.id,
                Finding.status == FindingStatus.open,
                Finding.severity.in_([FindingSeverity.critical, FindingSeverity.high]),
            )
            .order_by(Finding.severity, Finding.first_seen_at.desc())
            .limit(10)
            .all()
        )
        open_critical = (
            db.query(Finding)
            .join(Vendor)
            .filter(
                Vendor.engagement_id == engagement.id,
                Finding.status == FindingStatus.open,
                Finding.severity == FindingSeverity.critical,
            )
            .count()
        )

    ctx.update(
        {
            "vendors": vendors,
            "grade_counts": dict(grade_counts),
            "top_findings": top_findings,
            "open_critical": open_critical,
            "vendor_count": len(vendors),
        }
    )
    return templates.TemplateResponse("dashboard/index.html", ctx)


@router.post("/engagement/switch")
def switch_engagement(
    request: Request,
    engagement_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    allowed = {e.id for e in user_engagements(db, user)}
    if engagement_id not in allowed:
        return RedirectResponse("/", status_code=303)
    request.session["engagement_id"] = engagement_id
    write_audit(
        db,
        action="switch_engagement",
        user=user,
        entity_type="engagement",
        entity_id=engagement_id,
    )
    db.commit()
    return RedirectResponse("/", status_code=303)
