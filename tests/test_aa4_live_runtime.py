from pathlib import Path

from hayes_verify.aa4_live_runtime import collect_with_getter, evaluate_record, result_record
from hayes_verify.aa4_real_evidence import AA4_TARGET, load_published_contract

ROOT = Path(__file__).resolve().parents[1]


def test_getter_is_injected_and_signature_result_is_bound():
    contract = load_published_contract(ROOT)
    evidence = collect_with_getter(contract, control_id="EMS-CTRL-012", target=AA4_TARGET, collected_at_utc="2026-08-27T12:00:00Z", getter=lambda _uri: {"response_status": 200, "captured_payload": {"enabled": True}})
    result = result_record(evidence, evaluate_record(evidence), authorization_reference="test", created_at_utc="2026-08-27T12:00:01Z")
    assert result["result_status"] == "PASS"
    assert result["evidence_record_sha256"] == evidence["canonical_payload_sha256"]
