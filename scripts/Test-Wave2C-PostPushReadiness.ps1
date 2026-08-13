[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$ExpectedBranch="feature/wave2c-remediation"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C POST-PUSH READINESS BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch -ne $ExpectedBranch){Fail "Expected branch $ExpectedBranch; current=$branch"}

$cert=Join-Path $EMSPath "release\wave2c\post-closeout\branch_certification.json"
$scope=Join-Path $EMSPath "release\wave2c\post-closeout\scope_validation.json"
$summary=Join-Path $EMSPath "release\wave2c\post-closeout\release_package_summary.json"

foreach($p in @($cert,$scope,$summary)){
    if(-not(Test-Path $p)){Fail "Required release artifact missing: $p"}
}

$c=Get-Content $cert -Raw | ConvertFrom-Json
$s=Get-Content $scope -Raw | ConvertFrom-Json

if($c.status -ne "PASS"){Fail "Branch certification is not PASS."}
if($c.wave2c_state -ne "CLOSED"){Fail "Wave 2C is not CLOSED."}
if([int]$c.open_remediation_count -ne 0){Fail "Open remediation count is not zero."}
if($c.inheritance_validation -ne "PASS"){Fail "Inheritance validation is not PASS."}
if($s.status -ne "PASS"){Fail "Scope validation is not PASS."}

$localHead=(git -C $EMSPath rev-parse HEAD).Trim()
$remoteHead=(git -C $EMSPath rev-parse "origin/$ExpectedBranch").Trim()
if($localHead -ne $remoteHead){
    Fail "Local HEAD does not match origin/$ExpectedBranch."
}

$status=@(git -C $EMSPath status --porcelain)
$trackedChanges=@($status | Where-Object { $_ -notmatch '^\?\?' })
if($trackedChanges.Count -gt 0){
    $trackedChanges | ForEach-Object { Write-Host $_ }
    Fail "Tracked working-tree changes remain after push."
}

Write-Host "PASS: Wave 2C post-push branch readiness validated." -ForegroundColor Green
Write-Host "Local/remote HEAD: $localHead"
