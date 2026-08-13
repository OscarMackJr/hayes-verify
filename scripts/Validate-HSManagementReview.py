import argparse,json,sys
from pathlib import Path
EXPECTED={"EMS-CTRL-073","EMS-CTRL-074","EMS-CTRL-077","EMS-CTRL-078","EMS-CTRL-080"}
ap=argparse.ArgumentParser();ap.add_argument("--envelopes",required=True);ap.add_argument("--report",required=True);a=ap.parse_args()
rows=[json.loads(x) for x in Path(a.envelopes).read_text(encoding="utf-8").splitlines() if x.strip()]
errors=[];ids={r["control_id"] for r in rows}
if ids!=EXPECTED:errors.append(f"Expected {sorted(EXPECTED)}, found {sorted(ids)}")
for r in rows:
    if r["collector_id"]!="HS-MANAGEMENT-REVIEW":errors.append(f"{r['control_id']}: wrong collector")
    if r["evidence_class"]!="OPERATING_EVIDENCE":errors.append(f"{r['control_id']}: wrong evidence class")
    if r["status"]=="PASS" and not all(v["result"]=="PASS" for v in r["assertions"].values()):errors.append(f"{r['control_id']}: PASS without all assertions PASS")
res={"status":"PASS" if not errors else "FAIL","envelope_count":len(rows),"promotion_candidate_count":sum(bool(r["promotion_candidate"]) for r in rows),"errors":errors}
Path(a.report).write_text(json.dumps(res,indent=2),encoding="utf-8");print(json.dumps(res,indent=2));sys.exit(1 if errors else 0)
