#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--qualification",required=True); ap.add_argument("--root",required=True); a=ap.parse_args()
envs={r["control_id"]:r for r in [json.loads(x) for x in Path(a.input).read_text(encoding="utf-8").splitlines() if x.strip()]}
with Path(a.qualification).open(encoding="utf-8") as f: quals=list(csv.DictReader(f))
promoted=[]; skipped=[]
for q in quals:
    cid=q["control_id"]; eligible=str(q["promotion_eligible"]).lower()=="true"
    if not eligible:
        skipped.append({"control_id":cid,"reason":"Not promotion eligible"}); continue
    e=envs[cid]
    dest=Path(a.root)/"evidence"/e["scope"].lower()/f"{cid}.yaml"
    dest.parent.mkdir(parents=True,exist_ok=True)
    # JSON is valid YAML 1.2 and avoids requiring PyYAML.
    dest.write_text(json.dumps(e,indent=2),encoding="utf-8")
    promoted.append({"control_id":cid,"scope":e["scope"],"destination":str(dest)})
print(json.dumps({"promoted_count":len(promoted),"skipped_count":len(skipped),"promoted":promoted,"skipped":skipped},indent=2))
