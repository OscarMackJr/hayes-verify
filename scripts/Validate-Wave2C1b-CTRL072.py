import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--evidence",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

e=json.loads(Path(a.evidence).read_text(encoding="utf-8"))
errors=[]

required_assertions=[
    "generation_manifest_pass",
    "output_validation_pass",
    "source_count_equals_record_count",
    "exact_docx_count_matches_source_count",
    "exact_pdf_count_matches_source_count",
    "all_source_hashes_present",
    "all_docx_hashes_present",
    "all_pdf_hashes_present",
    "all_generator_identities_present",
    "all_generation_timestamps_present",
    "all_manifest_paths_exist",
    "all_current_hashes_match_manifest",
    "provenance_rows_match_manifest_records",
    "promotion_performed_false"
]

assertions=e.get("assertions",{})
for name in required_assertions:
    if name not in assertions:
        errors.append(f"Missing assertion: {name}")

all_pass=all(assertions.get(name,{}).get("result")=="PASS" for name in required_assertions)

if e.get("promotion_performed") is not False:
    errors.append("promotion_performed must be false.")
if e.get("remediation_state")!="OPEN":
    errors.append("remediation_state must remain OPEN before explicit promotion.")
if e.get("promotion_eligible") and not all_pass:
    errors.append("promotion_eligible true without all required assertions PASS.")
if e.get("status")=="PASS" and not all_pass:
    errors.append("PASS without all required assertions PASS.")
if e.get("promotion_status")=="QUALIFIED_NOT_PROMOTED" and not e.get("promotion_eligible"):
    errors.append("QUALIFIED_NOT_PROMOTED requires promotion_eligible=true.")

result={
    "status":"PASS" if not errors else "FAIL",
    "control_id":"EMS-CTRL-072",
    "promotion_eligible":bool(e.get("promotion_eligible")),
    "promotion_status":e.get("promotion_status"),
    "remediation_state":e.get("remediation_state"),
    "promotion_performed":False,
    "errors":errors
}

Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
