[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$cert=Join-Path $EMSPath "generated\wave2c\annual-review-closeout\wave2c_closeout_certification.json"
$recon=Join-Path $EMSPath "generated\wave2c\annual-review-closeout\inheritance_status_reconciliation.json"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

foreach($p in @($cert,$recon,$queue)){
    if(-not(Test-Path $p)){throw "Validation artifact missing: $p"}
}

$c=Get-Content $cert -Raw | ConvertFrom-Json
$r=Get-Content $recon -Raw | ConvertFrom-Json
$rows=@(Import-Csv $queue)

$checks=[ordered]@{
    CertificationPass        = ($c.status -eq "PASS")
    Wave2CClosed              = ($c.wave2c_state -eq "CLOSED")
    InheritanceValidationPass = ($c.inheritance_validation -eq "PASS")
    ZeroOpenRemediation       = (@($rows | Where-Object {$_.remediation_state -eq "OPEN"}).Count -eq 0)
    NoControlResultsChanged   = ($r.control_results_changed -eq $false)
    NoPopulationChanged       = ($r.remediation_population_changed -eq $false)
    NoEvidenceChanged         = ($r.evidence_artifacts_changed -eq $false)
}

$table=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$table|Format-Table -AutoSize

if(@($table|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2C closeout inheritance-status reconciliation validation failed."
}

Write-Host "PASS: Wave 2C closeout certification reconciled and validated." -ForegroundColor Green
