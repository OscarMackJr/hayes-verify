[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"

Write-Host "=== Wave 2C PR readiness ===" -ForegroundColor Cyan

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch -ne "feature/wave2c-remediation"){throw "Expected feature/wave2c-remediation; current=$branch"}

$cert=Join-Path $EMSPath "release\wave2c\post-closeout\branch_certification.json"
$scope=Join-Path $EMSPath "release\wave2c\post-closeout\scope_validation.json"
$summary=Join-Path $EMSPath "release\wave2c\post-closeout\release_package_summary.json"

foreach($p in @($cert,$scope,$summary)){
    if(-not(Test-Path $p)){throw "Required release-prep artifact missing: $p"}
}

$c=Get-Content $cert -Raw|ConvertFrom-Json
$s=Get-Content $scope -Raw|ConvertFrom-Json

if($c.status -ne "PASS"){throw "Branch certification not PASS."}
if($c.wave2c_state -ne "CLOSED"){throw "Wave 2C not CLOSED."}
if([int]$c.open_remediation_count -ne 0){throw "Open remediation count is not zero."}
if($c.inheritance_validation -ne "PASS"){throw "Inheritance validation not PASS."}
if($s.status -ne "PASS"){throw "Scope validation not PASS."}

$staged=@(git -C $EMSPath diff --cached --name-only)
if($staged.Count -eq 0){throw "No staged files."}

Write-Host "PASS: Wave 2C branch is ready for commit/push." -ForegroundColor Green
