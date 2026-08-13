import argparse,csv,json
from pathlib import Path
REQ={
"EMS-CTRL-023":"Retain vulnerability findings with severity, remediation target/due date, owner, and status/closure history.",
"EMS-CTRL-024":"Retain approved security exception records with scope/reason, approver, expiry/review date, and lifecycle status.",
"EMS-CTRL-063":"Retain data-classification records with level, owner/steward, system or dataset scope, and review/update history.",
"EMS-CTRL-065":"Retain retention records/schedules with period, data scope, authority, and actual disposition/retention execution evidence.",
"EMS-CTRL-066":"Retain production-data protection evidence showing scope, control/handling, accountable owner, and validation/review."
}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--gaps",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    with Path(a.gaps).open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        out.append({"control_id":r["control_id"],"control_name":r["control_name"],"scope":r["scope"],
                    "disposition":"REMEDIATE","current_status":"WARNING","missing_assertions":r["missing_assertions"],
                    "required_evidence":REQ[r["control_id"]],"remediation_state":"OPEN"})
    fields=["control_id","control_name","scope","disposition","current_status","missing_assertions","required_evidence","remediation_state"]
    with Path(a.out).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    print(json.dumps({"remediation_count":len(out)},indent=2))
if __name__=="__main__":main()
