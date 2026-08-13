import argparse,csv,json
from pathlib import Path

REQUIREMENTS={
"EMS-CTRL-049":"Retain an operating record showing an unapproved AI platform was blocked, rejected, denied, escalated, or handled through an approved exception process.",
"EMS-CTRL-050":"Retain an operating record showing prompt data classification or sensitive/confidential-data handling was actually applied to AI usage.",
"EMS-CTRL-053":"Retain an AI security review/assessment record with tracked finding, risk, exception, or remediation evidence."
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--resolution",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    with Path(a.resolution).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    rem=[]
    for r in rows:
        if str(r["promotion_eligible"]).lower()=="true": continue
        rem.append({
            "control_id":r["control_id"],
            "control_name":r["control_name"],
            "scope":r["scope"],
            "disposition":"REMEDIATE",
            "current_status":"WARNING",
            "missing_assertion":r["assertion"],
            "required_evidence":REQUIREMENTS[r["control_id"]],
            "remediation_state":"OPEN"
        })

    fields=["control_id","control_name","scope","disposition","current_status","missing_assertion","required_evidence","remediation_state"]
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rem)

    print(json.dumps({"remediation_count":len(rem)},indent=2))

if __name__=="__main__":main()
