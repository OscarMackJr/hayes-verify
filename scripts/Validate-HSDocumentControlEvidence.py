import argparse,json,sys
from pathlib import Path

EXPECTED={"EMS-CTRL-001","EMS-CTRL-002","EMS-CTRL-008","EMS-CTRL-067","EMS-CTRL-068","EMS-CTRL-069","EMS-CTRL-070"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    rows=[]
    with Path(a.envelopes).open(encoding="utf-8") as fh:
        for line in fh:
            line=line.strip()
            if line: rows.append(json.loads(line))

    errors=[]
    ids={r.get("control_id") for r in rows}
    if ids!=EXPECTED:
        errors.append(f"Expected {sorted(EXPECTED)}, found {sorted(ids)}")

    for r in rows:
        if r.get("collector_id")!="HS-DOCUMENT-CONTROL":
            errors.append(f"{r.get('control_id')}: wrong collector_id")
        if r.get("evidence_class")!="OPERATING_EVIDENCE":
            errors.append(f"{r.get('control_id')}: wrong evidence_class")
        assertions=r.get("assertions") or {}
        if not assertions:
            errors.append(f"{r.get('control_id')}: assertions missing")
        if r.get("status")=="PASS" and not all(x.get("result")=="PASS" for x in assertions.values()):
            errors.append(f"{r.get('control_id')}: PASS without all assertions PASS")
        if r.get("promotion_candidate") and r.get("status")!="PASS":
            errors.append(f"{r.get('control_id')}: promotion_candidate requires PASS")

    result={
        "status":"PASS" if not errors else "FAIL",
        "envelope_count":len(rows),
        "promotion_candidate_count":sum(bool(r.get("promotion_candidate")) for r in rows),
        "errors":errors
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":main()
