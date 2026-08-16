import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hayes_verify.onboarding_applicability import (
    ApplicabilityValidationError,
    compile_effective_applicability,
)
from hayes_verify.onboarding_classification import classification_snapshot
from hayes_verify.onboarding_identity import RepositoryIdentity, repository_snapshot

ROOT = Path(__file__).parents[1]
SHA = "c" * 64


def source():
    return {"source_type": "SYNTHETIC", "source_reference": "fixture", "observation_timestamp": "2026-08-15T00:00:00Z"}


def repository():
    return repository_snapshot(RepositoryIdentity("REPO-9003", "fixture", "synthetic", "github.com", "https://github.com/synthetic/fixture", "ACTIVE", "main"), captured_at="2026-08-15T00:00:00Z", authority_reference="ems", authority_sha256="a" * 64)


def attrs(**overrides):
    result = {
        "production": {"state": "KNOWN_TRUE", "value": True, "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"},
        "internet_exposed": {"state": "KNOWN_FALSE", "value": False, "source": source(), "confirmation_state": "AUTO_DISCOVERED"},
        "contains_customer_data": {"state": "KNOWN_FALSE", "value": False, "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"},
        "ai_enabled": {"state": "KNOWN_FALSE", "value": False, "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"},
        "owner": {"state": "KNOWN", "value": "Synthetic", "source": source(), "confirmation_state": "AUTO_DISCOVERED"},
        "tier": {"state": "KNOWN", "value": "Tier2", "source": source(), "confirmation_state": "AUTO_DISCOVERED"},
        "service_criticality": {"state": "KNOWN", "value": "Low", "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"},
        "data_classification": {"state": "KNOWN", "value": "Internal", "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"},
    }
    result.update(overrides)
    return result


def snapshots(attributes=None):
    repo = repository()
    repo_sha = hashlib.sha256(json.dumps(repo, sort_keys=True).encode()).hexdigest()
    cls = classification_snapshot(repo, repo_sha, attrs() if attributes is None else attributes, captured_at="2026-08-15T00:00:00Z", authority_reference="ems-class", authority_sha256="b" * 64, repository_snapshot_schema=str(ROOT / "schemas/repository_snapshot.schema.json"))
    return repo, repo_sha, cls, hashlib.sha256(json.dumps(cls, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def policy(*controls):
    return {"policy_reference": "registry/policy_applicability.yaml", "policy_sha256": SHA, "controls": list(controls)}


def compile(policy_value, evidence=None, attributes=None, support=None):
    repo, repo_sha, cls, cls_sha = snapshots(attributes)
    return compile_effective_applicability(repo, cls, repository_snapshot_sha256=repo_sha, classification_snapshot_sha256=cls_sha, repository_snapshot_schema=str(ROOT / "schemas/repository_snapshot.schema.json"), classification_snapshot_schema=str(ROOT / "schemas/classification_snapshot.schema.json"), current_policy=policy_value, condition_evidence=evidence or [], captured_at="2026-08-15T01:00:00Z", ems_authority_reference="registry/new_repository_onboarding_effective_applicability.json", ems_authority_sha256=SHA, hayes_registry=support)


def row(snapshot, control_id):
    return next(item for item in snapshot["controls"] if item["control_id"] == control_id)


def test_repository_policy_resolves_applicable_and_consumes_ws2_hash():
    output = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": [{"attribute": "production", "equals": True}]}))
    assert row(output, "EMS-CTRL-025")["applicability_state"] == "APPLICABLE"
    assert output["classification_snapshot_sha256"] == snapshots()[3]


def test_known_false_positively_resolves_not_applicable():
    output = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": [{"attribute": "production", "equals": False}]}))
    assert row(output, "EMS-CTRL-025")["applicability_state"] == "NOT_APPLICABLE"


@pytest.mark.parametrize("attribute", ["production", "internet_exposed", "contains_customer_data", "ai_enabled"])
def test_unknown_boolean_never_coerces_to_not_applicable(attribute):
    values = attrs(**{attribute: {"state": "UNKNOWN", "value": None, "source": source(), "confirmation_state": "UNKNOWN"}})
    output = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": [{"attribute": attribute, "equals": True}]}), attributes=values)
    assert row(output, "EMS-CTRL-025")["applicability_state"] == "APPLICABILITY_UNRESOLVED"


def test_missing_policy_condition_evidence_is_unresolved():
    output = compile(policy({"control_id": "EMS-CTRL-029", "scope": "SERVICE", "conditions": [{"condition_id": "service_registered", "equals": True}]}))
    assert row(output, "EMS-CTRL-029")["applicability_state"] == "APPLICABILITY_UNRESOLVED"


@pytest.mark.parametrize(("value", "state"), [(True, "APPLICABLE"), (False, "NOT_APPLICABLE")])
def test_condition_evidence_deterministically_resolves(value, state):
    evidence = [{"condition_id": "service_registered", "control_id": "EMS-CTRL-029", "source_type": "SERVICE_REGISTRY", "source_reference": "svc-1", "observed_value": value, "observed_at": "2026-08-15T00:00:00Z", "authority": "service registry", "provenance": "synthetic"}]
    output = compile(policy({"control_id": "EMS-CTRL-029", "scope": "SERVICE", "conditions": [{"condition_id": "service_registered", "equals": True}]}), evidence)
    assert row(output, "EMS-CTRL-029")["applicability_state"] == state


@pytest.mark.parametrize("scope", ["SERVICE", "ORGANIZATION"])
def test_non_repository_scope_without_authority_is_unresolved(scope):
    output = compile(policy({"control_id": "EMS-CTRL-030", "scope": scope, "conditions": []}))
    assert row(output, "EMS-CTRL-030")["applicability_state"] == "APPLICABILITY_UNRESOLVED"


def test_unsupported_control_can_still_be_applicable():
    output = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}), support={"EMS-CTRL-025": "NOT_IMPLEMENTED"})
    result = row(output, "EMS-CTRL-025")
    assert result["applicability_state"] == "APPLICABLE" and result["support_state"] == "NOT_IMPLEMENTED"


def test_schema_and_new_inputs_produce_distinct_immutable_snapshots():
    first = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}))
    changed = attrs(production={"state": "KNOWN_FALSE", "value": False, "source": source(), "confirmation_state": "HUMAN_CONFIRMED", "confirmed_by": "owner"})
    second = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}), attributes=changed)
    third = compile({**policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}), "policy_sha256": "d" * 64})
    Draft202012Validator(json.loads((ROOT / "schemas/effective_applicability_snapshot.schema.json").read_text())).validate(first)
    assert first["snapshot_id"] != second["snapshot_id"] != third["snapshot_id"]


def test_local_path_is_rejected_and_compliance_not_emitted():
    with pytest.raises(ApplicabilityValidationError):
        compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}), [{"condition_id": "x", "control_id": "EMS-CTRL-025", "source_type": "X", "source_reference": "x", "observed_value": True, "observed_at": "2026", "authority": "x", "local_path": "C:/x"}])
    output = compile(policy({"control_id": "EMS-CTRL-025", "scope": "REPOSITORY", "conditions": []}))
    assert "compliance_result" not in output
