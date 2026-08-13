[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "generated\wave2\higher-scope-evidence-qualified"

Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "evidence_qualification_summary.json")

Write-Host ""
Write-Host "Qualified best candidates:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "qualified_best_candidates.csv") |
 Select-Object control_id,control_name,scope,candidate_status,confidence,source_class,sufficiency,promotion_eligible,source_file |
 Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Remaining evidence gaps:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "qualified_evidence_gaps.csv") |
 Format-Table -Wrap -AutoSize
