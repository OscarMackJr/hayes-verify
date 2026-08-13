import argparse,csv,json,re
from pathlib import Path
import yaml

TARGETS={
"EMS-CTRL-001","EMS-CTRL-002","EMS-CTRL-003","EMS-CTRL-004","EMS-CTRL-005",
"EMS-CTRL-006","EMS-CTRL-007","EMS-CTRL-008","EMS-CTRL-016",
"EMS-CTRL-055","EMS-CTRL-056","EMS-CTRL-057","EMS-CTRL-058","EMS-CTRL-059","EMS-CTRL-060"
}

PLACEHOLDER_RE=re.compile(r"^Control\s+\d{3}$",re.I)

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def meaningful_name(s,cid):
    s=norm(s)
    if not s:return False
    if s==cid:return False
    if PLACEHOLDER_RE.match(s):return False
    return len(s)>=4

def score_candidate(name,desc,path,context):
    score=0.0
    p=str(path).lower()
    if meaningful_name(name,""):score+=0.45
    if desc and len(norm(desc))>=20:score+=0.25
    if "control_catalog" in p or "control_registry" in p:score+=0.15
    elif "\\registry\\" in p or "/registry/" in p:score+=0.10
    elif "\\docs\\" in p or "/docs/" in p:score+=0.05
    if "generated" in p:score-=0.05
    if context=="structured":score+=0.15
    return max(0.0,min(1.0,score))

def walk_structured(obj,path,found):
    if isinstance(obj,dict):
        cid=obj.get("control_id") or obj.get("id")
        if isinstance(cid,str) and cid in TARGETS:
            name=obj.get("control_name") or obj.get("name") or obj.get("title")
            desc=obj.get("description") or obj.get("purpose") or obj.get("statement") or obj.get("requirement") or obj.get("objective")
            if meaningful_name(name,cid) or desc:
                found.append({
                    "control_id":cid,
                    "recovered_name":norm(name),
                    "recovered_description":norm(desc),
                    "source_file":str(path),
                    "source_type":"structured"
                })
        for v in obj.values():
            walk_structured(v,path,found)
    elif isinstance(obj,list):
        for v in obj:
            walk_structured(v,path,found)

def extract_text(path,text,found):
    lines=text.splitlines()
    for i,line in enumerate(lines):
        ids=[cid for cid in TARGETS if cid in line]
        for cid in ids:
            window=lines[max(0,i-2):min(len(lines),i+5)]
            joined=" ".join(norm(x) for x in window if norm(x))
            # Common forms: EMS-CTRL-001, Name ; EMS-CTRL-001: Name ; | EMS-CTRL-001 | Name |
            m=re.search(re.escape(cid)+r"\s*[,|:\-]\s*([^|,\r\n]{4,120})",line)
            name=norm(m.group(1)) if m else ""
            if not meaningful_name(name,cid):
                # look ahead for heading-like name
                for w in window[1:]:
                    w=norm(w)
                    if w and cid not in w and len(w)<120 and not w.startswith(("{","[","- ")):
                        if not PLACEHOLDER_RE.match(w):
                            name=w
                            break
            desc=joined
            if meaningful_name(name,cid) or desc:
                found.append({
                    "control_id":cid,
                    "recovered_name":name,
                    "recovered_description":desc[:1200],
                    "source_file":str(path),
                    "source_type":"text"
                })

def load_existing_catalog(path):
    d=yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    controls=[]
    def walk(x):
        if isinstance(x,dict):
            cid=x.get("control_id") or x.get("id")
            if isinstance(cid,str) and cid.startswith("EMS-CTRL-"):
                controls.append(x)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(d)
    return d,{(c.get("control_id") or c.get("id")):c for c in controls}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--search-root",required=True)
    ap.add_argument("--catalog",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--min-confidence",type=float,default=0.90)
    a=ap.parse_args()

    root=Path(a.search_root)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    found=[]
    exts={".md",".txt",".json",".csv",".yaml",".yml"}

    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:continue
        low=str(p).lower()
        if "\\.venv\\" in low or "/.venv/" in low or "site-packages" in low or "__pycache__" in low:continue
        try:
            text=p.read_text(encoding="utf-8",errors="replace")
        except Exception:
            continue
        if not any(cid in text for cid in TARGETS):
            continue
        if p.suffix.lower() in {".yaml",".yml",".json"}:
            try:
                obj=json.loads(text) if p.suffix.lower()==".json" else yaml.safe_load(text)
                walk_structured(obj,p,found)
            except Exception:
                pass
        extract_text(p,text,found)

    # score + de-dupe
    candidates=[]
    seen=set()
    for x in found:
        key=(x["control_id"],x["recovered_name"],x["recovered_description"],x["source_file"])
        if key in seen:continue
        seen.add(key)
        x["confidence"]=score_candidate(x["recovered_name"],x["recovered_description"],x["source_file"],x["source_type"])
        candidates.append(x)

    best={}
    for cid in TARGETS:
        rows=[x for x in candidates if x["control_id"]==cid]
        rows.sort(key=lambda x:(x["confidence"],len(x["recovered_description"]),len(x["recovered_name"])),reverse=True)
        if rows:best[cid]=rows[0]

    _, cmap=load_existing_catalog(a.catalog)

    recovered=[]
    unresolved=[]
    for cid in sorted(TARGETS):
        b=best.get(cid)
        if not b:
            unresolved.append({"control_id":cid,"reason":"No candidate definition found"})
            continue
        auto=(b["confidence"]>=a.min_confidence and meaningful_name(b["recovered_name"],cid))
        row={**b,"auto_apply":auto}
        recovered.append(row)
        if not auto:
            unresolved.append({
                "control_id":cid,
                "reason":"Best candidate below auto-apply confidence threshold or name still not meaningful",
                "best_name":b["recovered_name"],
                "confidence":b["confidence"],
                "source_file":b["source_file"]
            })

    # write outputs
    fields=["control_id","recovered_name","recovered_description","source_file","source_type","confidence","auto_apply"]
    with (out/"recovered_control_definitions.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(recovered)

    ufields=sorted({k for r in unresolved for k in r.keys()}) if unresolved else ["control_id","reason"]
    with (out/"unresolved_control_definitions.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=ufields);w.writeheader();w.writerows(unresolved)

    (out/"recovery_sources.json").write_text(json.dumps(candidates,indent=2),encoding="utf-8")

    summary={
        "target_count":len(TARGETS),
        "candidate_count":len(candidates),
        "best_match_count":len(best),
        "auto_apply_count":sum(1 for r in recovered if r["auto_apply"]),
        "unresolved_count":len(unresolved)
    }
    (out/"recovery_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
