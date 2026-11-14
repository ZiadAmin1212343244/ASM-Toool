"""Vendor list and detail pages."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import require_engagement, require_user, user_engagements
from app.config import BASE_DIR, get_settings
from app.database import get_db
from app.models.enums import (
    AssetSource,
    AssetType,
    DataAccessLevel,
    FindingStatus,
    ScanAuthorization,
    VendorCriticality,
)
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.models.user import User
from app.models.vendor import Asset, Vendor
from app.models.evidence import Evidence
from app.models.scan import ScanRun
from app.models.audit import AuditLog
from app.services.audit import write_audit

router = APIRouter(prefix="/vendors", tags=["vendors"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _base_ctx(request: Request, db: Session, user: User, engagement: Engagement) -> dict:
    settings = get_settings()
    return {
        "request": request,
        "app_name": settings.app_name,
        "user": user,
        "engagements": user_engagements(db, user),
        "current_engagement": engagement,
        "active_nav": "vendors",
        "ScanAuthorization": ScanAuthorization,
        "VendorCriticality": VendorCriticality,
        "DataAccessLevel": DataAccessLevel,
        "today": date.today(),
        "soon": date.today() + timedelta(days=60),
    }


@router.get("", response_class=HTMLResponse)
def vendor_list(
    request: Request,
    q: str | None = Query(None),
    grade: str | None = Query(None),
    criticality: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    engagement: Engagement = Depends(require_engagement),
):
    ctx = _base_ctx(request, db, user, engagement)
    query = db.query(Vendor).filter(
        Vendor.engagement_id == engagement.id, Vendor.is_active.is_(True)
    )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(Vendor.name.ilike(like) | Vendor.primary_domain.ilike(like))
    if grade:
        query = query.filter(Vendor.grade == grade.upper())
    if criticality:
        query = query.filter(Vendor.criticality == VendorCriticality(criticality))
    vendors = query.order_by(Vendor.name).all()
    ctx.update({"vendors": vendors, "q": q or "", "grade": grade or "", "criticality": criticality or ""})
    return templates.TemplateResponse("vendors/list.html", ctx)


@router.get("/new", response_class=HTMLResponse)
def vendor_new_form(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    engagement: Engagement = Depends(require_engagement),
):
    ctx = _base_ctx(request, db, user, engagement)
    ctx["vendor"] = None
    return templates.TemplateResponse("vendors/form.html", ctx)


@router.post("/new")
def vendor_create(
    request: Request,
    name: str = Form(...),
    primary_domain: str = Form(""),
    criticality: str = Form("medium"),
    data_access: str = Form("limited"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    engagement: Engagement = Depends(require_engagement),
):
    vendor = Vendor(
        engagement_id=engagement.id,
        name=name.strip(),
        primary_domain=primary_domain.strip() or None,
        criticality=VendorCriticality(criticality),
        data_access=DataAccessLevel(data_access),
        notes=notes.strip() or None,
        scan_authorization=ScanAuthorization.passive_only,
    )
    db.add(vendor)
    db.flush()
    if vendor.primary_domain:
        db.add(
            Asset(
                vendor_id=vendor.id,
                asset_type=AssetType.domain,
                value=vendor.primary_domain.lower(),
                source=AssetSource.declared,
                attribution_confidence=1.0,
            )
        )
    write_audit(
        db,
        action="create_vendor",
        user=user,
        entity_type="vendor",
        entity_id=vendor.id,
        detail=f"Created vendor {vendor.name}",
    )
    db.commit()
    return RedirectResponse(f"/vendors/{vendor.id}", status_code=303)


@router.get("/{vendor_id}", response_class=HTMLResponse)
def vendor_detail(
    vendor_id: int,
    request: Request,
    tab: str = Query("overview"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    engagement: Engagement = Depends(require_engagement),
):
    vendor = (
        db.query(Vendor)
        .options(
            joinedload(Vendor.assets),
            joinedload(Vendor.findings),
            joinedload(Vendor.evidence),
            joinedload(Vendor.scan_runs),
        )
        .filter(Vendor.id == vendor_id, Vendor.engagement_id == engagement.id)
        .first()
    )
    if not vendor:
        return RedirectResponse("/vendors", status_code=303)

    ctx = _base_ctx(request, db, user, engagement)
    declared = [a for a in vendor.assets if a.source == AssetSource.declared]
    discovered = [a for a in vendor.assets if a.source == AssetSource.discovered]
    open_findings = [f for f in vendor.findings if f.status == FindingStatus.open]
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    open_findings.sort(key=lambda f: (severity_order.get(f.severity.value, 9), f.title))

    audit_entries = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "vendor", AuditLog.entity_id == str(vendor.id))
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    scan_runs = sorted(vendor.scan_runs, key=lambda s: s.created_at, reverse=True)

    ctx.update(
        {
            "vendor": vendor,
            "tab": tab,
            "declared_assets": declared,
            "discovered_assets": discovered,
            "open_findings": open_findings,
            "all_findings": sorted(
                vendor.findings, key=lambda f: severity_order.get(f.severity.value, 9)
            ),
            "evidence_list": sorted(
                vendor.evidence, key=lambda e: e.expiry_date or date.max, reverse=True
            ),
            "scan_runs": scan_runs,
            "audit_entries": audit_entries,
            "active_nav": "vendors",
        }
    )
    return templates.TemplateResponse("vendors/detail.html", ctx)
