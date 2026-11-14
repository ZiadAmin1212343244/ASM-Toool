"""Shared enumerations for domain models."""

import enum


class Role(str, enum.Enum):
    analyst = "analyst"
    engagement_lead = "engagement_lead"
    admin = "admin"


class ScanAuthorization(str, enum.Enum):
    passive_only = "passive_only"
    light_active = "light_active"
    deep_active = "deep_active"


class VendorCriticality(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DataAccessLevel(str, enum.Enum):
    none = "none"
    limited = "limited"
    confidential = "confidential"
    highly_confidential = "highly_confidential"


class AssetSource(str, enum.Enum):
    declared = "declared"
    discovered = "discovered"


class AssetType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip = "ip"
    url = "url"
    cloud = "cloud"
    email = "email"


class AssetReviewStatus(str, enum.Enum):
    accepted = "accepted"
    pending_review = "pending_review"
    rejected = "rejected"


class EvidenceType(str, enum.Enum):
    iso27001 = "iso27001"
    soc2 = "soc2"
    pentest = "pentest"
    policy = "policy"
    scan_authorization = "scan_authorization"
    other = "other"


class ScanProfile(str, enum.Enum):
    quick = "quick"
    standard = "standard"
    custom = "custom"


class ScanStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"
    skipped = "skipped"


class FindingSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class FindingStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    risk_accepted = "risk_accepted"
    resolved = "resolved"
    false_positive = "false_positive"


class ModuleName(str, enum.Enum):
    asset_discovery = "asset_discovery"
    network_exposure = "network_exposure"
    web_surface = "web_surface"
    tls = "tls"
    dns_email = "dns_email"
    vuln_enrichment = "vuln_enrichment"
    cloud_exposure = "cloud_exposure"
    leaks_darkweb = "leaks_darkweb"
    code_leaks = "code_leaks"
    lookalike_domains = "lookalike_domains"
    reputation = "reputation"
    fourth_parties = "fourth_parties"
    claims_vs_reality = "claims_vs_reality"
