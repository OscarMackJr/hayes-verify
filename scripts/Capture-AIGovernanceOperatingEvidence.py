import argparse,json
from pathlib import Path
from datetime import date

CONTROL_MAP={
    "EMS-CTRL-049":{
        "register":"ai_platform_register.json",
        "assertion":"unapproved_platform_handling_detected",
        "qualifies":lambda r: r.get("approval_status") in {"REJECTED","CONDITIONAL","EXCEPTION"}
            or bool(r.get("exception_id"))
            or (r.get("decision") in {"REJECTED","DENIED","ESCALATED","EXCEPTION"})
    },
    "EMS-CTRL-050":{
        "register":"ai_data_handling_assessment.json",
        "assertion":"sensitive_data_handling_detected",
        "qualifies":lambda r: (
            r.get("contains_confidential_data") is True
            or r.get("contains_customer_data") is True
            or str(r.get("prompt_data_classification","")).upper() in {"CONFIDENTIAL","RESTRICTED","SENSITIVE"}
        ) and (
            r.get("redaction_required") is False
            or r.get("redaction_performed") is True
            or r.get("decision") in {"REJECTED","ESCALATED","CONDITIONAL"}
        )
    },
    "EMS-CTRL-053":{
        "register":"ai_security_review_register.json",
        "assertion":"risk_or_finding_tracking_detected",
        "qualifies":lambda r: bool(r.get("finding_id")) and bool(r.get("risk")) and bool(r.get("remediation")) and bool(r.get("owner")) and bool(r.get("status"))
    }
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--register-dir",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    regdir=Path(a.register_dir); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    envelopes=[]; summary=[]

    for cid,cfg in CONTROL_MAP.items():
        path=regdir/cfg["register"]
        obj=json.loads(path.read_text(encoding="utf-8"))
        records=obj.get("records",[])
        qualifying=[r for r in records if cfg["qualifies"](r)]

        # Critical rule: empty register can NEVER PASS.
        if len(records)==0:
            status="WARNING"
            suff="INSUFFICIENT"
            reason="EMPTY_REGISTER"
        elif not qualifying:
            status="WARNING"
            suff="INSUFFICIENT"
            reason="NO_QUALIFYING_OPERATING_RECORD"
        else:
            status="PASS"
            suff="SUFFICIENT"
            reason="QUALIFYING_OPERATING_RECORD_PRESENT"

        env={
            "control_id":cid,
            "scope":"ORGANIZATION",
            "collector_id":"HS-AI-GOVERNANCE-OPERATING-REGISTERS",
            "collector_version":"2B2.5c",
            "status":status,
            "sufficiency":suff,
            "assertion":cfg["assertion"],
            "record_count":len(records),
            "qualifying_record_count":len(qualifying),
            "promotion_eligible":status=="PASS",
            "evidence_class":"OPERATING_EVIDENCE",
            "evidence_references":[str(path)] if qualifying else [],
            "evidence_date":date.today().isoformat(),
            "reason":reason
        }
        envelopes.append(env)
        summary.append({
            "control_id":cid,
            "assertion":cfg["assertion"],
            "record_count":len(records),
            "qualifying_record_count":len(qualifying),
            "status":status,
            "sufficiency":suff,
            "promotion_eligible":status=="PASS",
            "reason":reason
        })

    (out/"evidence_envelopes.jsonl").write_text("".join(json.dumps(e)+"\n" for e in envelopes),encoding="utf-8")
    (out/"evidence_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({
        "control_count":len(summary),
        "promotion_eligible_count":sum(x["promotion_eligible"] for x in summary),
        "empty_register_count":sum(x["reason"]=="EMPTY_REGISTER" for x in summary)
    },indent=2))

if __name__=="__main__": main()
