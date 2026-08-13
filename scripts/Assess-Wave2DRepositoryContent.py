import argparse,csv,json,re
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
IGNORE={".git",".venv","node_modules","dist","build","bin","obj",".terraform",".pytest_cache","coverage",".next"}
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
TEXT_EXT={".ps1",".py",".js",".ts",".tsx",".jsx",".cs",".rs",".json",".yaml",".yml",".tf",".tfvars",".bicep",".sql",".md",".xml",".toml",".ini",".cfg",".properties"}
def scan(path,cid):
    if not path or not Path(path).exists(): return [],False
    hits=[]
    pats=PATTERNS.get(cid,[])
    root=Path(path)
    for p in root.rglob("*"):
        if not p.is_file() or any(part in IGNORE for part in p.parts): continue
        try:
            if p.stat().st_size>2_000_000: continue
        except OSError: continue
        rel=str(p.relative_to(root)).replace("\\","/")
        blob=rel.lower()
        if p.suffix.lower() in TEXT_EXT:
            try: blob+="\n"+p.read_text(encoding="utf-8",errors="ignore")[:200000].lower()
            except Exception: pass
        if any(re.search(pt,blob,re.I|re.M) for pt in pats):
            hits.append(rel)
            if len(hits)>=20: break
    return hits,True
rows=[]
for q in queue:
    path=repo_map.get(q["repository_name"],"")
    hits,exists=scan(path,q["control_id"])
    if not exists:
        proposal="HUMAN_REVIEW_REQUIRED";confidence="LOW"
        rationale="Repository path was not found on disk; applicability cannot be derived from repository contents."
    elif hits:
        proposal="PROPOSE_APPLICABLE";confidence="HIGH" if len(hits)>=2 else "MEDIUM"
        rationale="Repository content contains evidence relevant to this control: "+"; ".join(hits[:5])
    else:
        proposal="HUMAN_REVIEW_REQUIRED";confidence="LOW"
        rationale="No repository-content evidence was detected; absence of evidence is not sufficient to conclude NOT_APPLICABLE."
    rows.append({
        "wave":"2D","control_id":q["control_id"],"control_name":q["control_name"],
        "target_id":q["target_id"],"repository_name":q["repository_name"],
        "repository_path":path,"proposal":proposal,"confidence":confidence,
        "evidence_count":len(hits),"evidence_paths":";".join(hits[:20]),
        "proposed_rationale":rationale,"evaluation_performed":"false","promotion_performed":"false"
    })
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
summary={
 "wave":"2D","generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS",
 "assessment_row_count":len(rows),
 "propose_applicable_count":sum(r["proposal"]=="PROPOSE_APPLICABLE" for r in rows),
 "human_review_required_count":sum(r["proposal"]=="HUMAN_REVIEW_REQUIRED" for r in rows),
 "high_confidence_count":sum(r["confidence"]=="HIGH" for r in rows),
 "medium_confidence_count":sum(r["confidence"]=="MEDIUM" for r in rows),
 "low_confidence_count":sum(r["confidence"]=="LOW" for r in rows),
 "evaluation_performed":False,"promotion_performed":False
}
Path(a.summary).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
