[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems",
    [int]$PRNumber=0,
    [switch]$MarkReady,
    [switch]$Merge
)
$ErrorActionPreference="Stop"

function Fail([string]$m){throw "WAVE 2C MERGE BLOCKED: $m"}

if($PRNumber -le 0){
    $prs = gh pr list --repo $Repo --head feature/wave2c-remediation --state open --json number | ConvertFrom-Json
    if($prs.Count -ne 1){Fail "Expected exactly one open Wave 2C PR; found $($prs.Count)."}
    $PRNumber=[int]$prs[0].number
}

Write-Host "=== Inspect Wave 2C PR #$PRNumber ===" -ForegroundColor Cyan

$pr = gh pr view $PRNumber --repo $Repo --json number,title,state,isDraft,mergeable,mergeStateStatus,headRefName,baseRefName,headRefOid,url,statusCheckRollup | ConvertFrom-Json
if(-not $pr){Fail "Unable to inspect PR."}

[pscustomobject]@{
    PR=$pr.number
    Title=$pr.title
    State=$pr.state
    Draft=$pr.isDraft
    Head=$pr.headRefName
    Base=$pr.baseRefName
    Mergeable=$pr.mergeable
    MergeStateStatus=$pr.mergeStateStatus
    HeadSha=$pr.headRefOid
    Url=$pr.url
} | Format-List

if($pr.state -ne "OPEN"){Fail "PR is not OPEN."}
if($pr.headRefName -ne "feature/wave2c-remediation"){Fail "Unexpected head branch."}
if($pr.baseRefName -ne "main"){Fail "Unexpected base branch."}
if($pr.mergeable -ne "MERGEABLE"){Fail "PR is not mergeable."}

Write-Host "`n=== Validate local frozen certification ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C-PRReadiness.ps1") -EMSPath $EMSPath
if(-not $?){Fail "Local Wave 2C certification gate failed."}

Write-Host "`n=== Inspect PR checks ===" -ForegroundColor Cyan
$checks=@($pr.statusCheckRollup)
$bad=@()
foreach($c in $checks){
    $state = if($c.conclusion){$c.conclusion}else{$c.status}
    [pscustomobject]@{Check=$c.name;State=$state} | Format-Table -AutoSize
    if($c.conclusion -and $c.conclusion -notin @("SUCCESS","NEUTRAL","SKIPPED")){
        $bad += "$($c.name):$($c.conclusion)"
    }
    if(-not $c.conclusion -and $c.status -ne "COMPLETED"){
        $bad += "$($c.name):$($c.status)"
    }
}
if($bad.Count -gt 0){Fail "Required checks are not successful: $($bad -join ', ')"}

if($MarkReady -and $pr.isDraft){
    gh pr ready $PRNumber --repo $Repo
    if($LASTEXITCODE){Fail "Failed to mark PR ready."}
    $pr.isDraft=$false
}

if($Merge){
    if($pr.isDraft){Fail "PR is still draft. Re-run with -MarkReady -Merge."}
    gh pr merge $PRNumber --repo $Repo --squash --delete-branch
    if($LASTEXITCODE){Fail "PR merge failed."}
    Write-Host "PASS: Wave 2C PR merged." -ForegroundColor Green
    exit 0
}

Write-Host "`nPASS: PR #$PRNumber satisfies the Wave 2C merge gate." -ForegroundColor Green
if($pr.isDraft){
    Write-Host "PR is still draft. Re-run with -MarkReady or -MarkReady -Merge."
}else{
    Write-Host "Re-run with -Merge when ready."
}
