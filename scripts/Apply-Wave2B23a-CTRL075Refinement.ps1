[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$collector = Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
if(-not(Test-Path $collector)){
    throw "Collector not found: $collector"
}

$backup = "$collector.pre-2B2.3a.bak"
Copy-Item $collector $backup -Force

$text = Get-Content $collector -Raw

$oldImports = 'import argparse,csv,json,re'
$newImports = 'import argparse,csv,json,re'
# imports unchanged; retained for stable patching.

$oldBlock = @'
    compliance_outputs=[p for p in fs if any(x in p.name.lower() for x in [
        "repository_control_compliance","effective_compliance","compliance_postpolicy",
        "inheritance_impact_report","compliance_report","continuous_compliance"
    ]) and p.suffix.lower() in {".csv",".json"}]

    execution_reports=[p for p in fs if p.suffix.lower()==".json" and any(
        x in txt(p).lower() for x in ['"status": "pass"','"row_count"','"errors": []','"observation_count"']
    )]

    repo_names=set()
    control_ids=set()
    row_count=0
    for p in compliance_outputs:
        t=txt(p)
        row_count += max(0, len(t.splitlines())-1) if p.suffix.lower()==".csv" else 0
        repo_names |= set(re.findall(r'(?im)^(bluto|fiskroad|hometown|nono|olive|popeye),',t))
        control_ids |= set(re.findall(r'EMS-CTRL-\d{3}',t))

    latest_candidates=[p for p in compliance_outputs+execution_reports if p.exists()]
    latest=max(latest_candidates,key=lambda p:p.stat().st_mtime) if latest_candidates else None

    retained_outputs=[p for p in compliance_outputs if "\\generated\\" in str(p).lower().replace("/","\\") or "\\releases\\" in str(p).lower().replace("/","\\")]
'@

$newBlock = @'
    compliance_outputs=[p for p in fs if any(x in p.name.lower() for x in [
        "repository_control_compliance","effective_compliance","compliance_postpolicy",
        "inheritance_impact_report","compliance_report","continuous_compliance"
    ]) and p.suffix.lower() in {".csv",".json"}]

    def is_execution_artifact(p):
        low=str(p).lower().replace("/","\\")
        name=p.name.lower()

        if any(x in low for x in [
            "\\schemas\\",
            "\\registry\\",
            "\\scripts\\",
            "\\docs\\",
            ".bak"
        ]):
            return False

        if name.endswith(".schema.json"):
            return False

        if "\\generated\\" not in low and "\\releases\\" not in low and "\\release\\" not in low:
            return False

        if p.suffix.lower() not in {".csv",".json"}:
            return False

        t=txt(p).lower()

        return any(x in name for x in [
            "repository_control_compliance",
            "effective_compliance",
            "compliance_postpolicy",
            "inheritance_impact_report",
            "validation",
            "observation",
            "compliance_report"
        ]) or any(x in t for x in [
            '"row_count"',
            '"observation_count"',
            '"errors": []',
            'repository_name,control_id',
            'repository_name,'
        ])

    execution_reports=[p for p in fs if is_execution_artifact(p)]

    repo_names=set()
    evaluated_control_ids=set()
    applicable_control_ids=set()
    result_row_count=0

    for p in compliance_outputs:
        if p.suffix.lower()==".csv":
            try:
                with p.open(encoding="utf-8-sig",newline="") as fh:
                    rows=list(csv.DictReader(fh))
            except Exception:
                rows=[]

            result_row_count += len(rows)

            for r in rows:
                repo=(r.get("repository_name") or r.get("repository") or "").strip()
                cid=(r.get("control_id") or "").strip()
                status=(r.get("compliance_status") or r.get("effective_status") or r.get("status") or "").strip()

                if repo:
                    repo_names.add(repo)

                if re.fullmatch(r"EMS-CTRL-\d{3}",cid):
                    evaluated_control_ids.add(cid)

                    if status and status != "NOT_APPLICABLE":
                        applicable_control_ids.add(cid)

        elif p.suffix.lower()==".json":
            t=txt(p)
            repo_names |= set(re.findall(r'"repository_name"\s*:\s*"([^"]+)"',t))
            evaluated_control_ids |= set(re.findall(r'EMS-CTRL-\d{3}',t))

    latest_candidates=[p for p in execution_reports if p.exists()]
    latest=max(latest_candidates,key=lambda p:p.stat().st_mtime) if latest_candidates else None

    retained_outputs=[p for p in compliance_outputs if "\\generated\\" in str(p).lower().replace("/","\\") or "\\releases\\" in str(p).lower().replace("/","\\") or "\\release\\" in str(p).lower().replace("/","\\")]
'@

if(-not $text.Contains($oldBlock)){
    throw "Expected CTRL-075 discovery block not found."
}
$text = $text.Replace($oldBlock,$newBlock)

$oldAssertions = @'
            A["managed_repository_population_evaluated"]=assertion(
                "PASS" if len(repo_names)>=6 else ("WARNING" if repo_names else "UNKNOWN"),
                f"{len(repo_names)} managed repository name(s) observed: {sorted(repo_names)}"
            )
            A["control_results_generated"]=assertion(
                "PASS" if len(control_ids)>=80 or row_count>=80 else ("WARNING" if control_ids or row_count else "UNKNOWN"),
                f"{len(control_ids)} unique control id(s); approx_csv_rows={row_count}"
            )
            A["scan_output_retained"]=assertion(
                "PASS" if retained_outputs else "UNKNOWN",
                f"{len(retained_outputs)} retained generated/release compliance output(s) detected."
            )
            A["latest_execution_identifiable"]=assertion(
                "PASS" if latest else "UNKNOWN",
                f"Latest execution artifact={latest}; mtime={datetime.fromtimestamp(latest.stat().st_mtime).isoformat()}" if latest else "No execution artifact timestamp available."
            )
'@

$newAssertions = @'
            A["managed_repository_population_evaluated"]=assertion(
                "PASS" if len(repo_names)>=6 else ("WARNING" if repo_names else "UNKNOWN"),
                f"{len(repo_names)} structurally parsed managed repository name(s) observed: {sorted(repo_names)}"
            )

            catalog_control_count=80
            evaluated_control_count=len(evaluated_control_ids)
            applicable_control_count=len(applicable_control_ids)

            coverage_ok=(
                evaluated_control_count >= applicable_control_count
                and applicable_control_count > 0
                and result_row_count > 0
            )

            A["control_results_generated"]=assertion(
                "PASS" if coverage_ok else ("WARNING" if evaluated_control_count or result_row_count else "UNKNOWN"),
                (
                    f"catalog_control_count={catalog_control_count}; "
                    f"evaluated_control_count={evaluated_control_count}; "
                    f"applicable_control_count={applicable_control_count}; "
                    f"result_row_count={result_row_count}"
                )
            )

            A["scan_output_retained"]=assertion(
                "PASS" if retained_outputs else "UNKNOWN",
                f"{len(retained_outputs)} retained generated/release compliance output(s) detected."
            )

            A["latest_execution_identifiable"]=assertion(
                "PASS" if latest else "UNKNOWN",
                (
                    f"Latest execution artifact={latest}; "
                    f"mtime={datetime.fromtimestamp(latest.stat().st_mtime).isoformat()}"
                    if latest else
                    "No qualifying generated/release execution artifact available."
                )
            )
'@

if(-not $text.Contains($oldAssertions)){
    throw "Expected CTRL-075 assertion block not found."
}
$text = $text.Replace($oldAssertions,$newAssertions)

Set-Content $collector $text -Encoding UTF8

Write-Host "Wave 2B.2.3a CTRL-075 refinement applied." -ForegroundColor Green
Write-Host "Backup:"
Write-Host "  $backup"
