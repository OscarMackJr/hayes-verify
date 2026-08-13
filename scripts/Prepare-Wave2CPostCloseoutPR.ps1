[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$CommitMessage="close Wave 2C remediation and certification",
    [switch]$Commit,
    [switch]$Push
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C PR PREP BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch -ne "feature/wave2c-remediation"){
    Fail "Expected feature/wave2c-remediation; current=$branch"
}

$cert=Join-Path $EMSPath "release\wave2c\post-closeout\branch_certification.json"
$scope=Join-Path $EMSPath "release\wave2c\post-closeout\scope_validation.json"
if(!(Test-Path $cert) -or !(Test-Path $scope)){Fail "Release-preparation reports missing."}

$c=Get-Content $cert -Raw|ConvertFrom-Json
$s=Get-Content $scope -Raw|ConvertFrom-Json
if($c.status -ne "PASS"){Fail "Branch certification is not PASS."}
if($s.status -ne "PASS"){Fail "Scope validation is not PASS."}

$staged=@(git -C $EMSPath diff --cached --name-only)
if($staged.Count -eq 0){Fail "No staged files. Run Prepare-Wave2CPostCloseoutRelease.ps1 -Stage first."}

Write-Host "=== Wave 2C branch ready for commit ===" -ForegroundColor Cyan
git -C $EMSPath diff --cached --stat

if(-not $Commit){
    Write-Host "`nPASS: branch is staged and ready. No commit or push performed." -ForegroundColor Green
    Write-Host "Rerun with -Commit, optionally -Push."
    exit 0
}

git -C $EMSPath commit -m $CommitMessage
if($LASTEXITCODE){Fail "git commit failed."}

if($Push){
    git -C $EMSPath push -u origin feature/wave2c-remediation
    if($LASTEXITCODE){Fail "git push failed."}
}

Write-Host "`nPASS: Wave 2C branch commit preparation completed." -ForegroundColor Green
