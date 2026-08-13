[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D INIT PR CREATION BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-initialization"){
    Fail "Expected feature/wave2d-initialization; current=$branch"
}

$local=(git -C $root rev-parse HEAD).Trim()
$remote=(git -C $root rev-parse origin/feature/wave2d-initialization 2>$null).Trim()
if(-not $remote){Fail "Remote Wave 2D initialization branch not found. Push first."}
if($local -ne $remote){Fail "Local HEAD does not match origin/feature/wave2d-initialization."}

$existing=@(
    gh pr list `
      --repo $Repo `
      --head feature/wave2d-initialization `
      --state open `
      --json number,title,isDraft,url 2>$null | ConvertFrom-Json
)

if($existing.Count -gt 0){
    Write-Host "Existing Wave 2D initialization PR:" -ForegroundColor Cyan
    $existing | Format-Table number,title,isDraft,url -AutoSize
    Write-Host "PASS: existing draft/open PR found." -ForegroundColor Green
    exit 0
}

Write-Host "=== Create Wave 2D initialization draft PR ===" -ForegroundColor Cyan
gh pr create `
  --repo $Repo `
  --base main `
  --head feature/wave2d-initialization `
  --title "Wave 2D baseline intake and scope initialization" `
  --body "Initializes Wave 2D from the authoritative ems-v0.6.0-wave2c baseline. Scope and population begin at zero with no implicit carry-forward. Certified Wave 2C evidence/results remain read-only. No EMS control results changed." `
  --draft

if($LASTEXITCODE){Fail "Failed to create Wave 2D draft PR."}

Write-Host "PASS: Wave 2D initialization draft PR created." -ForegroundColor Green
