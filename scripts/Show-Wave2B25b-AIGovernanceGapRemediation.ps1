[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-gap-remediation"

Write-Host "Gap resolution summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "gap_resolution_summary.json")

Write-Host ""
Write-Host "Gap resolution:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "gap_resolution.csv") |
  Select-Object control_id,control_name,assertion,operating_evidence_count,rejected_source_count,status,sufficiency,promotion_eligible |
  Format-Table -AutoSize

Write-Host ""
Write-Host "Targeted evidence candidates:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "targeted_evidence_candidates.csv") |
  Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Open remediation items:" -ForegroundColor Cyan
$r=Import-Csv (Join-Path $out "remediation_queue.csv")
if($r){$r|Format-Table -Wrap -AutoSize}else{Write-Host "None."}
