"""WS8 derived assessment completeness; does not alter compliance results."""
from __future__ import annotations

import hashlib
import json


def summarize(plan,composition,readiness,review_states,machine_results):
 rows=[]
 for e in plan["controls"]:
  c=e["control_id"];m=machine_results.get(c);review=review_states.get(c);comp=next((x["composition_disposition"] for x in composition["control_coverage"] if x["control_id"]==c),None);ready=next((x["readiness_disposition"] for x in readiness["request_level_readiness"] if x["control_id"]==c),None)
  if e["applicability_state"]=="NOT_APPLICABLE":f="NOT_APPLICABLE"
  elif e["applicability_state"]=="APPLICABILITY_UNRESOLVED" or review in {"OPEN","IN_REVIEW"}:f="UNRESOLVED"
  elif e["support_state"]=="NOT_IMPLEMENTED":f="NOT_IMPLEMENTED"
  elif ready=="BLOCKED_BY_CHECKOUT" or m=="EXECUTION_ERROR":f="EXECUTION_BLOCKED"
  elif m=="FAIL":f="NONCOMPLIANT"
  elif m in {"WARNING","INSUFFICIENT","HUMAN_REVIEW"}:f="WARNING"
  else:f="COMPLIANT"
  rows.append({"control_id":c,"scope":e["scope"],"applicability_state":e["applicability_state"],"support_state":e["support_state"],"composition_state":comp,"execution_readiness":ready,"machine_result":m,"human_review_state":review,"finding_state":f})
 unresolved=sum(x["finding_state"] in {"UNRESOLVED","NOT_IMPLEMENTED","EXECUTION_BLOCKED","WARNING"} for x in rows);fails=sum(x["finding_state"]=="NONCOMPLIANT" for x in rows);state="PARTIAL" if unresolved else ("COMPLETE_WITH_FINDINGS" if fails else "COMPLETE")
 b={"assessment_plan_id":plan["assessment_plan_id"],"assessment_plan_sha256":plan["plan_sha256"],"repository_id":plan["repository_id"],"control_results":rows,"assessment_completeness":state,"finding_count":fails,"unresolved_count":unresolved,"blocked_count":sum(x["finding_state"]=="EXECUTION_BLOCKED" for x in rows)};b["assessment_summary_id"]="SUM-"+hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest()[:16];return b
