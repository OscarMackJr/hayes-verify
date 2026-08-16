import json
from pathlib import Path

from hayes_verify.onboarding_orchestrator import inventory_tree, run_synthetic_pilot


def test_synthetic_orchestrator_executes_existing_evaluator(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    prior = root / "generated/onboarding/runs/SYNTHETIC_ONBOARDING_INTEGRATION"
    before = inventory_tree(prior)
    output = tmp_path / "runs"
    result = run_synthetic_pilot(root, output, prior)
    executed = json.loads((Path(result["run_dir"]) / "results/executed_results.json").read_text())
    assert executed["actual_evaluator_invocation_count"] == 1
    assert executed["contract_valid_executed_result_count"] == 1
    assert executed["hand_supplied_machine_result_count"] == 0
    assert result["certification"]["compliance_attestation"] is False
    assert inventory_tree(prior) == before
