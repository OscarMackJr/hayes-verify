import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path,rows,fields):
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def val(r,*names):
    for n in names:
        if n in r and r[n] not in (None,""):
            return str(r[n])
    return ""

def load_higher_scope_results(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(obj,list):
        rows=obj
    elif isinstance(obj,dict):
        for key in ("results","controls","higher_scope_results","items"):
            if isinstance(obj.get(key),list):
                rows=obj[key]
                break
        else:
            rows=[]
    else:
        rows=[]

    normalized=[]
    for r in rows:
        cid=val(r,"control_id")
        if not cid:
            continue
        normalized.append({
            "control_id":cid,
            "control_name":val(r,"control_name"),
            "scope":val(r,"scope").upper(),
            "status":val(r,"status","compliance_status","effective_status").upper(),
            "reason":val(r,"reason"),
            "assertions":r.get("assertions")
        })
    return normalized

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ems-root",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    root=Path(a.ems_root).resolve()
    out=Path(a.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

    scope_file=root/"registry"/"control_scope_registry.yaml"
    compliance_file=root/"generated"/"wave2"/"inheritance"/"effective_compliance_with_inheritance.csv"
    impact_file=root/"generated"/"wave2"/"inheritance"/"inheritance_impact_report.json"
    hs_results_file=root/"generated"/"wave2"/"inheritance"/"higher_scope_results.json"

    for p in (scope_file,compliance_file,impact_file,hs_results_file):
        if not p.exists():
            raise SystemExit(f"Required Wave 2B artifact missing: {p}")

    # Scope registry validation.
    text=scope_file.read_text(encoding="utf-8",errors="ignore")
    scope_rows=[]
    current={}
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("- control_id:"):
            if current:
                scope_rows.append(current)
            current={"control_id":line.split(":",1)[1].strip().strip('"').strip("'")}
        elif line.startswith("control_id:") and not current.get("control_id"):
            current["control_id"]=line.split(":",1)[1].strip().strip('"').strip("'")
        elif line.startswith("control_name:"):
            current["control_name"]=line.split(":",1)[1].strip().strip('"').strip("'")
        elif line.startswith("scope:"):
            current["scope"]=line.split(":",1)[1].strip().strip('"').strip("'")
    if current:
        scope_rows.append(current)

    scope_map={r.get("control_id"):r for r in scope_rows if r.get("control_id")}
    scope_errors=[]
    if len(scope_map)!=80:
        scope_errors.append(f"Expected 80 controls; found {len(scope_map)}.")
    for cid,r in scope_map.items():
        if not str(r.get("scope","")).strip():
            scope_errors.append(f"{cid}: missing scope.")

    scope_validation={
        "status":"PASS" if not scope_errors else "FAIL",
        "control_count":len(scope_map),
        "errors":scope_errors
    }
    (out/"scope_registry_validation.json").write_text(json.dumps(scope_validation,indent=2),encoding="utf-8")

    impact=json.loads(impact_file.read_text(encoding="utf-8"))
    expected_unresolved=int(impact.get("unresolved_higher_scope_count",0))
    hs_results=load_higher_scope_results(hs_results_file)

    if not hs_results:
        raise SystemExit("higher_scope_results.json contained no recognizable control results.")

    # Explicit controlled remediation sources.
    remediation_files=[
        root/"generated"/"wave2"/"higher-scope-remediation.csv",
        root/"generated"/"wave2"/"higher-scope-collectors"/"ai-governance-gap-remediation"/"remediation_queue.csv",
        root/"generated"/"wave2"/"higher-scope-collectors"/"security-data-governance-closeout"/"open_remediation.csv",
        root/"generated"/"wave2"/"higher-scope-collectors"/"security-data-governance"/"remediation_queue.csv",
        root/"generated"/"wave2"/"higher-scope-collectors"/"management-review-qualified"/"management_review_gaps.csv",
    ]

    remediation=[]
    remediation_controls=set()
    for p in remediation_files:
        if not p.exists():
            continue
        try:
            rows=read_csv(p)
        except Exception:
            continue
        for r in rows:
            cid=val(r,"control_id").strip()
            if not cid:
                continue
            remediation_controls.add(cid)
            remediation.append({
                "control_id":cid,
                "control_name":val(r,"control_name"),
                "scope":val(r,"scope"),
                "disposition":val(r,"disposition") or "REMEDIATE",
                "current_status":val(r,"current_status","status") or "WARNING",
                "missing_assertions":val(r,"missing_assertions","missing_assertion"),
                "required_evidence":val(r,"required_evidence"),
                "remediation_state":val(r,"remediation_state") or "OPEN",
                "source_file":str(p)
            })

    # Authoritative Wave 2B control population comes ONLY from higher_scope_results.json.
    control_reconciliation=[]
    satisfied_controls=[]
    remediated_controls=[]
    undispositioned_controls=[]

    for r in hs_results:
        cid=r["control_id"]
        st=r["status"]

        if st=="PASS":
            disp="SATISFIED"
            satisfied_controls.append(cid)
        elif cid in remediation_controls:
            disp="CONTROLLED_REMEDIATION"
            remediated_controls.append(cid)
        else:
            disp="UNDISPOSITIONED"
            undispositioned_controls.append(cid)

        control_reconciliation.append({
            "control_id":cid,
            "control_name":r["control_name"] or scope_map.get(cid,{}).get("control_name",""),
            "scope":r["scope"] or str(scope_map.get(cid,{}).get("scope","")).upper(),
            "higher_scope_status":st,
            "reason":r["reason"],
            "closeout_disposition":disp
        })

    write_csv(
        out/"higher_scope_control_reconciliation.csv",
        control_reconciliation,
        ["control_id","control_name","scope","higher_scope_status","reason","closeout_disposition"]
    )

    # Repository reconciliation is now informational only.
    compliance=read_csv(compliance_file)
    authoritative_ids={r["control_id"] for r in hs_results}
    repo_rows=[]
    for r in compliance:
        cid=val(r,"control_id")
        if cid not in authoritative_ids:
            continue
        reason=val(r,"reason","inheritance_reason")
        status=val(r,"compliance_status","effective_status","status")
        if reason=="HIGHER_SCOPE_PASS" or status in {"INHERITED","PASS"}:
            disp="SATISFIED"
        elif cid in remediation_controls:
            disp="CONTROLLED_REMEDIATION"
        else:
            disp="UNDISPOSITIONED"
        repo_rows.append({
            "repository_name":val(r,"repository_name","repository"),
            "control_id":cid,
            "control_name":val(r,"control_name"),
            "status":status,
            "reason":reason,
            "closeout_disposition":disp
        })

    write_csv(
        out/"higher_scope_repository_reconciliation.csv",
        repo_rows,
        ["repository_name","control_id","control_name","status","reason","closeout_disposition"]
    )

    write_csv(
        out/"open_remediation.csv",
        remediation,
        ["control_id","control_name","scope","disposition","current_status",
         "missing_assertions","required_evidence","remediation_state","source_file"]
    )

    undispositioned_rows=[r for r in repo_rows if r["closeout_disposition"]=="UNDISPOSITIONED"]
    write_csv(
        out/"undispositioned_rows.csv",
        undispositioned_rows,
        ["repository_name","control_id","control_name","status","reason","closeout_disposition"]
    )

    # True unresolved repository-row population is authoritative impact count.
    controlled_repo_rows=[r for r in repo_rows if r["closeout_disposition"]=="CONTROLLED_REMEDIATION"]
    count_matches=(len(controlled_repo_rows)==expected_unresolved)

    certification={
        "wave":"2B",
        "certified_at":datetime.now(timezone.utc).isoformat(),
        "scope_registry_status":scope_validation["status"],
        "scope_control_count":len(scope_map),
        "higher_scope_authority":{
            "source":str(hs_results_file),
            "control_count":len(hs_results),
            "pass_control_count":len(set(satisfied_controls)),
            "controlled_remediation_control_count":len(set(remediated_controls)),
            "undispositioned_control_count":len(set(undispositioned_controls))
        },
        "inheritance_authority":{
            "row_count":impact.get("row_count"),
            "changed_count":impact.get("changed_count"),
            "inherited_count":impact.get("inherited_count"),
            "unresolved_higher_scope_count":expected_unresolved
        },
        "repository_reconciliation":{
            "authoritative_population_row_count":len(repo_rows),
            "satisfied_row_count":sum(1 for r in repo_rows if r["closeout_disposition"]=="SATISFIED"),
            "controlled_remediation_row_count":len(controlled_repo_rows),
            "undispositioned_row_count":len(undispositioned_rows),
            "authoritative_unresolved_count_matches":count_matches
        },
        "open_remediation_control_count":len(remediation_controls),
        "open_remediation_controls":sorted(remediation_controls)
    }

    failures=[]
    if scope_validation["status"]!="PASS":
        failures.append("SCOPE_REGISTRY_VALIDATION_FAILED")
    if undispositioned_controls:
        failures.append("UNDISPOSITIONED_HIGHER_SCOPE_CONTROLS")
    if undispositioned_rows:
        failures.append("UNDISPOSITIONED_HIGHER_SCOPE_ROWS")
    if not count_matches:
        failures.append(
            f"UNRESOLVED_COUNT_MISMATCH: authoritative={expected_unresolved}, "
            f"controlled_remediation_rows={len(controlled_repo_rows)}"
        )

    if failures:
        certification["status"]="FAIL"
        certification["failure_reasons"]=failures
    else:
        certification["status"]="PASS"
        certification["certification_state"]="CERTIFIED_WITH_CONTROLLED_REMEDIATION" if remediation_controls else "CERTIFIED"

    (out/"wave2b_certification.json").write_text(json.dumps(certification,indent=2),encoding="utf-8")
    print(json.dumps(certification,indent=2))
    raise SystemExit(0 if certification["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
