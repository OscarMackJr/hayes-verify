import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

report=json.loads((root/spec["adjudication_report"]).read_text(encoding="utf-8"))
scope=json.loads((root/spec["scope_file"]).read_text(encoding="utf-8"))
population=json.loads((root/spec["population_file"]).read_text(encoding="utf-8"))

errors=[]
if report.get("status")!="PASS": errors.append("adjudication report is not PASS")
if int(report.get("review_required_count",-1))!=0: errors.append("REVIEW_REQUIRED rows remain")
if int(report.get("undecided_count",-1))!=0: errors.append("UNDECIDED rows remain")
if int(report.get("included_control_count",-1))!=spec["expected_control_count"]: errors.append("included control count mismatch")
if int(report.get("included_target_count",-1))!=spec["expected_target_count"]: errors.append("included target count mismatch")
if scope.get("status")!="PASS": errors.append("scope.json is not PASS")
if population.get("status")!="PASS": errors.append("population.json is not PASS")
if int(scope.get("scope_count",-1))!=spec["expected_control_count"]: errors.append("scope_count mismatch")
if int(population.get("population_count",-1))!=spec["expected_target_count"]: errors.append("population_count mismatch")
if report.get("evaluation_performed") is not False: errors.append("evaluation_performed must be false")
if report.get("promotion_performed") is not False: errors.append("promotion_performed must be false")

if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

control_dec=root/spec["control_decisions"]
target_dec=root/spec["target_decisions"]

scope_freeze={
    "wave":"2D",
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "control_count":spec["expected_control_count"],
    "scope_sha256":sha256(root/spec["scope_file"]),
    "control_decisions_sha256":sha256(control_dec),
    "adjudication_report_sha256":sha256(root/spec["adjudication_report"]),
    "evaluation_performed":False,
    "promotion_performed":False
}
sf=root/spec["scope_freeze"]
sf.parent.mkdir(parents=True,exist_ok=True)
sf.write_text(json.dumps(scope_freeze,indent=2),encoding="utf-8")

population_freeze={
    "wave":"2D",
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "target_count":spec["expected_target_count"],
    "population_sha256":sha256(root/spec["population_file"]),
    "target_decisions_sha256":sha256(target_dec),
    "evaluation_performed":False,
    "promotion_performed":False
}
pf=root/spec["population_freeze"]
pf.write_text(json.dumps(population_freeze,indent=2),encoding="utf-8")

print(json.dumps({
    "status":"PASS",
    "scope_freeze":str(sf),
    "population_freeze":str(pf),
    "control_count":spec["expected_control_count"],
    "target_count":spec["expected_target_count"],
    "evaluation_performed":False,
    "promotion_performed":False
},indent=2))
