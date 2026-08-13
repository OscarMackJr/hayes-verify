import json
from pathlib import Path

from hayes_verify.contracts import ContractBundle


def test_contract_bundle_loads():
    bundle = ContractBundle.discover()
    assert bundle.freeze["status"] == "PASS"
    assert bundle.freeze["authority"]["applicability"] == "EMS"
    assert bundle.freeze["authority"]["evidence_promotion"] == "EMS"


def test_example_request_validates():
    bundle = ContractBundle.discover()
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "examples" / "evaluation_request.json").read_text())
    bundle.validate_request(payload)
