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

foreach($p in @($cert,$summary)){
    if(-not(Test-Path $p)){Fail "Required release artifact missing: $p"}
}

$c=Get-Content $cert -Raw|ConvertFrom-Json
$s=Get-Content $summary -Raw|ConvertFrom-Json

if($c.status -ne "PASS"){Fail "Post-merge certification is not PASS."}
if($c.tag_ready -ne $true){Fail "Certification does not authorize tagging."}
if($c.release -ne $Tag){Fail "Requested tag $Tag does not match certified release $($c.release)."}
if($s.status -ne "PASS"){Fail "Release package summary is not PASS."}

$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "main"){Fail "Tagging requires main; current=$branch"}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){Fail "Working tree must be clean before tagging."}

$head=(git -C $root rev-parse HEAD).Trim()
$origin=(git -C $root rev-parse origin/main).Trim()
if($head -ne $origin){Fail "HEAD does not match origin/main."}
if($head -ne $c.merge_commit_sha){Fail "HEAD no longer matches certified merge commit."}

$existing=git -C $root rev-parse -q --verify "refs/tags/$Tag" 2>$null
if($LASTEXITCODE -eq 0){
    $tagSha=(git -C $root rev-list -n 1 $Tag).Trim()
    if($tagSha -ne $head){Fail "Existing tag $Tag points to $tagSha, expected $head"}
    Write-Host "Tag $Tag already exists at certified HEAD." -ForegroundColor Yellow
}else{
    git -C $root tag -a $Tag -m "EMS Wave 2C post-merge certified release"
    if($LASTEXITCODE){Fail "Failed to create annotated tag."}
    Write-Host "Created annotated tag $Tag at $head." -ForegroundColor Green
}

if($Push){
    git -C $root push origin $Tag
    if($LASTEXITCODE){Fail "Failed to push tag $Tag."}
    Write-Host "PASS: tag $Tag pushed to origin." -ForegroundColor Green
}else{
    Write-Host "PASS: tag $Tag created locally. Re-run with -Push to publish." -ForegroundColor Green
}
