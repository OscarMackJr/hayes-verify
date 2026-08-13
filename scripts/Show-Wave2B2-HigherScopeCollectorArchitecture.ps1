[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "generated\wave2\higher-scope-collector-architecture"
Write-Host "Architecture summary:" -ForegroundColor Cyan;Get-Content (Join-Path $out "architecture_summary.json")
Write-Host "`nCollector families:" -ForegroundColor Cyan;Import-Csv (Join-Path $out "higher_scope_collector_registry.csv")|Format-Table -Wrap -AutoSize
Write-Host "`nEvidence requirements:" -ForegroundColor Cyan;Import-Csv (Join-Path $out "higher_scope_evidence_requirements.csv")|Select-Object control_id,control_name,scope,collector_id,required_evidence_class,promotion_mode|Format-Table -Wrap -AutoSize
