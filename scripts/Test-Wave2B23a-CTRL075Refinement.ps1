[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
$text=Get-Content $collector -Raw

$checks=[ordered]@{
    ParsesCSVStructurally         = $text.Contains('csv.DictReader')
    ParsesRepositoryNameField    = $text.Contains('r.get("repository_name")')
    TracksEvaluatedControls      = $text.Contains('evaluated_control_ids')
    TracksApplicableControls     = $text.Contains('applicable_control_ids')
    TracksResultRowCount         = $text.Contains('result_row_count')
    RestrictsExecutionArtifacts  = $text.Contains('def is_execution_artifact')
    ExcludesSchemas              = $text.Contains('"\\schemas\\"')
    ExcludesRegistry             = $text.Contains('"\\registry\\"')
    ExcludesScripts              = $text.Contains('"\\scripts\\"')
    ExcludesSchemaJson           = $text.Contains('name.endswith(".schema.json")')
    UsesApplicableCoverage       = $text.Contains('applicable_control_count')
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}

$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "CTRL-075 refinement validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){
    throw "Patched collector syntax validation failed."
}

Write-Host "PASS: CTRL-075 execution-evidence refinement installed." -ForegroundColor Green
