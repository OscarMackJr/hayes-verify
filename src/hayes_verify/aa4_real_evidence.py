"""AA4 D5 evidence-record construction with no network or persistence capability."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

AA4_TARGET = {
    "repository_registry_identity": "REPO-001",
    "repository_identity": "OscarMackJr/bluto",
    "immutable_repository_revision": "7d3e12a2f7804041efd2840268f4d3d46f4266f9",
    "scope": "CONTROLLED_NON_PRODUCTION",
}
COLLECTOR_IDENTITY = "hayes-aa4-real-evidence-collector"
COLLECTOR_VERSION = "1.0.0-proposed"


class AA4EvidenceContractError(ValueError):
    """Reject an invalid static candidate before any collection is possible."""


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_published_contract(root: Path) -> dict[str, Any]:
    authority = json.loads((root / "contracts/authorities/aa4/ems_aa4_real_evidence_acquisition_contract_1.0.0.json").read_text(encoding="utf-8"))
    candidate = json.loads((root / authority["approved_candidate"]["path"]).read_text(encoding="utf-8"))
    if authority.get("status") != "PUBLISHED" or candidate.get("artifact_id") != authority.get("artifact_id"):
        raise AA4EvidenceContractError("published AA4 D5 authority is not bound to its candidate")
    return candidate


def build_static_candidate(contract: dict[str, Any], *, control_id: str, target: dict[str, str], collected_at_utc: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Create an in-memory candidate only; this module never performs HTTP or writes files."""
    if target != AA4_TARGET:
        raise AA4EvidenceContractError("AA4 target tuple mismatch")
    mapping = next((item for item in contract["source_contract"]["control_to_source_mapping"] if item["control_id"] == control_id), None)
    if mapping is None:
        raise AA4EvidenceContractError("control is outside the approved AA4 D5 scope")
    expected = set(mapping["sources"])
    observed = {item.get("request_uri") for item in sources}
    if expected != observed or any(item.get("request_method") != "GET" for item in sources):
        raise AA4EvidenceContractError("source mapping does not exactly match the approved read-only contract")
    if any(not item.get("captured_payload") for item in sources):
        raise AA4EvidenceContractError("source payload is missing")
    record: dict[str, Any] = {
        "schema_version": "1.0.0-proposed",
        "record_id": f"AA4-D5-{control_id}-{hashlib.sha256((control_id + collected_at_utc).encode()).hexdigest()[:16]}",
        "control_id": control_id,
        "target": target,
        "collector": {"identity": COLLECTOR_IDENTITY, "version": COLLECTOR_VERSION},
        "collected_at_utc": collected_at_utc,
        "sources": sources,
        "provenance": {"collector_identity": COLLECTOR_IDENTITY, "collector_version": COLLECTOR_VERSION, "target_validation": "EXACT_MATCH", "credential_scope_classification": "READ_ONLY_REPOSITORY_SCOPE", "source_observation_time_utc": collected_at_utc},
        "collection_status": "STATIC_VALIDATED_ONLY",
    }
    record["canonical_payload_sha256"] = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    return record
