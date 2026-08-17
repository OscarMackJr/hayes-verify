from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import ValidationError

from hayes_verify.contracts import ContractBundle
from hayes_verify.wave2d_targets import normalize_result_authority, validate_target

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "ARCHIVE-6C59EC6CEEFD583546BE3E47"
SHA = "6c59ec6ceefd583546be3e47c5c0500f23f54c686a476c6e913bc208cbb1704d"


def request(target_type: str, target_id: str) -> dict:
    value = {"contract_version": "1.0", "wave": "2D", "request_id": "AR3B-TEST", "control_id": "EMS-CTRL-025", "target_id": target_id, "applicability_state": "APPLICABLE", "requested_at_utc": "2026-08-16T00:00:00Z", "target_type": target_type, "evaluation_role": "AUTHORITATIVE_EVALUATION"}
    if target_type == "ARCHIVED_REPOSITORY_SNAPSHOT":
        value.update({"archive_source_sha256": SHA, "archive_evidence_source_class": "ARCHIVE_REPOSITORY_CONTENT"})
    return value


def test_existing_request_target_types_remain_valid() -> None:
    bundle = ContractBundle(ROOT)
    bundle.validate_request(request("REPOSITORY", "REPO-001"))
    bundle.validate_request(request("ORGANIZATION", "ORG-001"))


def test_archive_request_is_truthful_and_contract_valid(tmp_path: Path) -> None:
    bundle = ContractBundle(ROOT)
    value = request("ARCHIVED_REPOSITORY_SNAPSHOT", ARCHIVE)
    bundle.validate_request(value)
    validate_target({"target_id": ARCHIVE, "target_type": "ARCHIVED_REPOSITORY_SNAPSHOT", "evaluation_role": "AUTHORITATIVE_EVALUATION", "repository_path": str(tmp_path), "archive_source_sha256": SHA})


def test_archive_identifier_cannot_be_repository_target() -> None:
    bundle = ContractBundle(ROOT)
    with pytest.raises(ValidationError):
        bundle.validate_request(request("REPOSITORY", ARCHIVE))


def test_archive_result_round_trip_preserves_source_lineage() -> None:
    bundle = ContractBundle(ROOT)
    value = {"contract_version": "1.0", "wave": "2D", "request_id": "AR3B-TEST", "control_id": "EMS-CTRL-025", "target_id": ARCHIVE, "evaluation_state": "COMPLETE", "evidence_state": "SUFFICIENT", "result_state": "WARNING", "evaluated_at_utc": "2026-08-16T00:00:00Z", "evidence_ids": [], "rationale": "Archive test result.", "promotion_state": "NOT_PROMOTED"}
    normalize_result_authority(request("ARCHIVED_REPOSITORY_SNAPSHOT", ARCHIVE), value)
    bundle.validate_result(value)
    assert value["archive_source_sha256"] == SHA


def test_archive_target_does_not_require_git_metadata(tmp_path: Path) -> None:
    validate_target({"target_id": ARCHIVE, "target_type": "ARCHIVED_REPOSITORY_SNAPSHOT", "evaluation_role": "AUTHORITATIVE_EVALUATION", "repository_path": str(tmp_path), "archive_source_sha256": SHA})
