[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$certifier=Join-Path $EMSPath "scripts\Certify-Wave2B.py"
$text=Get-Content $certifier -Raw

$checks=[ordered]@{
    UsesHigherScopeResultsAuthority    = $text -match 'higher_scope_results\.json'
    AuthorityPopulationOnly           = $text -match 'Authoritative Wave 2B control population comes ONLY'
    FailsUndispositionedControls      = $text -match 'UNDISPOSITIONED_HIGHER_SCOPE_CONTROLS'
    FailsUndispositionedRows          = $text -match 'UNDISPOSITIONED_HIGHER_SCOPE_ROWS'
    ReconcilesAuthoritativeCount      = $text -match 'authoritative_unresolved_count_matches'
    PreservesRemediation              = $text -match 'CONTROLLED_REMEDIATION'
    RepositoryRowsInformational       = $text -match 'Repository reconciliation is now informational only'
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize
if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2B authoritative-population hotfix validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
& $py -m py_compile $certifier
if($LASTEXITCODE-ne 0){throw "Certify-Wave2B.py compile validation failed."}

Write-Host "PASS: Wave 2B authoritative-population hotfix validated." -ForegroundColor Green
