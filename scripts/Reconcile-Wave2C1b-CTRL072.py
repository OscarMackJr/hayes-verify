import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
outdir=Path(a.outdir).resolve()
outdir.mkdir(parents=True,exist_ok=True)

paths=spec["source_artifacts"]
manifest_path=root/paths["generation_manifest"]
validation_path=root/paths["output_validation"]
provenance_path=root/paths["provenance"]
output_root=root/paths["output_root"]

missing=[]
for p in (manifest_path,validation_path,provenance_path):
    if not p.exists():
        missing.append(str(p))
if missing:
    raise SystemExit(f"Missing Wave 2C.1a evidence artifacts: {missing}")

manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
validation=json.loads(validation_path.read_text(encoding="utf-8"))
with provenance_path.open(encoding="utf-8-sig",newline="") as f:
    provenance=list(csv.DictReader(f))

records=manifest.get("records",[])

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

docx_files=sorted(output_root.glob("*.docx")) if output_root.exists() else []
pdf_files=sorted(output_root.glob("*.pdf")) if output_root.exists() else []

path_errors=[]
hash_errors=[]

for r in records:
    for key in ("docx_path","pdf_path"):
        p=root/r.get(key,"")
        if not p.exists():
            path_errors.append(f"{r.get('source_path')}: missing {key} => {p}")
    docx=root/r.get("docx_path","")
    pdf=root/r.get("pdf_path","")
    if docx.exists() and r.get("docx_sha256"):
        actual=sha256(docx)
        if actual.lower()!=r["docx_sha256"].lower():
            hash_errors.append(f"{r.get('source_path')}: DOCX SHA-256 mismatch")
    if pdf.exists() and r.get("pdf_sha256"):
        actual=sha256(pdf)
        if actual.lower()!=r["pdf_sha256"].lower():
            hash_errors.append(f"{r.get('source_path')}: PDF SHA-256 mismatch")

manifest_keys={
    (r.get("source_path",""),r.get("docx_path",""),r.get("pdf_path",""))
    for r in records
}
provenance_keys={
    (r.get("source_path",""),r.get("docx_path",""),r.get("pdf_path",""))
    for r in provenance
}

assertions={
    "generation_manifest_pass":{
        "result":"PASS" if manifest.get("status")=="PASS" else "FAIL",
        "detail":f"manifest_status={manifest.get('status')}"
    },
    "output_validation_pass":{
        "result":"PASS" if validation.get("status")=="PASS" else "FAIL",
        "detail":f"validation_status={validation.get('status')}"
    },
    "source_count_equals_record_count":{
        "result":"PASS" if manifest.get("source_count")==manifest.get("record_count") and manifest.get("source_count",0)>0 else "FAIL",
        "detail":f"source_count={manifest.get('source_count')} record_count={manifest.get('record_count')}"
    },
    "exact_docx_count_matches_source_count":{
        "result":"PASS" if len(docx_files)==manifest.get("source_count") else "FAIL",
        "detail":f"docx_count={len(docx_files)} source_count={manifest.get('source_count')}"
    },
    "exact_pdf_count_matches_source_count":{
        "result":"PASS" if len(pdf_files)==manifest.get("source_count") else "FAIL",
        "detail":f"pdf_count={len(pdf_files)} source_count={manifest.get('source_count')}"
    },
    "all_source_hashes_present":{
        "result":"PASS" if records and all(r.get("source_sha256") for r in records) else "FAIL",
        "detail":f"{sum(1 for r in records if r.get('source_sha256'))}/{len(records)} source hashes present"
    },
    "all_docx_hashes_present":{
        "result":"PASS" if records and all(r.get("docx_sha256") for r in records) else "FAIL",
        "detail":f"{sum(1 for r in records if r.get('docx_sha256'))}/{len(records)} DOCX hashes present"
    },
    "all_pdf_hashes_present":{
        "result":"PASS" if records and all(r.get("pdf_sha256") for r in records) else "FAIL",
        "detail":f"{sum(1 for r in records if r.get('pdf_sha256'))}/{len(records)} PDF hashes present"
    },
    "all_generator_identities_present":{
        "result":"PASS" if records and all(r.get("generator") for r in records) else "FAIL",
        "detail":f"{sum(1 for r in records if r.get('generator'))}/{len(records)} generator identities present"
    },
    "all_generation_timestamps_present":{
        "result":"PASS" if records and all(r.get("generated_at_utc") for r in records) else "FAIL",
        "detail":f"{sum(1 for r in records if r.get('generated_at_utc'))}/{len(records)} timestamps present"
    },
    "all_manifest_paths_exist":{
        "result":"PASS" if not path_errors else "FAIL",
        "detail":"all manifest output paths exist" if not path_errors else "; ".join(path_errors)
    },
    "all_current_hashes_match_manifest":{
        "result":"PASS" if not hash_errors else "FAIL",
        "detail":"all current output hashes match manifest" if not hash_errors else "; ".join(hash_errors)
    },
    "provenance_rows_match_manifest_records":{
        "result":"PASS" if len(provenance)==len(records) and provenance_keys==manifest_keys else "FAIL",
        "detail":f"provenance_rows={len(provenance)} manifest_records={len(records)} keys_match={provenance_keys==manifest_keys}"
    },
    "promotion_performed_false":{
        "result":"PASS" if validation.get("promotion_performed") is False else "FAIL",
        "detail":f"promotion_performed={validation.get('promotion_performed')}"
    }
}

all_pass=all(v["result"]=="PASS" for v in assertions.values())

evidence={
    "wave":"2C.1b",
    "control_id":"EMS-CTRL-072",
    "control_name":"PDF/DOCX Generation Validation",
    "status":"PASS" if all_pass else "WARNING",
    "sufficiency":"SUFFICIENT" if all_pass else "INSUFFICIENT",
    "promotion_eligible":bool(all_pass),
    "promotion_status":"QUALIFIED_NOT_PROMOTED" if all_pass else "NOT_PROMOTED",
    "remediation_state":"OPEN",
    "promotion_performed":False,
    "reconciled_at":datetime.now(timezone.utc).isoformat(),
    "assertions":assertions,
    "evidence_summary":{
        "source_count":manifest.get("source_count",0),
        "record_count":manifest.get("record_count",0),
        "docx_count":len(docx_files),
        "pdf_count":len(pdf_files),
        "provenance_row_count":len(provenance),
        "generation_manifest":str(manifest_path),
        "output_validation":str(validation_path),
        "provenance":str(provenance_path),
        "output_root":str(output_root)
    }
}

(outdir/"ctrl072_reconciliation_evidence.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")

with (outdir/"assertions.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["control_id","assertion","result","detail"])
    w.writeheader()
    for name,v in assertions.items():
        w.writerow({
            "control_id":"EMS-CTRL-072",
            "assertion":name,
            "result":v["result"],
            "detail":v["detail"]
        })

summary={
    "control_id":"EMS-CTRL-072",
    "status":evidence["status"],
    "sufficiency":evidence["sufficiency"],
    "promotion_eligible":evidence["promotion_eligible"],
    "promotion_status":evidence["promotion_status"],
    "remediation_state":evidence["remediation_state"],
    "promotion_performed":False,
    "source_count":evidence["evidence_summary"]["source_count"],
    "docx_count":evidence["evidence_summary"]["docx_count"],
    "pdf_count":evidence["evidence_summary"]["pdf_count"],
    "failed_assertion_count":sum(1 for v in assertions.values() if v["result"]!="PASS")
}
(outdir/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

print(json.dumps(summary,indent=2))
