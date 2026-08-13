$ErrorActionPreference="Stop"
$Root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Out=Join-Path $Root "generated\wave2\higher-scope-collectors\ai-governance"
Write-Host "Collector report:"
Get-Content (Join-Path $Out "collector_report.json")
Write-Host "`nAssertions:"
Import-Csv (Join-Path $Out "assertions.csv") | Format-Table -Wrap -AutoSize
Write-Host "`nQualification summary:"
Get-Content (Join-Path $Out "qualification_summary.json")
Write-Host "`nQualified controls:"
Import-Csv (Join-Path $Out "qualification.csv") | Format-Table -AutoSize
Write-Host "`nGaps:"
$g=Import-Csv (Join-Path $Out "gaps.csv")
if($g){ $g | Format-Table -Wrap -AutoSize } else { Write-Host "None." }
