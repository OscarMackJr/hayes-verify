[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems"
)
$ErrorActionPreference="Stop"

Write-Host "=== Create or locate Wave 2C PR ===" -ForegroundColor Cyan

$existing = gh pr list --repo $Repo --head feature/wave2c-remediation --state open --json number,url,isDraft,title 2>$null | ConvertFrom-Json
if($existing.Count -gt 0){
    $existing | Format-Table number,title,isDraft,url -AutoSize
    Write-Host "PASS: existing Wave 2C PR found." -ForegroundColor Green
    exit 0
}

gh pr create `
  --repo $Repo `
  --base main `
  --head feature/wave2c-remediation `
  --title "Wave 2C remediation closeout" `
  --body "Wave 2C remediation and certification closeout. Control results are frozen; open remediation count is zero; inheritance validation is PASS." `
  --draft

if($LASTEXITCODE){throw "Failed to create Wave 2C draft PR."}
Write-Host "PASS: Wave 2C draft PR created." -ForegroundColor Green
