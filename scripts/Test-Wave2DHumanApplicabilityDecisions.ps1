[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"

$file = Join-Path $EMSPath "registry\wave2d\applicability_review_decisions.csv"
if (-not (Test-Path $file)) {
    throw "Decision file not found: $file"
}

$rows = @(Import-Csv $file)
$bad = @()

foreach ($r in $rows) {
    if ($r.human_decision -notin @("APPLICABLE","NOT_APPLICABLE") -or
        [string]::IsNullOrWhiteSpace($r.human_rationale) -or
        [string]::IsNullOrWhiteSpace($r.human_decision_owner) -or
        $r.human_decision_source -notmatch '^HUMAN_') {
        $bad += $r
    }
}

[pscustomobject]@{
    TotalRows      = $rows.Count
    Applicable     = @($rows | Where-Object {$_.human_decision -eq "APPLICABLE"}).Count
    NotApplicable  = @($rows | Where-Object {$_.human_decision -eq "NOT_APPLICABLE"}).Count
    InvalidRows    = $bad.Count
} | Format-List

if ($bad.Count -gt 0) {
    $bad | Select-Object control_id,repository_name,human_decision,human_rationale,human_decision_owner,human_decision_source |
        Format-Table -Wrap -AutoSize
    throw "Human applicability decision file is incomplete."
}

Write-Host "PASS: human applicability decision file is complete." -ForegroundColor Green
