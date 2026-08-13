[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D DEFINITION PR READINESS BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-scope-population"){Fail "Wrong branch"}

$v=Get-Content "$root\generated\wave2d\applicability-freeze\applicability_freeze_validation.json" -Raw|ConvertFrom-Json
if($v.status -ne "PASS"){Fail "Applicability freeze validation not PASS"}
if([int]$v.matrix_row_count -ne 560){Fail "Matrix row count invalid"}
if([int]$v.applicable_count -ne 410){Fail "Applicable count invalid"}
if([int]$v.not_applicable_count -ne 150){Fail "Not-applicable count invalid"}
if([int]$v.review_required_count -ne 0 -or [int]$v.pending_count -ne 0){Fail "Unresolved applicability remains"}
if($v.evaluation_performed -ne $false -or $v.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state"}

$staged=@(git -C $root diff --cached --name-only)
if($staged.Count -eq 0){Fail "No staged files"}

$bad=@($staged|Where-Object{
    $_ -notmatch '^generated/wave2d/' -and
    $_ -notmatch '^registry/wave2d/' -and
    $_ -notmatch '^registry/wave2d_' -and
    $_ -notmatch '^schemas/wave2d_' -and
    $_ -notmatch '^scripts/.*Wave2D'
})
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Out-of-scope staged file(s) detected."
}

Write-Host "PASS: Wave 2D definition branch is ready for commit/push." -ForegroundColor Green
