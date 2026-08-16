import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from hayes_verify.onboarding_identity import (
    IdentityValidationError,
    consume_controlled_identities,
    repository_snapshot,
)

AUTH = "C:/temp/standars/ems/registry/new_repository_onboarding_identity_authority.json"
SHA = "a" * 64

def row(**updates):
    value = {"repository_id":"REPO-9001","repository_host":"github.com","repository_owner_or_org":"synthetic","repository_name":"fixture","repository_url":"https://github.com/synthetic/fixture","lifecycle_state":"ACTIVE","default_branch":"main"}
    value.update(updates); return value

def snapshot(record=None):
    ident=consume_controlled_identities({"identities":[record or row()]})["REPO-9001"]
    return repository_snapshot(ident,captured_at="2026-08-15T00:00:00Z",authority_reference=AUTH,authority_sha256=SHA)

def test_valid_controlled_id_and_provenance():
    s=snapshot(); assert s["repository_id"]=="REPO-9001" and s["authority_reference"]==AUTH

def test_malformed_id_rejected():
    with pytest.raises(IdentityValidationError): consume_controlled_identities({"identities":[row(repository_id="fixture")]})

def test_duplicate_id_rejected():
    with pytest.raises(IdentityValidationError): consume_controlled_identities({"identities":[row(),row(repository_name="other",repository_url="https://github.com/synthetic/other")]})

@pytest.mark.parametrize("state",["RENAMED","TRANSFERRED","ARCHIVED","RETIRED","DELETED"])
def test_lifecycle_retains_same_id(state):
    assert snapshot(row(lifecycle_state=state))["repository_id"]=="REPO-9001"

def test_name_change_is_not_identity_authority():
    assert snapshot(row(repository_name="renamed"))["repository_id"]=="REPO-9001"

def test_local_path_rejected_and_excluded():
    with pytest.raises(IdentityValidationError): consume_controlled_identities({"identities":[row(local_path="C:/machine/private")]})
    assert "local_path" not in snapshot()

def test_snapshot_schema_and_unknown_extra_rejected():
    schema=json.loads((Path(__file__).parents[1]/"schemas/repository_snapshot.schema.json").read_text())
    Draft202012Validator(schema).validate(snapshot())
    bad=snapshot();bad["unknown_identity_field"]="no"
    with pytest.raises(ValidationError): Draft202012Validator(schema).validate(bad)

def test_hayes_never_allocates_id():
    with pytest.raises(IdentityValidationError): consume_controlled_identities({"identities":[row(repository_id="")]})
