[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems"
)
$ErrorActionPreference="Stop"

$existing=gh pr list --repo $Repo --head chore/wave2c-baseline-registration --state open --json number,url,isDraft,title | ConvertFrom-Json
if($existing.Count -gt 0){
    $existing|Format-Table number,title,isDraft,url -AutoSize
    Write-Host "PASS: existing baseline-registration PR found." -ForegroundColor Green
    exit 0
}

gh pr create `
  --repo $Repo `
  --base main `
  --head chore/wave2c-baseline-registration `
  --title "Persist Wave 2C baseline registration" `
  --body "Persists the authoritative Wave 2C baseline registration/spec/schema only. Generated post-merge bundle remains externally archived. No EMS control results changed." `
  --draft
if($LASTEXITCODE){throw "Failed to create draft PR"}

Write-Host "PASS: draft baseline-registration PR created." -ForegroundColor Green
