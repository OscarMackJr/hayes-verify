import argparse,json,subprocess,sys,hashlib,os
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
out=Path(a.outdir).resolve()
out.mkdir(parents=True,exist_ok=True)

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

# Discover likely controlled source documents and generation tooling.
source_exts={".md",".docx",".yaml",".yml",".json"}
source_roots=[root/"docs",root/"controlled",root/"source",root/"streams"]
sources=[]
for base in source_roots:
    if not base.exists(): continue
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in source_exts:
            sources.append(p)

tool_candidates=[]
for p in (root/"scripts").glob("*"):
    if p.is_file() and any(k in p.name.lower() for k in ["build","generate","document","docx","pdf"]):
        tool_candidates.append(p)

# Prefer known build scripts if present.
preferred=[
    root/"scripts"/"Build-EMS.ps1",
    root/"scripts"/"Build-ControlledDocuments.ps1",
    root/"scripts"/"Generate-ControlledDocuments.ps1"
]
runner=None
for p in preferred:
    if p.exists():
        runner=p;break

execution={
    "attempted":False,
    "runner":str(runner) if runner else "",
    "exit_code":None,
    "stdout":"",
    "stderr":""
}

if runner:
    execution["attempted"]=True
    try:
        if runner.suffix.lower()==".ps1":
            cp=subprocess.run(
                ["pwsh","-NoProfile","-ExecutionPolicy","Bypass","-File",str(runner)],
                cwd=str(root),capture_output=True,text=True
            )
        else:
            cp=subprocess.run([sys.executable,str(runner)],cwd=str(root),capture_output=True,text=True)
        execution["exit_code"]=cp.returncode
        execution["stdout"]=cp.stdout[-12000:]
        execution["stderr"]=cp.stderr[-12000:]
    except Exception as e:
        execution["exit_code"]=-1
        execution["stderr"]=repr(e)

# Detect produced outputs. Exclude venvs and generated evidence folders.
docx=[]; pdf=[]
for p in root.rglob("*"):
    if not p.is_file(): continue
    parts={x.lower() for x in p.parts}
    if ".venv" in parts or "site-packages" in parts: continue
    if p.suffix.lower()==".docx": docx.append(p)
    elif p.suffix.lower()==".pdf": pdf.append(p)

outputs=[]
for fmt,arr in [("DOCX",docx),("PDF",pdf)]:
    for p in arr:
        try:
            size=p.stat().st_size
            outputs.append({
                "format":fmt,
                "path":str(p),
                "size_bytes":size,
                "sha256":sha256(p) if size>0 else "",
                "mtime_utc":datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()
            })
        except Exception:
            pass

assertions={
    "controlled_sources_discovered":{
        "result":"PASS" if sources else "FAIL",
        "detail":f"{len(sources)} controlled-source candidate(s) discovered."
    },
    "docx_output_detected":{
        "result":"PASS" if any(o["format"]=="DOCX" and o["size_bytes"]>0 for o in outputs) else "FAIL",
        "detail":f"{sum(1 for o in outputs if o['format']=='DOCX' and o['size_bytes']>0)} non-empty DOCX output(s)."
    },
    "pdf_output_detected":{
        "result":"PASS" if any(o["format"]=="PDF" and o["size_bytes"]>0 for o in outputs) else "FAIL",
        "detail":f"{sum(1 for o in outputs if o['format']=='PDF' and o['size_bytes']>0)} non-empty PDF output(s)."
    },
    "output_files_nonempty":{
        "result":"PASS" if outputs and all(o["size_bytes"]>0 for o in outputs) else "FAIL",
        "detail":f"{len(outputs)} output artifact(s) inspected."
    },
    "generation_provenance_retained":{
        "result":"PASS" if runner and execution["attempted"] else "FAIL",
        "detail":f"runner={execution['runner'] or 'NONE'}; exit_code={execution['exit_code']}"
    },
    "output_validation_retained":{
        "result":"PASS" if outputs and all(o["sha256"] for o in outputs if o["size_bytes"]>0) else "FAIL",
        "detail":"SHA-256 captured for detected outputs."
    }
}

all_pass=all(v["result"]=="PASS" for v in assertions.values())
status="PASS" if all_pass else "WARNING"
evidence={
    "wave":"2C.1",
    "control_id":"EMS-CTRL-072",
    "control_name":"PDF/DOCX Generation Validation",
    "status":status,
    "sufficiency":"SUFFICIENT" if all_pass else "INSUFFICIENT",
    "promotion_eligible":bool(all_pass),
    "promotion_performed":False,
    "collected_at":datetime.now(timezone.utc).isoformat(),
    "sources":[str(p) for p in sources[:500]],
    "tool_candidates":[str(p) for p in tool_candidates[:200]],
    "execution":execution,
    "assertions":assertions,
    "outputs":outputs
}
(out/"ctrl072_evidence.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")

with (out/"assertions.csv").open("w",encoding="utf-8",newline="") as f:
    import csv
    w=csv.DictWriter(f,fieldnames=["control_id","assertion","result","detail"])
    w.writeheader()
    for k,v in assertions.items():
        w.writerow({"control_id":"EMS-CTRL-072","assertion":k,"result":v["result"],"detail":v["detail"]})

summary={
    "control_id":"EMS-CTRL-072",
    "status":status,
    "promotion_eligible":bool(all_pass),
    "docx_count":sum(1 for o in outputs if o["format"]=="DOCX" and o["size_bytes"]>0),
    "pdf_count":sum(1 for o in outputs if o["format"]=="PDF" and o["size_bytes"]>0),
    "promotion_performed":False
}
(out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
