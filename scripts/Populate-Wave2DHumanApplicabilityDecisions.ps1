[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$DefaultOwner = "Engineering Management",
    [string]$DecisionSource = "HUMAN_MANUAL_REVIEW",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

function Fail([string]$m) {
    throw "WAVE 2D HUMAN APPLICABILITY POPULATION BLOCKED: $m"
}

$root = (Resolve-Path $EMSPath).Path
$template = Join-Path $root "registry\wave2d\applicability_review_template.csv"
$output   = Join-Path $root "registry\wave2d\applicability_review_decisions.csv"

if (-not (Test-Path $template)) {
    Fail "Review template not found: $template"
}

if ($DecisionSource -notmatch '^HUMAN_') {
    Fail "DecisionSource must begin with HUMAN_."
}

if ($Resume -and (Test-Path $output)) {
    $rows = @(Import-Csv $output)
    Write-Host "Resuming existing human applicability decisions." -ForegroundColor Cyan
}
else {
    $rows = @(Import-Csv $template)
}

if ($rows.Count -eq 0) {
    Fail "Review template contains no rows."
}

Write-Host "=== Wave 2D Human Applicability Population ===" -ForegroundColor Cyan
Write-Host "Rows to review: $($rows.Count)"
Write-Host "Allowed decisions: APPLICABLE / NOT_APPLICABLE"
Write-Host "Default owner: $DefaultOwner"
Write-Host "Decision source: $DecisionSource"
Write-Host ""

for ($i = 0; $i -lt $rows.Count; $i++) {
    $r = $rows[$i]

    if (
        $Resume -and
        $r.human_decision -in @("APPLICABLE","NOT_APPLICABLE") -and
        -not [string]::IsNullOrWhiteSpace($r.human_rationale) -and
        -not [string]::IsNullOrWhiteSpace($r.human_decision_owner) -and
        $r.human_decision_source -match '^HUMAN_'
    ) {
        Write-Host "[$($i+1)/$($rows.Count)] Already complete: $($r.control_id) / $($r.repository_name)" -ForegroundColor DarkGray
        continue
    }

    Write-Host ""
    Write-Host "[$($i+1)/$($rows.Count)] $($r.control_id) - $($r.control_name)" -ForegroundColor Yellow
    Write-Host "Target: $($r.target_id) / $($r.repository_name)"
    Write-Host "Current rationale: $($r.current_rationale)"
    Write-Host ""

    $decision = $null
    while ($decision -notin @("APPLICABLE","NOT_APPLICABLE")) {
        $raw = Read-Host "Decision [A=APPLICABLE, N=NOT_APPLICABLE]"
        switch ($raw.Trim().ToUpperInvariant()) {
            "A"              { $decision = "APPLICABLE" }
            "APPLICABLE"     { $decision = "APPLICABLE" }
            "N"              { $decision = "NOT_APPLICABLE" }
            "NA"             { $decision = "NOT_APPLICABLE" }
            "NOT_APPLICABLE" { $decision = "NOT_APPLICABLE" }
            default {
                Write-Host "Enter A/APPLICABLE or N/NA/NOT_APPLICABLE." -ForegroundColor Red
            }
        }
    }

    $rationale = ""
    while ([string]::IsNullOrWhiteSpace($rationale)) {
        $rationale = Read-Host "Rationale"
        if ([string]::IsNullOrWhiteSpace($rationale)) {
            Write-Host "Rationale is required." -ForegroundColor Red
        }
    }

    $ownerInput = Read-Host "Decision owner [$DefaultOwner]"
    $owner = if ([string]::IsNullOrWhiteSpace($ownerInput)) {
        $DefaultOwner
    } else {
        $ownerInput.Trim()
    }

    $r.human_decision        = $decision
    $r.human_rationale       = $rationale.Trim()
    $r.human_decision_owner  = $owner
    $r.human_decision_source = $DecisionSource

    # Save after every row so interruption is recoverable.
    $rows | Export-Csv $output -NoTypeInformation -Encoding UTF8
}

Write-Host ""
Write-Host "=== Validate completed human review ===" -ForegroundColor Cyan

$errors = @()

for ($i = 0; $i -lt $rows.Count; $i++) {
    $r = $rows[$i]
    $rowNum = $i + 2

    if ($r.human_decision -notin @("APPLICABLE","NOT_APPLICABLE")) {
        $errors += "Row $rowNum: invalid/missing human_decision."
    }
    if ([string]::IsNullOrWhiteSpace($r.human_rationale)) {
        $errors += "Row $rowNum: human_rationale is required."
    }
    if ([string]::IsNullOrWhiteSpace($r.human_decision_owner)) {
        $errors += "Row $rowNum: human_decision_owner is required."
    }
    if ($r.human_decision_source -notmatch '^HUMAN_') {
        $errors += "Row $rowNum: human_decision_source must begin with HUMAN_."
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Fail "$($errors.Count) validation error(s) remain."
}

$rows | Export-Csv $output -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "Decision counts:" -ForegroundColor Cyan
$rows |
    Group-Object human_decision |
    Select-Object Name, Count |
    Format-Table -AutoSize

Write-Host "PASS: all $($rows.Count) Wave 2D human applicability rows are populated." -ForegroundColor Green
Write-Host "Output: $output"
Write-Host ""
Write-Host "Next:"
Write-Host "  .\scripts\Run-Wave2DApplicabilityHumanReview.ps1"
Write-Host "  .\scripts\Show-Wave2DApplicabilityHumanReview.ps1"
