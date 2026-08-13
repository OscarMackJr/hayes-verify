[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\evidence-integrity-release"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\evidence-integrity-release-qualified"
Get-Content (Join-Path $c "collector_report.json")
Import-Csv (Join-Path $c "assertions.csv")|Select-Object control_id,assertion,result,detail|Format-Table -Wrap -AutoSize
Get-Content (Join-Path $q "qualification_summary.json")
Import-Csv (Join-Path $q "qualified_evidence_integrity_release.csv")|Select-Object control_id,control_name,status,sufficiency,promotion_eligible|Format-Table -AutoSize
Import-Csv (Join-Path $q "evidence_integrity_release_gaps.csv")|Format-Table -AutoSize
