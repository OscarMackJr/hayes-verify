[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path

Write-Host "Human review record:" -ForegroundColor Cyan
$p="$root\generated\wave2d\evaluation-matrix\applicability_human_review_record.json"
if(Test-Path $p){Get-Content $p}else{Write-Host "NOT YET APPLIED" -ForegroundColor Yellow}

Write-Host "`nCurrent applicability summary:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json"

Write-Host "`nHuman-decision counts:" -ForegroundColor Cyan
$review="$root\registry\wave2d\applicability_review_decisions.csv"
if(Test-Path $review){
    Import-Csv $review | Group-Object human_decision | Select Name,Count | Format-Table -AutoSize
}

Write-Host "`nRemaining unresolved decisions:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\applicability_decisions.csv" |
    Where-Object {$_.decision -eq "REVIEW_REQUIRED"} |
    Select control_id,control_name,target_id,repository_name,decision,rationale,decision_source |
    Format-Table -Wrap -AutoSize
