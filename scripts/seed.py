"""Seed demo client, engagement, users, three vendors, and mocked findings."""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cryptography.fernet import Fernet

from app.auth.security import hash_password
from app.config import BASE_DIR, get_settings
from app.database import SessionLocal, init_db
from app.models.engagement import Client, Engagement, EngagementMembership
from app.models.enums import (
    AssetReviewStatus,
    AssetSource,
    AssetType,
    DataAccessLevel,
    EvidenceType,
    FindingSeverity,
    FindingStatus,
    ModuleName,
    Role,
    ScanAuthorization,
    ScanProfile,
    ScanStatus,
    VendorCriticality,
)
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.scan import ScanModuleRun, ScanRun
from app.models.user import User
from app.models.vendor import Asset, Vendor


def ensure_env() -> None:
    env_path = BASE_DIR / ".env"
    example = BASE_DIR / ".env.example"
    if not env_path.exists() and example.exists():
        text = example.read_text()
        if "generate-with-python-cryptography-fernet" in text:
            text = text.replace(
                "FERNET_KEY=generate-with-python-cryptography-fernet",
                f"FERNET_KEY={Fernet.generate_key().decode()}",
            )
        if "change-me-to-a-long-random-string" in text:
            text = text.replace(
                "SECRET_KEY=change-me-to-a-long-random-string",
                "SECRET_KEY=dev-secret-key-for-local-demo-only",
            )
        env_path.write_text(text)
        print(f"Wrote {env_path}")


