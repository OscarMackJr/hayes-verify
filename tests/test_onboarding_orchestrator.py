import json
from pathlib import Path

import pytest

from hayes_verify.onboarding_orchestrator import (
    AuthoritySource,
    inventory_tree,
    run_synthetic_pilot,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_AUTHORITY = ROOT / "tests" / "fixtures" / "onboarding_authority"


def fixture_authority() -> AuthoritySource:
    return AuthoritySource(
        FIXTURE_AUTHORITY,
        source_identity="TEST_FIXTURE_ONBOARDING_AUTHORITY",
        source_class="TEST_FIXTURE_NON_PRODUCTION",
    )


def test_synthetic_orchestrator_executes_existing_evaluator(tmp_path: Path):
    prior = ROOT / "generated/onboarding/runs/SYNTHETIC_ONBOARDING_INTEGRATION"
    before = inventory_tree(prior)
    result = run_synthetic_pilot(ROOT, tmp_path / "runs", prior, authority_source=fixture_authority())
    executed = json.loads((Path(result["run_dir"]) / "results/executed_results.json").read_text())
    orchestration = json.loads((Path(result["run_dir"]) / "orchestration_manifest.json").read_text())
    assert executed["actual_evaluator_invocation_count"] == 1
    assert executed["contract_valid_executed_result_count"] == 1
    assert executed["hand_supplied_machine_result_count"] == 0
    assert orchestration["authority_provenance"]["source_class"] == "TEST_FIXTURE_NON_PRODUCTION"
    assert "root" not in orchestration["authority_provenance"]
    assert result["certification"]["compliance_attestation"] is False
    assert inventory_tree(prior) == before


def test_missing_authority_fails_closed(tmp_path: Path):
    prior = ROOT / "generated/onboarding/runs/SYNTHETIC_ONBOARDING_INTEGRATION"
    with pytest.raises(ValueError, match="explicit published authority source is required"):
        run_synthetic_pilot(ROOT, tmp_path / "runs", prior)


def test_explicit_test_fixture_authority_succeeds(tmp_path: Path):
    prior = ROOT / "generated/onboarding/runs/SYNTHETIC_ONBOARDING_INTEGRATION"
    result = run_synthetic_pilot(ROOT, tmp_path / "runs", prior, authority_source=fixture_authority())
    assert Path(result["run_dir"]).is_dir()


def test_linux_compatible_authority_resolution(tmp_path: Path):
    copied = tmp_path / "authority"
    copied.mkdir()
    for path in FIXTURE_AUTHORITY.iterdir():
        (copied / path.name).write_bytes(path.read_bytes())
    requirements, certification, provenance = AuthoritySource(
        copied, "TEST_FIXTURE_LINUX_PATH", "TEST_FIXTURE_NON_PRODUCTION"
    ).load_test_quality()
    assert requirements.parent == copied
    assert certification.parent == copied
    assert provenance["source_identity"] == "TEST_FIXTURE_LINUX_PATH"


def test_authority_provenance_retained():
    _, _, provenance = fixture_authority().load_test_quality()
    assert provenance["source_identity"] == "TEST_FIXTURE_ONBOARDING_AUTHORITY"
    assert provenance["requirements_sha256"]
    assert provenance["certification_sha256"]


def test_fixture_authority_cannot_be_mistaken_for_published_ems():
    with pytest.raises(ValueError, match="cannot be used as published EMS authority"):
        AuthoritySource(FIXTURE_AUTHORITY, "MISLABELED_FIXTURE", "PUBLISHED_EMS").load_test_quality()


def test_unsupported_authority_source_class_fails_closed():
    with pytest.raises(ValueError, match="source class is unsupported"):
        AuthoritySource(FIXTURE_AUTHORITY, "UNSUPPORTED", "AUTODETECTED").load_test_quality()


def test_malformed_authority_fails_closed(tmp_path: Path):
    (tmp_path / "test_quality_control_requirements.json").write_text("not-json", encoding="utf-8")
    (tmp_path / "test_quality_publication_certification.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        AuthoritySource(tmp_path, "MALFORMED", "PUBLISHED_EMS").load_test_quality()


def test_no_hard_coded_windows_authority_path():
    source = (ROOT / "src/hayes_verify/onboarding_orchestrator.py").read_text(encoding="utf-8")
    assert "C:/temp" not in source
    assert "C:\\temp" not in source
    assert "standars\\ems" not in source
