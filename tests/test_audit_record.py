from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
AUDIT_REPORT = ROOT_DIR / "AUDIT_REPORT.md"
REPAIR_MANIFEST = ROOT_DIR / "REPAIR_MANIFEST.md"


def test_audit_records_profile_pr_merge_as_verified_history():
    report = AUDIT_REPORT.read_text(encoding="utf-8")
    manifest = REPAIR_MANIFEST.read_text(encoding="utf-8")

    assert "5669c4d8cb510c47e0fac987be1b23cbac6e86ce" in report
    assert "5669c4d8cb510c47e0fac987be1b23cbac6e86ce" in manifest
    assert "PR #1 was verified merged" in report
    assert "PR #1 is **MERGED**, not open" in manifest


def test_audit_does_not_present_prior_external_snapshot_as_current():
    report = AUDIT_REPORT.read_text(encoding="utf-8")
    manifest = REPAIR_MANIFEST.read_text(encoding="utf-8")

    assert "six separate engineering repositories were not live-rechecked" in report
    assert "historical leads" in report
    assert "not live-rechecked here" in manifest
    assert "not treat them as current until verified" in manifest


def test_audit_identifies_the_session_fixed_branch():
    report = AUDIT_REPORT.read_text(encoding="utf-8")
    manifest = REPAIR_MANIFEST.read_text(encoding="utf-8")
    branch = "arena/be8b3b2e-hariszafar740-lang"

    assert branch in report
    assert branch in manifest
