[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Build-Wave2DApplicabilityReviewQueue.py",
    "Validate-Wave2DHumanApplicabilityDecisions.py",
    "Apply-Wave2DHumanApplicabilityDecisions.py",
    "Reconcile-Wave2DApplicabilityAfterHumanReview.py",
    "Run-Wave2DApplicabilityHumanReview.ps1",
    "Show-Wave2DApplicabilityHumanReview.ps1",
    "Stage-Wave2DApplicabilityHumanReview.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\wave2d_applicability_human_review_spec.json" "$EMSPath\registry\wave2d_applicability_human_review_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_applicability_human_review_record.schema.json" "$EMSPath\schemas\wave2d_applicability_human_review_record.schema.json" -Force
Write-Host "Wave 2D Applicability Review & Human Adjudication tooling installed." -ForegroundColor Green
