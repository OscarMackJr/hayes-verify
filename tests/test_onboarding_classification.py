import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hayes_verify.onboarding_classification import (
 ClassificationValidationError,
 classification_snapshot,
)
from hayes_verify.onboarding_identity import RepositoryIdentity, repository_snapshot

ROOT=Path(__file__).parents[1]; SHA="b"*64
def rs(): return repository_snapshot(RepositoryIdentity("REPO-9002","fixture","synthetic","github.com","https://github.com/synthetic/fixture","ACTIVE","main"),captured_at="2026-08-15T00:00:00Z",authority_reference="ems",authority_sha256="a"*64)
def src(): return {"source_type":"SYNTHETIC","source_reference":"fixture","observation_timestamp":"2026-08-15T00:00:00Z"}
def attrs(**u):
 d={"production":{"state":"KNOWN_TRUE","value":True,"source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner","confirmed_at":"2026-08-15T00:00:00Z"},"internet_exposed":{"state":"KNOWN_FALSE","value":False,"source":src(),"confirmation_state":"AUTO_DISCOVERED"},"contains_customer_data":{"state":"KNOWN_FALSE","value":False,"source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"},"ai_enabled":{"state":"KNOWN_TRUE","value":True,"source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"},"owner":{"state":"KNOWN","value":"Synthetic","source":src(),"confirmation_state":"AUTO_DISCOVERED"},"tier":{"state":"KNOWN","value":"Tier2","source":src(),"confirmation_state":"AUTO_DISCOVERED"},"service_criticality":{"state":"KNOWN","value":"Low","source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"},"data_classification":{"state":"KNOWN","value":"Internal","source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"}};d.update(u);return d
def snap(a=None): return classification_snapshot(rs(),hashlib.sha256(json.dumps(rs(),sort_keys=True).encode()).hexdigest(),a if a is not None else attrs(),captured_at="2026-08-15T00:00:00Z",authority_reference="ems-class",authority_sha256=SHA,repository_snapshot_schema=str(ROOT/'schemas/repository_snapshot.schema.json'))
def test_valid_hash_bound_snapshot(): assert snap()["repository_id"]=="REPO-9002"
def test_true_false_retained(): assert snap()["attributes"]["production"]["state"]=="KNOWN_TRUE" and snap()["attributes"]["internet_exposed"]["state"]=="KNOWN_FALSE"
@pytest.mark.parametrize("field",["production","internet_exposed","contains_customer_data","ai_enabled"])
def test_unknown_retained_not_false(field):
 a=attrs();a[field]={"state":"UNKNOWN","value":None,"source":src(),"confirmation_state":"UNKNOWN"}; assert snap(a)["attributes"][field]["state"]=="UNKNOWN"
def test_missing_boolean_does_not_default_false(): assert snap({})["attributes"]["production"]["state"]=="UNKNOWN"
def test_auto_discovered_not_human_confirmed(): assert snap()["attributes"]["internet_exposed"]["confirmation_state"]=="AUTO_DISCOVERED"
def test_unknown_non_boolean():
 a=attrs(owner={"state":"UNKNOWN","value":None,"source":src(),"confirmation_state":"UNKNOWN"});assert snap(a)["attributes"]["owner"]["state"]=="UNKNOWN"
def test_identity_not_mutable_and_local_path_rejected():
 a=attrs(production={"state":"KNOWN_TRUE","value":True,"source":{**src(),"local_path":"C:/no"},"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"});
 with pytest.raises(ClassificationValidationError): snap(a)
def test_schema_and_changed_classification_new_snapshot():
 schema=json.loads((ROOT/'schemas/classification_snapshot.schema.json').read_text());Draft202012Validator(schema).validate(snap());a=attrs(production={"state":"KNOWN_FALSE","value":False,"source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"});assert snap()["classification_snapshot_id"]!=snap(a)["classification_snapshot_id"]
def test_invalid_boolean_coercion_rejected():
 a=attrs(production={"state":"KNOWN_FALSE","value":"false","source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"});
 with pytest.raises(ClassificationValidationError): snap(a)
