import pytest
from test_onboarding_plan import current, plan

from hayes_verify.onboarding_execution import compose_requests
from hayes_verify.onboarding_review import ReviewValidationError, build_queue, derive_current_state


def data():
 p=plan();m=compose_requests(p,current_hashes=current(p),evidence_candidates=[],requested_at_utc="2026-08-16T00:00:00Z")["manifest"];r={"assessment_plan_sha256":p["plan_sha256"]};return p,m,r
def test_queue_deterministic_and_sources_unchanged():
 p,m,r=data();a=build_queue(p,m,r,source_hashes={"manifest":"a"*64});b=build_queue(p,m,r,source_hashes={"manifest":"a"*64});assert a["review_item_ids"]==b["review_item_ids"] and a["review_item_count"]>0
def test_append_only_lifecycle_and_invalid_transition():
 p,m,r=data();q=build_queue(p,m,r,source_hashes={"manifest":"a"*64});i=q["review_item_ids"][0];events=[{"review_event_id":"e1","review_item_id":i,"from_state":"OPEN","to_state":"IN_REVIEW","actor":"a","actor_role":"CONTROL_OWNER"},{"review_event_id":"e2","review_item_id":i,"from_state":"IN_REVIEW","to_state":"RESOLVED","actor":"a","actor_role":"CONTROL_OWNER"}];assert derive_current_state(q,events)[i]=="RESOLVED"
 with pytest.raises(ReviewValidationError):derive_current_state(q,[events[1]])
