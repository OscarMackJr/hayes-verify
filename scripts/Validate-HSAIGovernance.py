#!/usr/bin/env python3
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); a=ap.parse_args()
rows=[json.loads(x) for x in Path(a.input).read_text(encoding="utf-8").splitlines() if x.strip()]
errors=[]
expected={"EMS-CTRL-007","EMS-CTRL-049","EMS-CTRL-050","EMS-CTRL-052","EMS-CTRL-053","EMS-CTRL-054"}
seen={r.get("control_id") for r in rows}
if seen != expected: errors.append(f"Control set mismatch: expected={sorted(expected)} actual={sorted(seen)}")
for r in rows:
    for k in ("collector_id","collector_version","control_id","control_name","scope","collector_status","assertions","promotion_candidate"):
        if k not in r: errors.append(f"{r.get('control_id','?')}: missing {k}")
    if r.get("collector_status")=="PASS" and not all(v.get("result")=="PASS" for v in r.get("assertions",{}).values()):
        errors.append(f"{r.get('control_id')}: PASS without all assertions PASS")
    if r.get("promotion_candidate") and r.get("collector_status")!="PASS":
        errors.append(f"{r.get('control_id')}: promotion candidate without PASS")
out={"status":"PASS" if not errors else "FAIL","envelope_count":len(rows),
     "promotion_candidate_count":sum(1 for r in rows if r.get("promotion_candidate")),"errors":errors}
print(json.dumps(out,indent=2))
raise SystemExit(0 if not errors else 1)
