[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$dir=Join-Path $EMSPath "generated\wave2\scope-adjudication"

Write-Host "Authoritative override report:" -ForegroundColor Cyan
Get-Content (Join-Path $dir "authoritative_scope_override_report.json")

Write-Host ""
Write-Host "Final adjudication decisions:" -ForegroundColor Cyan
Import-Csv (Join-Path $dir "scope_registry_adjudication_queue.authoritative.csv") |
    Group-Object reviewer_decision |
    Select-Object Name,Count |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Nine authoritative decisions:" -ForegroundColor Cyan
Import-Csv (Join-Path $dir "scope_registry_adjudication_queue.authoritative.csv") |
    Where-Object control_id -in @(
        "EMS-CTRL-006","EMS-CTRL-007","EMS-CTRL-016",
        "EMS-CTRL-055","EMS-CTRL-056","EMS-CTRL-057",
        "EMS-CTRL-058","EMS-CTRL-059","EMS-CTRL-060"
    ) |
    Select-Object control_id,control_name,current_scope,reviewer_decision,proposed_scope,reviewer_rationale |
    Format-Table -Wrap -AutoSize