def seed() -> None:
    ensure_env()
    get_settings.cache_clear()
    (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "data" / "files").mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "analyst@pwc.local").first():
            print("Seed data already present — skipping.")
            return

        analyst = User(
            email="analyst@pwc.local",
            full_name="Alex Analyst",
            password_hash=hash_password("ChangeMe123!"),
            role=Role.analyst,
        )
        lead = User(
            email="lead@pwc.local",
            full_name="Jordan Lead",
            password_hash=hash_password("ChangeMe123!"),
            role=Role.engagement_lead,
        )
        admin = User(
            email="admin@pwc.local",
            full_name="Sam Admin",
            password_hash=hash_password("ChangeMe123!"),
            role=Role.admin,
        )
        db.add_all([analyst, lead, admin])
        db.flush()

        client = Client(name="Acme Holdings Ltd")
        db.add(client)
        db.flush()

        engagement = Engagement(
            client_id=client.id,
            name="FY26 Third-Party Assurance",
            code="ACME-TPA-26",
            allowed_countries="GB,IE,DE,NL,US",
            notes="Demo engagement for local UI walkthrough.",
        )
        db.add(engagement)
        db.flush()

        for u in (analyst, lead):
            db.add(EngagementMembership(user_id=u.id, engagement_id=engagement.id))

        vendors_spec = [
            {
                "name": "CloudPay Solutions",
                "domain": "cloudpaysolutions.example",
                "criticality": VendorCriticality.critical,
                "data_access": DataAccessLevel.highly_confidential,
                "auth": ScanAuthorization.light_active,
                "approved": True,
                "score": Decimal("62.00"),
                "grade": "D",
                "assets": [
                    (AssetType.domain, "cloudpaysolutions.example", AssetSource.declared, 1.0, True),
                    (AssetType.subdomain, "api.cloudpaysolutions.example", AssetSource.declared, 1.0, True),
                    (AssetType.subdomain, "staging.cloudpaysolutions.example", AssetSource.discovered, 0.72, True),
                    (AssetType.url, "https://admin.cloudpaysolutions.example/login", AssetSource.discovered, 0.85, True),
                ],
                "findings": [
                    (
                        ModuleName.web_surface,
                        FindingSeverity.critical,
                        "Admin login panel exposed to the internet",
                        "admin.cloudpaysolutions.example",
                        0.92,
                    ),
                    (
                        ModuleName.tls,
                        FindingSeverity.high,
                        "TLS certificate expires within 14 days",
                        "api.cloudpaysolutions.example",
                        0.98,
                    ),
                    (
                        ModuleName.dns_email,
                        FindingSeverity.medium,
                        "DMARC policy is p=none",
                        "cloudpaysolutions.example",
                        0.95,
                    ),
                ],
                "evidence": [
                    (
                        EvidenceType.iso27001,
                        "ISO 27001 certificate",
                        "BSI",
                        date.today() - timedelta(days=400),
                        date.today() - timedelta(days=35),
                        True,
                    ),
                    (
                        EvidenceType.scan_authorization,
                        "Scan authorization letter",
                        "CloudPay Legal",
                        date.today() - timedelta(days=10),
                        date.today() + timedelta(days=355),
                        True,
                    ),
                ],
            },
            {
                "name": "Northwind Logistics",
                "domain": "northwindlogistics.example",
                "criticality": VendorCriticality.high,
                "data_access": DataAccessLevel.confidential,
                "auth": ScanAuthorization.passive_only,
                "approved": False,
                "score": Decimal("78.00"),
                "grade": "C",
                "assets": [
                    (AssetType.domain, "northwindlogistics.example", AssetSource.declared, 1.0, True),
                    (AssetType.subdomain, "portal.northwindlogistics.example", AssetSource.declared, 1.0, False),
                    (AssetType.ip, "203.0.113.44", AssetSource.declared, 1.0, True),
                ],
                "findings": [
                    (
                        ModuleName.lookalike_domains,
                        FindingSeverity.high,
                        "Registered lookalike domain with MX records",
                        "northwind-logistics.example",
                        0.88,
                    ),
                    (
                        ModuleName.leaks_darkweb,
                        FindingSeverity.medium,
                        "Vendor name referenced on ransomware leak tracker",
                        "northwindlogistics.example",
                        0.70,
                    ),
                ],
                "evidence": [
                    (
                        EvidenceType.soc2,
                        "SOC 2 Type II report",
                        "BigFour Audit LLP",
                        date.today() - timedelta(days=200),
                        date.today() + timedelta(days=40),
                        True,
                    ),
                    (
                        EvidenceType.pentest,
                        "External pentest report",
                        "RedTeam Co",
                        date.today() - timedelta(days=500),
                        None,
                        True,
                    ),
                ],
            },
            {
                "name": "BrightHR Analytics",
                "domain": "brighthr.example",
                "criticality": VendorCriticality.medium,
                "data_access": DataAccessLevel.limited,
                "auth": ScanAuthorization.passive_only,
                "approved": False,
                "score": Decimal("91.00"),
                "grade": "A",
                "assets": [
                    (AssetType.domain, "brighthr.example", AssetSource.declared, 1.0, True),
                    (AssetType.subdomain, "app.brighthr.example", AssetSource.declared, 1.0, True),
                    (AssetType.cloud, "brighthr-backups", AssetSource.declared, 1.0, None),
                ],
                "findings": [
                    (
                        ModuleName.reputation,
                        FindingSeverity.low,
                        "Domain on low-priority informational blocklist",
                        "brighthr.example",
                        0.60,
                    ),
                    (
                        ModuleName.claims_vs_reality,
                        FindingSeverity.info,
                        "Intake claims MFA everywhere — no contradictory evidence yet",
                        "brighthr.example",
                        0.50,
                    ),
                ],
                "evidence": [
                    (
                        EvidenceType.policy,
                        "Information security policy",
                        "BrightHR",
                        date.today() - timedelta(days=90),
                        date.today() + timedelta(days=275),
                        True,
                    ),
                ],
            },
        ]

        now = datetime.now(timezone.utc)
        for spec in vendors_spec:
            vendor = Vendor(
                engagement_id=engagement.id,
                name=spec["name"],
                primary_domain=spec["domain"],
                criticality=spec["criticality"],
                data_access=spec["data_access"],
                scan_authorization=spec["auth"],
                authorization_approved=spec["approved"],
                authorization_approved_by_id=lead.id if spec["approved"] else None,
                authorization_approved_at=now if spec["approved"] else None,
                score=spec["score"],
                grade=spec["grade"],
            )
            db.add(vendor)
            db.flush()

            for asset_type, value, source, conf, resolves in spec["assets"]:
                db.add(
                    Asset(
                        vendor_id=vendor.id,
                        asset_type=asset_type,
                        value=value,
                        source=source,
                        attribution_confidence=conf,
                        review_status=(
                            AssetReviewStatus.pending_review
                            if source == AssetSource.discovered and conf < 0.8
                            else AssetReviewStatus.accepted
                        ),
                        resolves=resolves,
                    )
                )

            for etype, title, issuer, issued, expires, in_scope in spec["evidence"]:
                db.add(
                    Evidence(
                        vendor_id=vendor.id,
                        evidence_type=etype,
                        title=title,
                        filename=f"{title.replace(' ', '_').lower()}.pdf",
                        stored_path=f"seed/{vendor.id}/{etype.value}.pdf",
                        content_type="application/pdf",
                        issuer=issuer,
                        scope="Corporate",
                        issue_date=issued,
                        expiry_date=expires,
                        in_scope=in_scope,
                        uploaded_by_id=analyst.id,
                    )
                )

            scan = ScanRun(
                vendor_id=vendor.id,
                profile=ScanProfile.standard,
                status=ScanStatus.done,
                triggered_by_id=analyst.id,
                started_at=now - timedelta(hours=2),
                finished_at=now - timedelta(hours=1),
            )
            db.add(scan)
            db.flush()

            for module in (
                ModuleName.asset_discovery,
                ModuleName.web_surface,
                ModuleName.tls,
                ModuleName.dns_email,
                ModuleName.lookalike_domains,
            ):
                db.add(
                    ScanModuleRun(
                        scan_run_id=scan.id,
                        module=module,
                        status=ScanStatus.done,
                        findings_count=0,
                        started_at=now - timedelta(hours=2),
                        finished_at=now - timedelta(hours=1, minutes=30),
                    )
                )

            for module, severity, title, asset, confidence in spec["findings"]:
                db.add(
                    Finding(
                        vendor_id=vendor.id,
                        scan_run_id=scan.id,
                        module=module,
                        title=title,
                        description=f"Mocked finding for demo UI — {title}.",
                        severity=severity,
                        status=FindingStatus.open,
                        confidence=Decimal(str(confidence)),
                        asset_value=asset,
                        evidence="Seeded evidence placeholder (no live scan).",
                        remediation="Remediate per engagement playbook.",
                    )
                )

        db.commit()
        print("Seed complete.")
        print("  Login: analyst@pwc.local / ChangeMe123!")
        print("  Lead:  lead@pwc.local / ChangeMe123!")
        print("  Open:  http://127.0.0.1:8000")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
