import argparse,csv,json,re
from pathlib import Path
import yaml

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def load_scope_registry(path):
    d=yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return {
        c["control_id"]:c
        for c in d.get("controls",[])
        if c.get("scope") in {"EMS","ORGANIZATION"}
    }

def load_catalog(path):
    d=yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out={}
    def walk(x):
        if isinstance(x,dict):
            cid=x.get("control_id") or x.get("id")
            if isinstance(cid,str) and cid.startswith("EMS-CTRL-"):
                out[cid]=x
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(d)
    return out

def semantic_text(c):
    parts=[]
    for k in ("control_name","name","title","description","purpose","statement","requirement","objective"):
        v=c.get(k)
        if isinstance(v,str) and v.strip():
            parts.append(v)
    return norm(" ".join(parts))

def keyword_set(text):
    words=re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}",text.lower())
    stop={"control","must","shall","with","from","that","this","have","into","their","according","defined","approved","using"}
    return {w for w in words if w not in stop}

def file_relevance(text, sem_words, cid):
    low=text.lower()
    score=0.0
    matched=[]
    if cid.lower() in low:
        score+=0.45
        matched.append(cid)
    for w in sorted(sem_words, key=len, reverse=True)[:12]:
        if w in low:
            matched.append(w)
    unique=set(matched)
    semantic_matches=len([x for x in unique if x!=cid])
    score += min(0.35, semantic_matches*0.05)
    if "pass" in low or "approved" in low or "validated" in low or "baseline" in low:
        score+=0.05
    if "sha256" in low or "manifest" in low or "evidence" in low or "adjudication" in low:
        score+=0.05
    if "policy" in low or "review" in low or "governance" in low:
        score+=0.05
    return min(1.0,score), sorted(unique)

def source_bonus(path):
    p=str(path).lower()
    b=0.0
    if "\\releases\\" in p or "/releases/" in p or "\\release\\" in p: b+=0.10
    if "\\registry\\" in p or "/registry/" in p: b+=0.08
    if "\\docs\\" in p or "/docs/" in p: b+=0.05
    if "\\evidence\\" in p or "/evidence/" in p: b+=0.10
    if ".bak" in p or ".tmp" in p: b-=0.10
    return b

def infer_status(path,text,control):
    low=text.lower()
    # Conservative: never infer FAIL from mere mention.
    # PASS only when strong affirmative evidence language appears.
    affirmative = any(x in low for x in [
        "status: pass","status = pass","\"status\": \"pass\"",
        "validation passed","validated successfully","approved","baselined",
        "resolved_count","errors\": []","errors: []"
    ])
    warning = any(x in low for x in [
        "warning","policy_pending","not_evaluated","deferred","exception"
    ])
    if affirmative and not warning:
        return "PASS"
    if affirmative and warning:
        return "WARNING"
    return "NOT_EVALUATED"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ems-root",required=True)
    ap.add_argument("--scope-registry",required=True)
    ap.add_argument("--catalog",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    root=Path(a.ems_root)
    controls=load_scope_registry(a.scope_registry)
    catalog=load_catalog(a.catalog)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    prop=out/"proposed_evidence_records";prop.mkdir(parents=True,exist_ok=True)

    exts={".yaml",".yml",".json",".csv",".md",".txt",".ps1",".py"}
    candidates=[]

    files=[]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        low=str(p).lower()
        if "\\.venv\\" in low or "/.venv/" in low or "site-packages" in low or "__pycache__" in low:
            continue
        if "higher-scope-evidence\\proposed_evidence_records" in low.replace("/","\\"):
            continue
        files.append(p)

    for cid,scope_rec in controls.items():
        cat=catalog.get(cid,{})
        sem=semantic_text(cat) or scope_rec.get("control_name",cid)
        words=keyword_set(sem)
        rows=[]
        for p in files:
            try:
                text=p.read_text(encoding="utf-8",errors="replace")
            except Exception:
                continue
            score,matched=file_relevance(text,words,cid)
            score=min(1.0,score+source_bonus(p))
            if score < 0.25:
                continue
            status=infer_status(p,text,scope_rec)
            rows.append({
                "control_id":cid,
                "control_name":scope_rec.get("control_name",""),
                "scope":scope_rec["scope"],
                "candidate_status":status,
                "confidence":round(score,3),
                "source_file":str(p),
                "matched_terms":";".join(matched),
                "semantic_basis":sem[:800]
            })
        rows.sort(key=lambda x:(x["confidence"],x["candidate_status"]=="PASS"), reverse=True)
        if rows:
            best=rows[0]
            best["is_best_candidate"]=True
            candidates.extend(rows[:10])

            evidence = {
                "evidence_id": f"{scope_rec['scope']}-{cid}-DISCOVERED",
                "control_id": cid,
                "scope": scope_rec["scope"],
                "authority_id": "EMS-GOVERNANCE" if scope_rec["scope"]=="EMS" else "ENGINEERING-LEADERSHIP",
                "status": best["candidate_status"],
                "evidence_date": "2026-08-12",
                "expires_on": None,
                "evidence_summary": f"Discovered candidate evidence for {cid} from {best['source_file']}.",
                "evidence_references": [best["source_file"]],
                "notes": f"Discovery confidence={best['confidence']}; matched_terms={best['matched_terms']}"
            }
            (prop/f"{cid}.yaml").write_text(yaml.safe_dump(evidence,sort_keys=False),encoding="utf-8")

    # outputs
    fields=[
        "control_id","control_name","scope","candidate_status","confidence",
        "source_file","matched_terms","semantic_basis","is_best_candidate"
    ]
    with (out/"evidence_candidates.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields)
        w.writeheader()
        for r in candidates:
            r.setdefault("is_best_candidate",False)
            w.writerow(r)

    best_by={}
    for r in candidates:
        if r.get("is_best_candidate"):
            best_by[r["control_id"]]=r

    gaps=[]
    for cid,c in controls.items():
        b=best_by.get(cid)
        if not b or b["candidate_status"]=="NOT_EVALUATED":
            gaps.append({
                "control_id":cid,
                "control_name":c.get("control_name",""),
                "scope":c["scope"],
                "reason":"NO_HIGH_CONFIDENCE_AFFIRMATIVE_EVIDENCE" if b else "NO_CANDIDATE_EVIDENCE",
                "best_confidence":b["confidence"] if b else "",
                "best_source":b["source_file"] if b else ""
            })

    gfields=["control_id","control_name","scope","reason","best_confidence","best_source"]
    with (out/"evidence_gaps.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=gfields);w.writeheader();w.writerows(gaps)

    summary={
        "target_control_count":len(controls),
        "candidate_control_count":len(best_by),
        "proposed_pass_count":sum(1 for x in best_by.values() if x["candidate_status"]=="PASS"),
        "proposed_warning_count":sum(1 for x in best_by.values() if x["candidate_status"]=="WARNING"),
        "proposed_not_evaluated_count":sum(1 for x in best_by.values() if x["candidate_status"]=="NOT_EVALUATED"),
        "gap_count":len(gaps)
    }
    (out/"evidence_discovery_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
