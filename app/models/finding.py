"""Findings and status history."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FindingSeverity, FindingStatus, ModuleName


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    scan_run_id: Mapped[int | None] = mapped_column(ForeignKey("scan_runs.id"), nullable=True, index=True)
    module: Mapped[ModuleName] = mapped_column(Enum(ModuleName))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity), default=FindingSeverity.info)
    status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus), default=FindingStatus.open)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.80"))
    asset_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vendor = relationship("Vendor", back_populates="findings")
    scan_run = relationship("ScanRun", back_populates="findings")
    status_history = relationship(
        "FindingStatusHistory", back_populates="finding", cascade="all, delete-orphan"
    )


class FindingStatusHistory(Base):
    __tablename__ = "finding_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    old_status: Mapped[FindingStatus | None] = mapped_column(Enum(FindingStatus), nullable=True)
    new_status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus))
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finding = relationship("Finding", back_populates="status_history")
