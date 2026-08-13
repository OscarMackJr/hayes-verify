[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-qualified-v2"

Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "qualification_summary.json")

Write-Host ""
Write-Host "Qualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "qualified_ai_governance.csv") |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Assertion/evidence matrix:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "assertion_evidence_matrix.csv") |
    Select-Object control_id,assertion,source_count,operating_evidence_count,rejected_source_count,operating_evidence_sufficient |
    Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Gaps:" -ForegroundColor Cyan
$g=Import-Csv (Join-Path $out "ai_governance_gaps.csv")
if($g){$g|Format-Table -Wrap -AutoSize}else{Write-Host "None."}

Write-Host ""
Write-Host "Rejected source class counts:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "rejected_sources.csv") |
    Group-Object source_class |
    Select-Object Name,Count |
    Format-Table -AutoSize
