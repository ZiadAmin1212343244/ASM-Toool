"""Central policy guard: authorization level before any vendor-targeted traffic."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from app.models.enums import ModuleName, ScanAuthorization

# Minimum authorization required for each module to send traffic / probe assets.
# Passive modules may run under passive_only. Light-active modules need light_active+.
MODULE_REQUIREMENTS: dict[ModuleName, ScanAuthorization] = {
    ModuleName.asset_discovery: ScanAuthorization.passive_only,
    ModuleName.leaks_darkweb: ScanAuthorization.passive_only,
    ModuleName.code_leaks: ScanAuthorization.passive_only,
    ModuleName.lookalike_domains: ScanAuthorization.passive_only,
    ModuleName.reputation: ScanAuthorization.passive_only,
    ModuleName.fourth_parties: ScanAuthorization.passive_only,
    ModuleName.claims_vs_reality: ScanAuthorization.passive_only,
    ModuleName.vuln_enrichment: ScanAuthorization.passive_only,
    ModuleName.dns_email: ScanAuthorization.light_active,
    ModuleName.tls: ScanAuthorization.light_active,
    ModuleName.web_surface: ScanAuthorization.light_active,
    ModuleName.network_exposure: ScanAuthorization.light_active,
    ModuleName.cloud_exposure: ScanAuthorization.light_active,
}

_AUTH_RANK = {
    ScanAuthorization.passive_only: 0,
    ScanAuthorization.light_active: 1,
    ScanAuthorization.deep_active: 2,
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""

    @property
    def skip_label(self) -> str | None:
        if self.allowed:
            return None
        return f"skipped – {self.reason}"


def check_module_authorization(
    vendor_authorization: ScanAuthorization,
    module: ModuleName,
    *,
    authorization_approved: bool = True,
) -> PolicyDecision:
    """
    One central guard called before any module sends traffic to a vendor asset.

    Rules:
    - Vendor authorization must meet or exceed the module requirement.
    - Raising above passive_only requires an approved authorization letter
      (authorization_approved=True). If not approved, treat as passive_only.
    - Unknown modules are denied.
    """
    effective = vendor_authorization
    if (
        vendor_authorization != ScanAuthorization.passive_only
        and not authorization_approved
    ):
        effective = ScanAuthorization.passive_only

    required = MODULE_REQUIREMENTS.get(module)
    if required is None:
        return PolicyDecision(False, "not authorized")

    if _AUTH_RANK[effective] < _AUTH_RANK[required]:
        return PolicyDecision(False, "not authorized")

    return PolicyDecision(True)


def is_private_or_reserved_ip(value: str) -> bool:
    """Return True if value is a private, loopback, link-local, or reserved IP."""
    try:
        addr = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def is_safe_scan_target(value: str) -> bool:
    """Reject private/reserved IPs; hostnames are allowed (resolved later)."""
    try:
        ipaddress.ip_address(value.strip())
    except ValueError:
        return True  # hostname / domain
    return not is_private_or_reserved_ip(value)
