"""WS7 append-only onboarding human review."""
from __future__ import annotations

import hashlib
import json
from typing import Any

STATES={"OPEN","IN_REVIEW","RESOLVED","EXCEPTION_APPROVED","SUPERSEDED"}
TRANSITIONS={"OPEN":{"IN_REVIEW","SUPERSEDED"},"IN_REVIEW":{"RESOLVED","EXCEPTION_APPROVED"}}
class ReviewValidationError(ValueError):pass
def sha(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def build_queue(plan,manifest,readiness,*,source_hashes):
 if plan.get("state")!="FROZEN" or manifest.get("assessment_plan_sha256")!=plan.get("plan_sha256") or readiness.get("assessment_plan_sha256")!=plan.get("plan_sha256"):raise ReviewValidationError("lineage invalid")
 items=[]
 for entry in plan["controls"]:
  reason=None; state=entry["applicability_state"]
  if state=="APPLICABILITY_UNRESOLVED":reason="APPLICABILITY_UNRESOLVED"
  elif entry["human_review_required"] and entry["support_state"]=="HUMAN_EVIDENCE_REQUIRED":reason="HUMAN_EVIDENCE_REQUIRED"
  else:
   r=next((x for x in manifest.get("control_coverage",[]) if x["control_id"]==entry["control_id"]),None)
   if r and r["composition_disposition"]=="NO_REQUEST_EVIDENCE_UNRESOLVED":reason="EVIDENCE_UNRESOLVED"
  if reason:
   b={"assessment_plan_id":plan["assessment_plan_id"],"assessment_plan_sha256":plan["plan_sha256"],"repository_id":plan["repository_id"],"control_id":entry["control_id"],"source_artifact_type":"MACHINE_ARTIFACT","source_artifact_reference":"frozen-lineage","source_artifact_sha256":source_hashes["manifest"],"source_machine_state":state,"reason_code":reason,"reason_detail":entry.get("human_review_reason") or reason,"authoritative_evidence_source":entry["evidence_authority"],"required_reviewer_role":"CONTROL_OWNER_OR_AUTHORITY","exception_path_available":False,"created_at":"2026-08-16T00:00:00Z","initial_state":"OPEN","provenance":{"generator":"hayes-verify"}};b["review_item_id"]="REV-"+sha(b)[:16];items.append(b)
 q={"assessment_plan_id":plan["assessment_plan_id"],"assessment_plan_sha256":plan["plan_sha256"],"repository_id":plan["repository_id"],"created_at":"2026-08-16T00:00:00Z","source_artifact_hashes":source_hashes,"review_item_count":len(items),"review_item_ids":[x["review_item_id"] for x in items],"items":items};q["queue_sha256"]=sha(q);return q
def derive_current_state(queue,events):
 items={x["review_item_id"]:x for x in queue["items"]}; current={k:"OPEN" for k in items}; seen=set()
 for e in events:
  if e["review_event_id"] in seen or e["review_item_id"] not in items:raise ReviewValidationError("duplicate or unknown event")
  seen.add(e["review_event_id"]); old=current[e["review_item_id"]]
  if e.get("from_state")!=old or e.get("to_state") not in TRANSITIONS.get(old,set()):raise ReviewValidationError("invalid lifecycle transition")
  if not e.get("actor") or not e.get("actor_role"):raise ReviewValidationError("reviewer attribution required")
  if e["to_state"]=="EXCEPTION_APPROVED" and not e.get("exception_reference"):raise ReviewValidationError("exception reference required")
  if e["to_state"]=="SUPERSEDED" and not e.get("supersedes_event_id"):raise ReviewValidationError("supersession reference required")
  current[e["review_item_id"]]=e["to_state"]
 return current
