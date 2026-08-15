import json
from pathlib import Path

from hayes_verify.evaluator_families.release_integrity import evaluate_rule


def rules(tmp_path: Path) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {"rules": {
                "EMS-CTRL-034": {"supported": True, "evidence_type": "MANIFEST", "decision_ids": ["RI-034-01"], "evidence_authority": "manifest"},
                "EMS-CTRL-035": {"supported": True, "evidence_type": "SHA", "decision_ids": ["RI-035-01"], "evidence_authority": "checksum"},
                "EMS-CTRL-036": {"supported": True, "evidence_type": "SIGN", "decision_ids": ["RI-036-01"], "evidence_authority": "signing"},
                "EMS-CTRL-037": {"supported": True, "evidence_type": "RETENTION", "decision_ids": ["RI-037-01"], "evidence_authority": "retention"},
                "EMS-CTRL-038": {"supported": True, "evidence_type": "VERSION", "decision_ids": ["RI-038-01"], "evidence_authority": "tags"},
                "EMS-CTRL-040": {"supported": True, "evidence_type": "ROLLBACK", "decision_ids": ["RI-040-07"], "evidence_authority": "service"},
            }},
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def manifest(root: Path, version: str = "1.2.3") -> Path:
    path = root / "release" / "r1" / "release_manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "release_id": "r1", "source_revision": "abc", "version": version,
        "artifact_inventory": ["artifact.zip"], "integrity_references": ["SHA256SUMS"],
        "approval_record": "approval", "timestamp": "2026-08-14T00:00:00Z",
    }), encoding="utf-8")
    return path


def test_manifest_missing_required_field_fails(tmp_path):
    path = manifest(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["approval_record"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    _, result = evaluate_rule("EMS-CTRL-034", tmp_path, rules(tmp_path))
    assert result["result_state"] == "FAIL"


def test_checksum_inventory_gap_fails(tmp_path):
    path = manifest(tmp_path)
    (path.parent / "SHA256SUMS").write_text("a" * 64 + "  other.zip\n", encoding="utf-8")
    _, result = evaluate_rule("EMS-CTRL-035", tmp_path, rules(tmp_path))
    assert result["result_state"] == "FAIL"


def test_version_violation_fails(tmp_path):
    manifest(tmp_path, "release-1")
    _, result = evaluate_rule("EMS-CTRL-038", tmp_path, rules(tmp_path))
    assert result["result_state"] == "FAIL"


def test_service_rollback_evidence_routes_to_human_review(tmp_path):
    evidence, result = evaluate_rule("EMS-CTRL-040", tmp_path, rules(tmp_path))
    assert evidence[0]["control_id"] == "EMS-CTRL-040"
    assert result["result_state"] == "WARNING"
    assert result["evidence_state"] == "INSUFFICIENT"
    assert result["assertions"][0]["assertion_id"] == "authoritative_evidence_requires_human_review"


def test_no_formal_release_evidence_routes_to_human_review(tmp_path):
    _, result = evaluate_rule("EMS-CTRL-038", tmp_path, rules(tmp_path))
    assert result["result_state"] == "WARNING"
    assert result["evidence_state"] == "INSUFFICIENT"
