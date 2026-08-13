import argparse,csv,json,sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--compliance",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.compliance).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    errors=[]
    for i,r in enumerate(rows,start=2):
        scope=r.get("inherited_from_scope","")
        istat=r.get("inheritance_status","")
        eff=r.get("effective_status","")
        inherited=r.get("inherited_control_status","")
        reason=r.get("inheritance_reason","")

        if scope in {"EMS","ORGANIZATION"}:
            if reason=="HIGHER_SCOPE_PASS":
                if not (istat=="INHERITED" and eff=="INHERITED" and inherited=="PASS"):
                    errors.append(f"Line {i}: invalid PASS inheritance state")
            elif reason=="HIGHER_SCOPE_WARNING":
                if eff!="WARNING": errors.append(f"Line {i}: WARNING not propagated")
            elif reason=="HIGHER_SCOPE_FAIL":
                if eff!="FAIL": errors.append(f"Line {i}: FAIL not propagated")
            elif reason=="HIGHER_SCOPE_EVIDENCE_MISSING":
                if eff!="NOT_EVALUATED": errors.append(f"Line {i}: missing evidence must remain NOT_EVALUATED")

    result={
        "status":"PASS" if not errors else "FAIL",
        "row_count":len(rows),
        "errors":errors
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":main()
