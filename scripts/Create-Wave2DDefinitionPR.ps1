[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D DEFINITION PR BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$local=(git -C $root rev-parse HEAD).Trim()
$remote=(git -C $root rev-parse origin/feature/wave2d-scope-population 2>$null).Trim()
if(-not $remote){Fail "Remote branch missing"}
if($local -ne $remote){Fail "Local/remote HEAD mismatch"}

$existing=@(
  gh pr list --repo $Repo --head feature/wave2d-scope-population --state open --json number,title,isDraft,url |
  ConvertFrom-Json
)
if($existing.Count -gt 0){
    $existing|Format-Table number,title,isDraft,url -AutoSize
    Write-Host "PASS: existing Wave 2D definition PR found." -ForegroundColor Green
    exit 0
}

gh pr create `
  --repo $Repo `
  --base main `
  --head feature/wave2d-scope-population `
  --title "Wave 2D scope, applicability, and evaluation matrix definition" `
  --body "Freezes Wave 2D scope and the 560-row applicability matrix: 410 APPLICABLE, 150 NOT_APPLICABLE, zero unresolved. No evidence collection, control evaluation, result assignment, or promotion performed." `
  --draft

if($LASTEXITCODE){Fail "Failed to create draft PR"}
Write-Host "PASS: Wave 2D definition draft PR created." -ForegroundColor Green
