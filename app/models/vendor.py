"""Vendors and assets."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    AssetReviewStatus,
    AssetSource,
    AssetType,
    DataAccessLevel,
    ScanAuthorization,
    VendorCriticality,
)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    primary_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[VendorCriticality] = mapped_column(
        Enum(VendorCriticality), default=VendorCriticality.medium
    )
    data_access: Mapped[DataAccessLevel] = mapped_column(
        Enum(DataAccessLevel), default=DataAccessLevel.limited
    )
    scan_authorization: Mapped[ScanAuthorization] = mapped_column(
        Enum(ScanAuthorization), default=ScanAuthorization.passive_only
    )
    authorization_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    authorization_approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    authorization_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engagement = relationship("Engagement", back_populates="vendors")
    assets = relationship("Asset", back_populates="vendor", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="vendor", cascade="all, delete-orphan")
    scan_runs = relationship("ScanRun", back_populates="vendor", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="vendor", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType))
    value: Mapped[str] = mapped_column(String(512), index=True)
    source: Mapped[AssetSource] = mapped_column(Enum(AssetSource), default=AssetSource.declared)
    attribution_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    review_status: Mapped[AssetReviewStatus] = mapped_column(
        Enum(AssetReviewStatus), default=AssetReviewStatus.accepted
    )
    resolves: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("Vendor", back_populates="assets")
