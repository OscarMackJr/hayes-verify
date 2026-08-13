import argparse,csv,json,re,time
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--review-queue",required=True)
ap.add_argument("--repo-map",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--summary",required=True)
a=ap.parse_args()

queue=list(csv.DictReader(Path(a.review_queue).open(encoding="utf-8-sig",newline="")))
repo_map=json.loads(Path(a.repo_map).read_text(encoding="utf-8"))

IGNORE={".git",".venv","node_modules","dist","build","bin","obj",".terraform",".pytest_cache","coverage",".next",".idea",".vs","__pycache__"}
TEXT_EXT={".ps1",".py",".js",".ts",".tsx",".jsx",".cs",".rs",".json",".yaml",".yml",".tf",".tfvars",".bicep",".sql",".md",".xml",".toml",".ini",".cfg",".properties",".env",".txt"}
MAX_FILE=2_000_000

PATTERNS={
 "EMS-CTRL-041":[r"\.tf$",r"\.tfvars$",r"\.bicep$",r"cloudformation",r"pulumi",r"terraform"],
 "EMS-CTRL-042":[r"checkov",r"tfsec",r"terrascan",r"trivy",r"iac.*scan",r"terraform.*validate"],
 "EMS-CTRL-043":[r"\biam\b",r"service.?principal",r"managed.?identity",r"assume.?role",r"role",r"policy"],
 "EMS-CTRL-044":[r"key.?vault",r"secrets.?manager",r"vault",r"secret",r"credential",r"token"],
 "EMS-CTRL-045":[r"\btags?\b",r"\blabels?\b"],
 "EMS-CTRL-046":[r"backup",r"snapshot",r"dump",r"pg_dump"],
 "EMS-CTRL-047":[r"restore",r"recovery",r"disaster.?recovery",r"point.?in.?time"],
 "EMS-CTRL-048":[r"\bdev\b",r"\btest\b",r"\bstage\b",r"\bstaging\b",r"\bprod\b",r"workspace",r"environment"],
 "EMS-CTRL-061":[r"\.sql$",r"migration",r"alembic",r"flyway",r"liquibase",r"efcore",r"entityframework",r"schema"],
 "EMS-CTRL-062":[r"\.sql$",r"migration",r"schema",r"database.?project"],
 "EMS-CTRL-063":[r"data.?classification",r"customer.?data",r"confidential",r"restricted",r"\bpii\b"],
 "EMS-CTRL-064":[r"backup",r"snapshot",r"restore",r"pg_dump",r"database"],
 "EMS-CTRL-065":[r"retention",r"data.?retention",r"disposition",r"archive"]
}

compiled={cid:[re.compile(p,re.I|re.M) for p in pats] for cid,pats in PATTERNS.items()}

# Only scan controls that actually appear in the review queue for each repo.
repo_controls={}
for r in queue:
    repo_controls.setdefault(r["repository_name"],set()).add(r["control_id"])

def scan_repo(repo_name,path,control_ids):
    start=time.time()
    findings={cid:[] for cid in control_ids}
    inspected=0
    skipped=0
    if not path or not Path(path).exists():
        return {"exists":False,"files_inspected":0,"files_skipped":0,"elapsed_seconds":0.0,"findings":findings}

    root=Path(path)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORE for part in p.parts):
            continue
        try:
            size=p.stat().st_size
        except OSError:
            skipped+=1
            continue
        if size>MAX_FILE:
            skipped+=1
            continue

        inspected+=1
        rel=str(p.relative_to(root)).replace("\\","/")
        blob=rel.lower()

        if p.suffix.lower() in TEXT_EXT:
            try:
                blob += "\n" + p.read_text(encoding="utf-8",errors="ignore")[:200000].lower()
            except Exception:
                pass

        for cid in control_ids:
            if len(findings[cid])>=20:
                continue
            pats=compiled.get(cid,[])
            if any(rx.search(blob) for rx in pats):
                findings[cid].append(rel)

    elapsed=round(time.time()-start,2)
    return {"exists":True,"files_inspected":inspected,"files_skipped":skipped,"elapsed_seconds":elapsed,"findings":findings}

print("=== Scan repositories once ===", flush=True)
cache={}
repo_names=sorted(repo_controls)
for idx,repo in enumerate(repo_names,1):
    path=repo_map.get(repo,"")
    print(f"[{idx}/{len(repo_names)}] {repo}", flush=True)
    print(f"      Path: {path or '<NOT FOUND>'}", flush=True)
    result=scan_repo(repo,path,repo_controls[repo])
    cache[repo]=result
    obs=sum(len(v) for v in result["findings"].values())
    print(f"      Files inspected: {result['files_inspected']}", flush=True)
    print(f"      Files skipped:   {result['files_skipped']}", flush=True)
    print(f"      Observations:    {obs}", flush=True)
    print(f"      Complete:        {result['elapsed_seconds']}s", flush=True)

print("\n=== Evaluate applicability proposals ===", flush=True)
rows=[]
for idx,q in enumerate(queue,1):
    repo=q["repository_name"]
    cid=q["control_id"]
    cached=cache.get(repo,{"exists":False,"findings":{}})
    hits=cached.get("findings",{}).get(cid,[])

    if not cached.get("exists"):
        proposal="HUMAN_REVIEW_REQUIRED"
        confidence="LOW"
        rationale="Repository path was not found on disk; applicability cannot be derived from repository contents."
    elif hits:
        proposal="PROPOSE_APPLICABLE"
        confidence="HIGH" if len(hits)>=2 else "MEDIUM"
        rationale="Repository content contains evidence relevant to this control: " + "; ".join(hits[:5])
    else:
        proposal="HUMAN_REVIEW_REQUIRED"
        confidence="LOW"
        rationale="No repository-content evidence was detected; absence of evidence is not sufficient to conclude NOT_APPLICABLE."

    print(f"[{idx}/{len(queue)}] {cid} / {repo:<10} {proposal:<24} {confidence}", flush=True)

    rows.append({
        "wave":"2D",
        "control_id":cid,
        "control_name":q["control_name"],
        "target_id":q["target_id"],
        "repository_name":repo,
        "repository_path":repo_map.get(repo,""),
        "proposal":proposal,
        "confidence":confidence,
        "evidence_count":len(hits),
        "evidence_paths":";".join(hits[:20]),
        "proposed_rationale":rationale,
        "files_inspected":cached.get("files_inspected",0),
        "scan_elapsed_seconds":cached.get("elapsed_seconds",0),
        "evaluation_performed":"false",
        "promotion_performed":"false"
    })

out=Path(a.out)
out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader();w.writerows(rows)

summary={
    "wave":"2D",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "assessment_row_count":len(rows),
    "repository_count":len(repo_names),
    "propose_applicable_count":sum(r["proposal"]=="PROPOSE_APPLICABLE" for r in rows),
    "human_review_required_count":sum(r["proposal"]=="HUMAN_REVIEW_REQUIRED" for r in rows),
    "high_confidence_count":sum(r["confidence"]=="HIGH" for r in rows),
    "medium_confidence_count":sum(r["confidence"]=="MEDIUM" for r in rows),
    "low_confidence_count":sum(r["confidence"]=="LOW" for r in rows),
    "total_files_inspected":sum(v["files_inspected"] for v in cache.values()),
    "total_scan_seconds":round(sum(v["elapsed_seconds"] for v in cache.values()),2),
    "evaluation_performed":False,
    "promotion_performed":False
}
Path(a.summary).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print("\n=== Assessment summary ===", flush=True)
print(json.dumps(summary,indent=2), flush=True)
