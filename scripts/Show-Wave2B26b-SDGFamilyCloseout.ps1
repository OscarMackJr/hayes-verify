[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance-closeout"

Write-Host "Family closeout:" -ForegroundColor Cyan
Get-Content (Join-Path $out "family_closeout.json")

Write-Host ""
Write-Host "Open remediation:" -ForegroundColor Cyan
$r=Import-Csv (Join-Path $out "open_remediation.csv")
if($r){$r|Format-Table -Wrap -AutoSize}else{Write-Host "None."}

Write-Host ""
Write-Host "Promotion report:" -ForegroundColor Cyan
$p=Join-Path $out "promotion_report.json"
if(Test-Path $p){Get-Content $p}else{Write-Host "No promotion run yet."}
