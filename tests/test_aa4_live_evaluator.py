import pytest

from hayes_verify.aa4_live_evaluator import evaluate


@pytest.mark.parametrize(
    ("control_id", "payloads"),
    [
        ("EMS-CTRL-009", [{"required_status_checks": {}, "enforce_admins": {}, "required_pull_request_reviews": {}, "restrictions": {}}]),
        ("EMS-CTRL-010", [{"required_approving_review_count": 1}]),
        ("EMS-CTRL-011", [{"content": "* @owner"}, {"required_pull_request_reviews": {"require_code_owner_reviews": True}}]),
        ("EMS-CTRL-012", [{"enabled": True}]),
        ("EMS-CTRL-013", [[{"enforcement": "active", "target": "tag"}]]),
        ("EMS-CTRL-014", [{"workflow": "issue-link"}, {"checks": ["issue-link"]}]),
        ("EMS-CTRL-015", [{"template": "issue"}]),
        ("EMS-CTRL-017", [{"content": "security"}]),
        ("EMS-CTRL-018", [{"security_and_analysis": {"secret_scanning": {"status": "enabled"}, "secret_scanning_push_protection": {"status": "enabled"}}}]),
        ("EMS-CTRL-020", [{"license": {"spdx_id": "MIT"}}, {"LICENSE": "MIT"}]),
        ("EMS-CTRL-021", [{"bomFormat": "CycloneDX", "components": [{}]}]),
        ("EMS-CTRL-033", [{"workflow": "build"}, {"id": 1}]),
        ("EMS-CTRL-039", [{"id": 20656884777, "protection_rules": [{"type": "required_reviewers"}]}]),
    ],
)
def test_approved_rules_accept_complete_positive_projections(control_id, payloads):
    assert evaluate(control_id, payloads)["result_status"] == "PASS"


def test_missing_payload_fails_closed():
    assert evaluate("EMS-CTRL-012", [])["result_status"] == "UNRESOLVED"
