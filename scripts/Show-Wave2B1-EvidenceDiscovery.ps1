[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "generated\wave2\higher-scope-evidence"

Write-Host "Discovery summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "evidence_discovery_summary.json")

Write-Host ""
Write-Host "Best candidates:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "evidence_candidates.csv") |
  Where-Object { $_.is_best_candidate -eq "True" } |
  Select-Object control_id,control_name,scope,candidate_status,confidence,source_file |
  Sort-Object scope,control_id |
  Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Evidence gaps:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "evidence_gaps.csv") |
  Format-Table -Wrap -AutoSize
