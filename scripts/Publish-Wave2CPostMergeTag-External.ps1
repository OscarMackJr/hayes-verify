[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Tag="ems-v0.6.0-wave2c",
    [switch]$Push
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C TAG BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$cert=Join-Path $root "release\wave2c\post-merge\post_merge_certification.json"
$summary=Join-Path $root "release\wave2c\post-merge\release_summary.json"
if(-not(Test-Path $cert)){Fail "Certification missing."}
if(-not(Test-Path $summary)){Fail "Release summary missing."}

$c=Get-Content $cert -Raw|ConvertFrom-Json
$s=Get-Content $summary -Raw|ConvertFrom-Json
if($c.status -ne "PASS" -or $c.tag_ready -ne $true){Fail "Certification does not authorize tag."}
if($c.release -ne $Tag){Fail "Tag mismatch."}
if($s.status -ne "PASS"){Fail "Release summary not PASS."}

$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "main"){Fail "Current branch is not main."}
$head=(git -C $root rev-parse HEAD).Trim()
$origin=(git -C $root rev-parse origin/main).Trim()
if($head -ne $origin){Fail "HEAD != origin/main."}
if($head -ne $c.merge_commit_sha){Fail "HEAD != certified merge commit."}

# Permit only untracked post-merge release outputs at tag time.
$status=@(git -C $root status --porcelain)
$bad=@()
foreach($line in $status){
    if($line -match '^\?\?\s+release/wave2c/post-merge/'){continue}
    $bad += $line
}
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Unexpected working-tree changes remain."
}

$existing=git -C $root rev-parse -q --verify "refs/tags/$Tag" 2>$null
if($LASTEXITCODE -eq 0){
    $tagSha=(git -C $root rev-list -n 1 $Tag).Trim()
    if($tagSha -ne $head){Fail "Existing tag points to $tagSha, expected $head"}
    Write-Host "Tag already exists at certified HEAD." -ForegroundColor Yellow
}else{
    git -C $root tag -a $Tag -m "EMS Wave 2C post-merge certified release"
    if($LASTEXITCODE){Fail "Failed to create annotated tag."}
    Write-Host "Created annotated tag $Tag at $head." -ForegroundColor Green
}

if($Push){
    git -C $root push origin $Tag
    if($LASTEXITCODE){Fail "Failed to push tag."}
    Write-Host "PASS: tag $Tag pushed to origin." -ForegroundColor Green
}else{
    Write-Host "PASS: tag created locally; re-run with -Push to publish." -ForegroundColor Green
}
