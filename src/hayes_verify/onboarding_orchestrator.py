"""Synthetic-only WS1--WS10 orchestration seam.

This module composes established workstream APIs; it neither allocates
identities nor interprets EMS policy or evaluator business logic.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hayes_verify.contracts import ContractBundle
from hayes_verify.evaluator_families.test_quality import run as run_test_quality
from hayes_verify.onboarding_applicability import compile_effective_applicability
from hayes_verify.onboarding_bundle import finalize_existing_bundle
from hayes_verify.onboarding_checkout import gate_requests, verify_checkout
from hayes_verify.onboarding_classification import classification_snapshot
from hayes_verify.onboarding_execution import compose_requests
from hayes_verify.onboarding_identity import RepositoryIdentity, repository_snapshot
from hayes_verify.onboarding_plan import create_frozen_assessment_plan
from hayes_verify.onboarding_reassessment import classify_changes
from hayes_verify.onboarding_review import build_queue, derive_current_state
from hayes_verify.onboarding_summary import summarize

FREEZE_SHA256 = "79adb6c003e9a61e2fd36131b1a37d3387973f72d206102985a78a3271bc5b35"

class FailClosedException(RuntimeError):
    """Raised when onboarding input or evaluator output is not safe to consume."""


def assert_non_production_pilot_boundary(
    repository_id: str, *, pilot_execution_authorized: bool, production_authorized: bool
) -> None:
    """Stop REPO-003 before WS1 unless its non-production pilot gate is explicit."""
    if repository_id == "REPO-003" and not pilot_execution_authorized:
        raise FailClosedException("FAIL_CLOSED_EXCEPTION: REPO-003 pilot execution is not authorized")
    if repository_id == "REPO-003" and production_authorized:
        raise FailClosedException("FAIL_CLOSED_EXCEPTION: REPO-003 non-production pilot cannot enable production")


def _validate_executed_result(bundle: ContractBundle, result: dict[str, Any]) -> None:
    """Reject malformed and unknown evaluator dispositions before WS7 consumes them."""
    if result.get("result_state") not in {"PASS", "FAIL", "WARNING"}:
        raise FailClosedException("FAIL_CLOSED_EXCEPTION: evaluator result has an unknown disposition")
    try:
        _validate_executed_result(bundle, result)
    except Exception as exc:
        raise FailClosedException("FAIL_CLOSED_EXCEPTION: evaluator result violates the result contract") from exc



@dataclass(frozen=True)
class AuthoritySource:
    """Explicit, location-agnostic input for published EMS authority.

    ``root`` is an execution input only. It is never persisted in an
    onboarding artifact; provenance records the caller-supplied identity and
    hashes of consumed authority documents instead.
    """

    root: Path
    source_identity: str
    source_class: str = "PUBLISHED_EMS"

    def load_test_quality(self) -> tuple[Path, Path, dict[str, Any]]:
        if self.source_class not in {"PUBLISHED_EMS", "TEST_FIXTURE_NON_PRODUCTION"}:
            raise ValueError("authority source class is unsupported")
        root = Path(self.root)
        requirements = root / "test_quality_control_requirements.json"
        certification = root / "test_quality_publication_certification.json"
        if not self.source_identity or not requirements.is_file() or not certification.is_file():
            raise ValueError("required published authority is unavailable")
        try:
            requirements_value = json.loads(requirements.read_text(encoding="utf-8-sig"))
            certification_value = json.loads(certification.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("required published authority is malformed") from exc
        fixture_markers = (
            requirements_value.get("authority_source_type") == "TEST_FIXTURE",
            certification_value.get("authority_source_type") == "TEST_FIXTURE",
        )
        if any(fixture_markers) and self.source_class != "TEST_FIXTURE_NON_PRODUCTION":
            raise ValueError("test fixture authority cannot be used as published EMS authority")
        if self.source_class == "TEST_FIXTURE_NON_PRODUCTION" and not all(fixture_markers):
            raise ValueError("test fixture authority must be explicitly labeled")
        return requirements, certification, {
            "source_identity": self.source_identity,
            "source_class": self.source_class,
            "requirements_sha256": _sha_bytes(requirements.read_bytes()),
            "certification_sha256": _sha_bytes(certification.read_bytes()),
        }


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def inventory_tree(root: Path) -> dict[str, dict[str, Any]]:
    return {p.relative_to(root).as_posix(): {"sha256": _sha_bytes(p.read_bytes()), "size": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file()}


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def run_synthetic_pilot(
    root: Path,
    output_root: Path,
    prior_run: Path,
    *,
    authority_source: AuthoritySource | None = None,
    run_id: str = "SYNTHETIC_ONBOARDING_ORCHESTRATED",
    pilot: bool = False,
) -> dict[str, Any]:
    """Create one new synthetic-only lineage and execute an existing evaluator."""
    root, output_root, prior_run = Path(root), Path(output_root), Path(prior_run)
    prior_inventory = inventory_tree(prior_run)
    run_dir = output_root / run_id
    if run_dir.exists():
        raise ValueError("synthetic run id already exists; historical runs are immutable")
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if authority_source is None:
        raise ValueError("explicit published authority source is required")
    _requirements, _certification, authority_provenance = authority_source.load_test_quality()
    registry_path = root / "registry" / "wave2d_evaluator_registry_v1_10.json"
    if not registry_path.is_file():
        raise ValueError("required published authority is unavailable")
    identity = RepositoryIdentity("REPO-9001", "hayes-synthetic-pilot", "synthetic", "github.com", "https://github.com/synthetic/hayes-synthetic-pilot", "ACTIVE", None)
    assert_non_production_pilot_boundary(identity.repository_id, pilot_execution_authorized=True, production_authorized=False)
    ws1 = repository_snapshot(identity, captured_at=now, authority_reference="SYNTHETIC_TEST_IDENTITY_ONLY", authority_sha256=_sha_bytes(b"synthetic-test-identity"))
    # WS4 established binding uses sorted JSON with default separators.
    ws1_sha = _sha_bytes(json.dumps(ws1, sort_keys=True).encode())
    attrs = {name: {"state": "KNOWN_TRUE" if name == "production" else "KNOWN_FALSE", "value": name == "production", "source": {"source_type": "SYNTHETIC_TEST_AUTHORITY", "source_reference": "synthetic-fixture", "observation_timestamp": now}, "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "SYNTHETIC_TEST_ACTOR", "confirmed_at": now} for name in ("production", "internet_exposed", "contains_customer_data", "ai_enabled")}
    attrs.update({name: {"state": "KNOWN", "value": "SYNTHETIC", "source": {"source_type": "SYNTHETIC_TEST_AUTHORITY", "source_reference": "synthetic-fixture", "observation_timestamp": now}, "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "SYNTHETIC_TEST_ACTOR", "confirmed_at": now} for name in ("owner", "tier", "service_criticality", "data_classification")})
    ws2 = classification_snapshot(ws1, ws1_sha, attrs, captured_at=now, authority_reference="SYNTHETIC_TEST_CLASSIFICATION_ONLY", authority_sha256=_sha_bytes(b"synthetic-test-classification"), repository_snapshot_schema=str(root / "schemas" / "repository_snapshot.schema.json"))
    ws2_sha = _sha_json(ws2)
    policy = {"policy_reference": "SYNTHETIC_TEST_POLICY_NOT_EMS", "policy_sha256": _sha_bytes(b"synthetic-policy"), "controls": [{"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": [{"attribute": "production", "equals": True}]}, {"control_id": "EMS-CTRL-016", "scope": "REPOSITORY", "conditions": [{"attribute": "production", "equals": True}]}]}
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    ws3 = compile_effective_applicability(ws1, ws2, repository_snapshot_sha256=ws1_sha, classification_snapshot_sha256=ws2_sha, repository_snapshot_schema=str(root / "schemas" / "repository_snapshot.schema.json"), classification_snapshot_schema=str(root / "schemas" / "classification_snapshot.schema.json"), current_policy=policy, condition_evidence=[], captured_at=now, ems_authority_reference="SYNTHETIC_TEST_POLICY_NOT_EMS", ems_authority_sha256=policy["policy_sha256"], hayes_registry={"EMS-CTRL-025": "IMPLEMENTED", "EMS-CTRL-016": "PLANNED_AUTOMATED"}, historical_freeze_reference={"sha256": FREEZE_SHA256})
    ws3_sha = _sha_json(ws3)
    authorities = {"requirements": {"reference": authority_provenance["source_identity"] + ":test_quality_requirements", "sha256": authority_provenance["requirements_sha256"]}, "certification": {"reference": authority_provenance["source_identity"] + ":test_quality_certification", "sha256": authority_provenance["certification_sha256"]}}
    plan = create_frozen_assessment_plan(ws1, ws2, ws3, snapshot_references={"repository_snapshot": {"reference": "repository_snapshot", "sha256": ws1_sha}, "classification_snapshot": {"reference": "classification_snapshot", "sha256": ws2_sha}, "effective_applicability_snapshot": {"reference": "applicability_snapshot", "sha256": ws3_sha}}, ems_authorities=authorities, registry=registry, registry_reference="registry/wave2d_evaluator_registry_v1_10.json", registry_sha256=_sha_bytes(registry_path.read_bytes()), created_at=now, frozen_at=now)
    hashes = {"repository_snapshot": ws1_sha, "classification_snapshot": ws2_sha, "effective_applicability_snapshot": ws3_sha, "ems:requirements": authorities["requirements"]["sha256"], "ems:certification": authorities["certification"]["sha256"], "hayes_registry": plan["hayes"]["registry_sha256"]}
    composed = compose_requests(plan, current_hashes=hashes, evidence_candidates=[{"control_id": "EMS-CTRL-025", "authority_type": "REPOSITORY", "availability_state": "AVAILABLE", "freshness_state": "CURRENT", "observed_value": {"synthetic": True}, "source_reference": "synthetic-ci-evidence"}], requested_at_utc=now)
    if len(composed["requests"]) != 1:
        raise ValueError("synthetic WS5 did not compose one request")
    with tempfile.TemporaryDirectory(prefix="hayes-synthetic-") as td:
        checkout = Path(td) / "checkout"; (checkout / "tests").mkdir(parents=True); (checkout / "tests" / "test_smoke.py").write_text("def test_synthetic(): assert True\n", encoding="utf-8")
        _git(checkout, "init"); _git(checkout, "config", "user.email", "synthetic@example.invalid"); _git(checkout, "config", "user.name", "Synthetic"); _git(checkout, "remote", "add", "origin", "https://github.com/synthetic/hayes-synthetic-pilot.git"); _git(checkout, "add", "."); _git(checkout, "commit", "-m", "synthetic fixture")
        checkout_verification = verify_checkout(plan, composed["manifest"], {"REPO-9001": str(checkout)}, ws1, dirty_allowed=False)
        readiness = gate_requests(composed["manifest"], checkout_verification)
        if not checkout_verification["request_execution_permitted"] or readiness["execution_ready_request_count"] != 1:
            raise ValueError("synthetic checkout is not execution ready")
        bundle = ContractBundle(root)
        evidence, result = run_test_quality(bundle, composed["requests"][0], checkout, "synthetic/hayes-synthetic-pilot")
    bundle.validate_result(result)
    run_dir.mkdir(parents=True)
    for name, value in (("repository_snapshot.json", ws1), ("classification_snapshot.json", ws2), ("applicability_snapshot.json", ws3), ("assessment_plan.json", plan), ("evidence/evidence_resolution.json", {"resolutions": composed["evidence_resolutions"]}), ("requests/request_composition_manifest.json", composed["manifest"]), ("requests/requests.json", composed["requests"]), ("checkout/checkout_verification.json", checkout_verification), ("checkout/execution_readiness_manifest.json", readiness)):
        _write(run_dir / name, value)
    executed = {"synthetic": True, "actual_evaluator_invocation_count": 1, "contract_valid_executed_result_count": 1, "hand_supplied_machine_result_count": 0, "results": [result], "evidence_ids": [x["evidence_id"] for x in evidence]}
    _write(run_dir / "results/executed_results.json", executed)
    _write(run_dir / "orchestration_manifest.json", {"execution_mode": "SYNTHETIC_PILOT", "authority_provenance": authority_provenance, "actual_evaluator_invocation_count": 1, "contract_valid_executed_result_count": 1, "hand_supplied_machine_result_count": 0})
    queue = build_queue(plan, composed["manifest"], readiness, source_hashes={"manifest": _sha_json(composed["manifest"])})
    review_states = derive_current_state(queue, [])
    _write(run_dir / "human_review/queue.json", queue); _write(run_dir / "human_review/decisions/events.json", [])
    summary = summarize(plan, composed["manifest"], readiness, review_states, {"EMS-CTRL-025": result["result_state"]})
    _write(run_dir / "assessment_summary.json", summary)
    _write(run_dir / "run_metadata.json", {"run_id": run_id, "synthetic": True, "production_evidence": False, "pilot": pilot, "compliance_attestation": False, "real_repository": False, "execution_mode": "SYNTHETIC_PILOT", "actual_evaluator_invocation_count": 1, "hand_supplied_machine_result_count": 0, "historical_freeze_sha256": FREEZE_SHA256})
    manifest, cert = finalize_existing_bundle(run_dir, plan, ws1["repository_id"])
    no_change = classify_changes([{ "category": "LOCAL_EXECUTION_CONFIGURATION", "detail": "synthetic execution checkout", "ambiguous": False }])
    if inventory_tree(prior_run) != prior_inventory:
        raise RuntimeError("prior certified synthetic run changed")
    return {"run_dir": str(run_dir), "manifest": manifest, "certification": cert, "summary": summary, "ws10_read_only": no_change, "prior_inventory_unchanged": True}
