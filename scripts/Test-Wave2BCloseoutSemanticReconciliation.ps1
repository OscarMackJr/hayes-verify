[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$certifier=Join-Path $EMSPath "scripts\Certify-Wave2B.py"
$text=Get-Content $certifier -Raw

$checks=[ordered]@{
    RecognizesHigherScopePass             = $text -match 'reason=="HIGHER_SCOPE_PASS"'
    TreatsInheritedAsSatisfied            = $text -match '"INHERITED"'
    UsesAuthoritativeUnresolvedCount      = $text -match 'unresolved_higher_scope_count'
    ExcludesNativeNotEvaluatedRows        = $text -match 'OUTSIDE_WAVE2B_INHERITANCE_CLOSEOUT'
    RequiresCountReconciliation           = $text -match 'authoritative_unresolved_count_matches'
    PreservesControlledRemediation        = $text -match 'CONTROLLED_REMEDIATION'
    StillFailsUndispositionedRows         = $text -match 'UNDISPOSITIONED_HIGHER_SCOPE_ROWS'
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2B semantic-reconciliation hotfix validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $certifier
if($LASTEXITCODE-ne 0){throw "Certify-Wave2B.py compile validation failed."}

Write-Host "PASS: Wave 2B semantic-reconciliation hotfix validated." -ForegroundColor Green
