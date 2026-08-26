import hashlib
from pathlib import Path

import pytest

from hayes_verify.aa4_real_evidence import AA4EvidenceContractError, AA4_TARGET, build_static_candidate, canonical_json_bytes, load_published_contract


ROOT = Path(__file__).resolve().parents[1]


def source(uri: str) -> dict:
    return {"request_method": "GET", "request_uri": uri, "response_status": 200, "response_etag": "test", "source_object_sha": "a" * 40, "captured_payload": {"fixture": True}}


def test_static_candidate_is_canonical_and_non_executing():
    contract = load_published_contract(ROOT)
    item = next(row for row in contract["source_contract"]["control_to_source_mapping"] if row["control_id"] == "EMS-CTRL-009")
    record = build_static_candidate(contract, control_id="EMS-CTRL-009", target=AA4_TARGET, collected_at_utc="2026-08-26T20:00:00Z", sources=[source(uri) for uri in item["sources"]])
    copy = dict(record); digest = copy.pop("canonical_payload_sha256")
    assert digest == hashlib.sha256(canonical_json_bytes(copy)).hexdigest()
    assert record["collection_status"] == "STATIC_VALIDATED_ONLY"


def test_static_candidate_fails_closed_on_target_or_source_change():
    contract = load_published_contract(ROOT)
    with pytest.raises(AA4EvidenceContractError):
        build_static_candidate(contract, control_id="EMS-CTRL-009", target={**AA4_TARGET, "scope": "PRODUCTION"}, collected_at_utc="2026-08-26T20:00:00Z", sources=[])
    with pytest.raises(AA4EvidenceContractError):
        build_static_candidate(contract, control_id="EMS-CTRL-009", target=AA4_TARGET, collected_at_utc="2026-08-26T20:00:00Z", sources=[source("GET /wrong")])
