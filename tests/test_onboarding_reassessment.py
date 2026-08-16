import pytest

from hayes_verify.onboarding_reassessment import classify_changes


@pytest.mark.parametrize("category",["CLASSIFICATION","CONTROL_SUPPORT","EFFECTIVE_APPLICABILITY","EXCEPTION","EMS_AUTHORITY","AUTHORITATIVE_EVIDENCE","HUMAN_REVIEW_CONDITION"])
def test_material(category):assert classify_changes([{"category":category}])["decision"]=="REASSESSMENT_REQUIRED"
def test_no_change_and_local_path():assert classify_changes([])["decision"]=="NO_REASSESSMENT_REQUIRED" and classify_changes([{"category":"LOCAL_EXECUTION_CONFIGURATION"}])["decision"]=="NO_REASSESSMENT_REQUIRED"
def test_ambiguous_blocks():assert classify_changes([{"category":"REPOSITORY_IDENTITY","ambiguous":True}])["decision"]=="REASSESSMENT_BLOCKED"
