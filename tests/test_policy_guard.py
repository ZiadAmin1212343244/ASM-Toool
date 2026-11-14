"""Unit tests for the central scan authorization policy guard."""

import pytest

from app.models.enums import ModuleName, ScanAuthorization
from app.policy.guard import (
    check_module_authorization,
    is_private_or_reserved_ip,
    is_safe_scan_target,
)


@pytest.mark.parametrize(
    "auth,module,approved,allowed",
    [
        (ScanAuthorization.passive_only, ModuleName.asset_discovery, True, True),
        (ScanAuthorization.passive_only, ModuleName.leaks_darkweb, True, True),
        (ScanAuthorization.passive_only, ModuleName.web_surface, True, False),
        (ScanAuthorization.passive_only, ModuleName.network_exposure, True, False),
        (ScanAuthorization.light_active, ModuleName.web_surface, True, True),
        (ScanAuthorization.light_active, ModuleName.tls, True, True),
        (ScanAuthorization.light_active, ModuleName.asset_discovery, True, True),
        (ScanAuthorization.deep_active, ModuleName.network_exposure, True, True),
        # Raised auth without approved letter is treated as passive_only
        (ScanAuthorization.light_active, ModuleName.web_surface, False, False),
        (ScanAuthorization.light_active, ModuleName.asset_discovery, False, True),
        (ScanAuthorization.deep_active, ModuleName.tls, False, False),
    ],
)
def test_check_module_authorization(auth, module, approved, allowed):
    decision = check_module_authorization(auth, module, authorization_approved=approved)
    assert decision.allowed is allowed
    if not allowed:
        assert decision.skip_label == "skipped – not authorized"
        assert "not authorized" in decision.reason


def test_passive_modules_always_ok_when_passive():
    for module in (
        ModuleName.asset_discovery,
        ModuleName.leaks_darkweb,
        ModuleName.code_leaks,
        ModuleName.lookalike_domains,
        ModuleName.reputation,
        ModuleName.fourth_parties,
        ModuleName.claims_vs_reality,
        ModuleName.vuln_enrichment,
    ):
        d = check_module_authorization(ScanAuthorization.passive_only, module)
        assert d.allowed is True


def test_light_active_modules_need_light():
    for module in (
        ModuleName.dns_email,
        ModuleName.tls,
        ModuleName.web_surface,
        ModuleName.network_exposure,
        ModuleName.cloud_exposure,
    ):
        denied = check_module_authorization(ScanAuthorization.passive_only, module)
        allowed = check_module_authorization(ScanAuthorization.light_active, module)
        assert denied.allowed is False
        assert allowed.allowed is True


@pytest.mark.parametrize(
    "ip,expected",
    [
        ("10.0.0.1", True),
        ("192.168.1.10", True),
        ("127.0.0.1", True),
        ("169.254.1.1", True),
        ("8.8.8.8", False),
        ("203.0.113.44", False),  # TEST-NET-3 is reserved in some stacks; check carefully
    ],
)
def test_private_ip_detection(ip, expected):
    # 203.0.113.0/24 is documentation range — treated as reserved by ipaddress
    if ip.startswith("203.0.113."):
        assert is_private_or_reserved_ip(ip) is True
        return
    assert is_private_or_reserved_ip(ip) is expected


def test_safe_scan_target_allows_hostnames():
    assert is_safe_scan_target("vendor.example") is True
    assert is_safe_scan_target("10.1.2.3") is False
    assert is_safe_scan_target("1.1.1.1") is True
