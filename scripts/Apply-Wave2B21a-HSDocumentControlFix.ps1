
[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$collector = Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSDocumentControl.py"
if(-not(Test-Path $collector)){
    throw "Collector not found: $collector"
}

$backup = "$collector.pre-2B2.1a.bak"
Copy-Item $collector $backup -Force

$text = Get-Content $collector -Raw

$oldBlock = @'
    ids=[]
    for _,obj in docs: walk_ids(obj,ids)
    unique_ids=set(ids)
'@

$newBlock = @'
    # Separate authoritative definitions from ordinary references.
    authoritative_definition_files=[]
    for p,obj in docs:
        low=str(p).lower().replace("/","\\")
        name=p.name.lower()

        if any(x in low for x in [
            "\\generated\\",
            "\\releases\\",
            "\\release\\",
            ".bak",
            ".pre-",
            "\\evidence\\",
        ]):
            continue

        if name in {
            "control_catalog.yaml",
            "control_catalog.yml",
            "control_registry.yaml",
            "control_registry.yml",
        }:
            authoritative_definition_files.append((p,obj))

    definition_ids=[]
    for _,obj in authoritative_definition_files:
        walk_ids(obj,definition_ids)

    reference_ids=[]
    for _,obj in docs:
        walk_ids(obj,reference_ids)

    unique_definition_ids=set(definition_ids)
    unique_reference_ids=set(reference_ids)

    from collections import Counter
    definition_counts=Counter(definition_ids)
    duplicate_definition_ids=sorted(
        cid for cid,count in definition_counts.items()
        if count > 1
    )
'@

if(-not $text.Contains($oldBlock)){
    throw "Expected definition/reference block not found."
}
$text = $text.Replace($oldBlock,$newBlock)

$oldCtrl002 = @'
        elif cid=="EMS-CTRL-002":
            A["controlled_document_inventory_detected"]=assertion("PASS" if inventory_sources else "UNKNOWN",f"{len(inventory_sources)} inventory/catalog/registry source(s) detected.")
            A["document_ids_unique"]=assertion("PASS" if len(ids)==len(set(ids)) else "FAIL",f"{len(ids)} control/document ids observed; {len(set(ids))} unique.")
            A["version_or_status_metadata_detected"]=assertion("PASS" if meta["version"] or meta["status"] else "UNKNOWN",f"version={meta['version']} status={meta['status']}")
            A["controlled_artifacts_retrievable"]=assertion("PASS" if files else "UNKNOWN",f"{len(files)} repository artifact(s) traversable.")
            sources=inventory_sources[:15]
'@

$newCtrl002 = @'
        elif cid=="EMS-CTRL-002":
            A["controlled_document_inventory_detected"]=assertion(
                "PASS" if authoritative_definition_files else "UNKNOWN",
                f"{len(authoritative_definition_files)} authoritative control-definition source(s) detected."
            )
            A["controlled_ids_unique"]=assertion(
                "PASS" if authoritative_definition_files and not duplicate_definition_ids else (
                    "FAIL" if duplicate_definition_ids else "UNKNOWN"
                ),
                (
                    f"definition_occurrence_count={len(definition_ids)}; "
                    f"unique_definition_count={len(unique_definition_ids)}; "
                    f"reference_occurrence_count={len(reference_ids)}; "
                    f"unique_reference_count={len(unique_reference_ids)}; "
                    f"duplicate_definitions={duplicate_definition_ids}"
                )
            )
            A["version_or_status_metadata_detected"]=assertion(
                "PASS" if meta["version"] or meta["status"] else "UNKNOWN",
                f"version={meta['version']} status={meta['status']}"
            )
            A["controlled_artifacts_retrievable"]=assertion(
                "PASS" if files else "UNKNOWN",
                f"{len(files)} repository artifact(s) traversable."
            )
            sources=[str(p) for p,_ in authoritative_definition_files]
'@

if(-not $text.Contains($oldCtrl002)){
    throw "Expected EMS-CTRL-002 block not found."
}
$text = $text.Replace($oldCtrl002,$newCtrl002)

$old067 = '            A["controlled_ids_detected"]=assertion("PASS" if unique_ids else "UNKNOWN",f"{len(unique_ids)} EMS control ids detected.")'
$new067 = '            A["controlled_ids_detected"]=assertion("PASS" if unique_definition_ids else "UNKNOWN",f"{len(unique_definition_ids)} authoritative EMS control ids detected.")'

if(-not $text.Contains($old067)){
    throw "Expected EMS-CTRL-067 controlled_ids_detected line not found."
}
$text = $text.Replace($old067,$new067)

Set-Content $collector $text -Encoding UTF8

Write-Host "Wave 2B.2.1a collector patch applied." -ForegroundColor Green
Write-Host "Backup:"
Write-Host "  $backup"
