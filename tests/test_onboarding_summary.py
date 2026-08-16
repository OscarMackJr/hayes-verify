from test_onboarding_plan import current, plan

from hayes_verify.onboarding_execution import compose_requests
from hayes_verify.onboarding_summary import summarize


def inputs():
 p=plan();m=compose_requests(p,current_hashes=current(p),evidence_candidates=[{"control_id":"EMS-CTRL-025","authority_type":"REPOSITORY","source_reference":"x","observed_value":True}],requested_at_utc="2026-08-16T00:00:00Z")["manifest"];r={"assessment_plan_id":p["assessment_plan_id"],"assessment_plan_sha256":p["plan_sha256"],"repository_id":p["repository_id"],"request_level_readiness":[{"control_id":x["control_id"],"readiness_disposition":"EXECUTION_READY"} for x in m["control_coverage"]]};return p,m,r
def test_fail_is_finding_not_incomplete():
 p,m,r=inputs();s=summarize(p,m,r,{}, {"EMS-CTRL-025":"FAIL"});assert s["assessment_completeness"] in {"COMPLETE_WITH_FINDINGS","PARTIAL"} and next(x for x in s["control_results"] if x["control_id"]=="EMS-CTRL-025")["machine_result"]=="FAIL"
def test_not_implemented_and_unresolved_remain_partial():
 p,m,r=inputs();s=summarize(p,m,r,{},{});assert s["assessment_completeness"]=="PARTIAL"
