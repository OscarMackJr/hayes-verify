[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\closeout-certification"

Write-Host "Wave 2B certification:" -ForegroundColor Cyan
Get-Content (Join-Path $out "wave2b_certification.json")

Write-Host ""
Write-Host "Scope validation:" -ForegroundColor Cyan
Get-Content (Join-Path $out "scope_registry_validation.json")

Write-Host ""
Write-Host "Higher-scope disposition summary:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "higher_scope_reconciliation.csv") |
  Group-Object closeout_disposition |
  Select-Object Name,Count |
  Format-Table -AutoSize

Write-Host ""
Write-Host "Open remediation controls:" -ForegroundColor Cyan
$r=Import-Csv (Join-Path $out "open_remediation.csv")
if($r){
    $r|Sort-Object control_id -Unique|
      Select-Object control_id,control_name,scope,missing_assertions,remediation_state|
      Format-Table -Wrap -AutoSize
}else{
    Write-Host "None."
}

Write-Host ""
Write-Host "Undispositioned rows:" -ForegroundColor Cyan
$u=Import-Csv (Join-Path $out "undispositioned_rows.csv")
if($u){$u|Format-Table -Wrap -AutoSize}else{Write-Host "None."}

$freeze=Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"
if(Test-Path $freeze){
    Write-Host ""
    Write-Host "Freeze summary:" -ForegroundColor Cyan
    Get-Content $freeze
}
