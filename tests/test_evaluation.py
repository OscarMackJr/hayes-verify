import json
from pathlib import Path

from hayes_verify.contracts import ContractBundle
from hayes_verify.orchestration import run_evaluation


def test_bootstrap_evaluation_never_promotes(tmp_path):
    bundle = ContractBundle.discover()
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "examples" / "evaluation_request.json").read_text())
    payload["repository_name"] = str(tmp_path)
    result = run_evaluation(bundle, payload)
    assert result["promotion_state"] == "NOT_PROMOTED"
    assert result["result_state"] in {"WARNING", "FAIL"}
