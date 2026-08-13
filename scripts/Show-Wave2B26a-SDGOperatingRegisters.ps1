[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance-requalified"
$reg=Join-Path $EMSPath "registers\security-data-governance"

Write-Host "Register counts:" -ForegroundColor Cyan
$rows=foreach($f in @(
 "data_classification_register.json",
 "data_retention_register.json",
 "production_data_protection_register.json"
)){
 $o=Get-Content (Join-Path $reg $f) -Raw|ConvertFrom-Json
 [pscustomobject]@{Register=$f;RecordCount=@($o.records).Count}
}
$rows|Format-Table -AutoSize

Write-Host ""
Write-Host "Requalification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "qualification_summary_requalified.json")

Write-Host ""
Write-Host "Qualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "qualified_security_data_governance_requalified.csv")|Format-Table -AutoSize

Write-Host ""
Write-Host "Remaining gaps:" -ForegroundColor Cyan
$g=Import-Csv (Join-Path $out "security_data_governance_gaps_requalified.csv")
if($g){$g|Format-Table -Wrap -AutoSize}else{Write-Host "None."}

Write-Host ""
Write-Host "Register assertion evidence:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "register_assertion_evidence.csv")|Format-Table -Wrap -AutoSize
