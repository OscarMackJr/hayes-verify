[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems",
    [int]$PRNumber=0,
    [switch]$MarkReady,
    [switch]$Merge
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C BASELINE MERGE BLOCKED: $m"}

if($PRNumber -le 0){
    $prs=gh pr list --repo $Repo --head chore/wave2c-baseline-registration --state open --json number | ConvertFrom-Json
    if($prs.Count -ne 1){Fail "Expected exactly one open baseline-registration PR"}
    $PRNumber=[int]$prs[0].number
}

$pr=gh pr view $PRNumber --repo $Repo --json number,title,state,isDraft,mergeable,mergeStateStatus,headRefName,baseRefName,headRefOid,statusCheckRollup,url | ConvertFrom-Json
if($pr.state -ne "OPEN"){Fail "PR is not OPEN"}
if($pr.headRefName -ne "chore/wave2c-baseline-registration"){Fail "Unexpected head"}
if($pr.baseRefName -ne "main"){Fail "Unexpected base"}
if($pr.mergeable -ne "MERGEABLE"){Fail "PR is not mergeable"}

Write-Host "PR: $($pr.number) $($pr.title)"
Write-Host "Draft: $($pr.isDraft) MergeStateStatus: $($pr.mergeStateStatus)"

$checks=@($pr.statusCheckRollup)
$bad=@()
foreach($c in $checks){
    $state=if($c.conclusion){$c.conclusion}else{$c.status}
    [pscustomobject]@{Check=$c.name;State=$state}|Format-Table -AutoSize
    if($c.conclusion -and $c.conclusion -notin @("SUCCESS","NEUTRAL","SKIPPED")){$bad+="$($c.name):$($c.conclusion)"}
    elseif(-not $c.conclusion -and $c.status -ne "COMPLETED"){$bad+="$($c.name):$($c.status)"}
}
if($bad.Count -gt 0){Fail "Checks not successful: $($bad -join ', ')"}

if($MarkReady -and $pr.isDraft){
    gh pr ready $PRNumber --repo $Repo
    if($LASTEXITCODE){Fail "Failed to mark ready"}
    $pr.isDraft=$false
}

if($Merge){
    if($pr.isDraft){Fail "PR still draft"}
    gh pr merge $PRNumber --repo $Repo --squash --delete-branch
    if($LASTEXITCODE){Fail "Merge failed"}
    Write-Host "PASS: baseline-registration PR merged." -ForegroundColor Green
    exit 0
}

Write-Host "PASS: baseline-registration PR satisfies merge gate." -ForegroundColor Green
