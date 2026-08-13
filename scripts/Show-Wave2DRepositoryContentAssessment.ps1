[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path
Get-Content "$root\generated\wave2d\repository-content-assessment\repository_content_applicability_summary.json"
Import-Csv "$root\generated\wave2d\repository-content-assessment\repository_content_applicability_assessment.csv"|Group-Object proposal|Select Name,Count|Format-Table -AutoSize
Import-Csv "$root\generated\wave2d\repository-content-assessment\repository_content_applicability_assessment.csv"|Group-Object confidence|Select Name,Count|Format-Table -AutoSize
