[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
 "Initialize-Wave2C4AnnualReview.py",
 "Validate-Wave2C4AnnualReview.py",
 "Qualify-Wave2C4AnnualReview.py",
 "ReviewPromote-Wave2C4AnnualReview.py",
 "Closeout-Wave2C4.py",
 "Add-AnnualEMSReviewRecord.ps1",
 "Run-Wave2C4-AnnualReviewCloseout.ps1",
 "Show-Wave2C4-AnnualReviewCloseout.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}

Copy-Item (Join-Path $pkg "registry\wave2c4_annual_review_closeout_spec.json") (Join-Path $EMSPath "registry\wave2c4_annual_review_closeout_spec.json") -Force
Copy-Item (Join-Path $pkg "schemas\wave2c4_closeout_record.schema.json") (Join-Path $EMSPath "schemas\wave2c4_closeout_record.schema.json") -Force

Write-Host "Wave 2C.4 Annual EMS Review & Closeout tooling installed." -ForegroundColor Green
