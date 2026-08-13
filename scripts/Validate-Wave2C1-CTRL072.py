import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("--evidence",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()
e=json.loads(Path(a.evidence).read_text(encoding="utf-8"))
errors=[]
required=["controlled_sources_discovered","docx_output_detected","pdf_output_detected","output_files_nonempty","generation_provenance_retained","output_validation_retained"]
for k in required:
    if k not in e.get("assertions",{}): errors.append(f"Missing assertion: {k}")
if e.get("promotion_performed") is not False: errors.append("promotion_performed must remain false.")
eligible=e.get("promotion_eligible") is True
all_pass=all(e["assertions"].get(k,{}).get("result")=="PASS" for k in required)
if eligible and not all_pass: errors.append("promotion_eligible true without all required assertions PASS.")
if e.get("status")=="PASS" and not all_pass: errors.append("PASS without all required assertions PASS.")
result={"status":"PASS" if not errors else "FAIL","errors":errors,"promotion_eligible":eligible,"promotion_performed":False}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
