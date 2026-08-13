[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$BaselinePath="C:\temp\standars\ems-local-archive\wave1-input\effective_compliance_postpolicy.csv"
)

$ErrorActionPreference="Stop"

Write-Host "=== Validate already-promoted CTRL-080 state ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C4-AlreadyPromotedState.ps1") -EMSPath $EMSPath
if($LASTEXITCODE){throw "Already-promoted CTRL-080 state validation failed."}

Write-Host "`n=== Resume Wave 2C.4 closeout ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Run-Wave2C4-AnnualReviewCloseout.ps1") `
    -EMSPath $EMSPath `
    -BaselinePath $BaselinePath

if($LASTEXITCODE){throw "Wave 2C.4 closeout resume failed."}
