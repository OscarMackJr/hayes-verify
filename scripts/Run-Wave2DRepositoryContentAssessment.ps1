[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[hashtable]$RepositoryPaths)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D REPOSITORY CONTENT ASSESSMENT BLOCKED: $m"}
$root=(Resolve-Path $EMSPath).Path
$queue="$root\registry\wave2d\applicability_review_queue.csv"
if(-not(Test-Path $queue)){Fail "Applicability review queue missing."}
$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}
$outDir="$root\generated\wave2d\repository-content-assessment"
New-Item -ItemType Directory -Force -Path $outDir|Out-Null
$repoMap="$outDir\repository_map.json"
if($RepositoryPaths){
    $RepositoryPaths|ConvertTo-Json -Depth 10|Set-Content $repoMap -Encoding UTF8
}else{
    & $py "$root\scripts\Discover-Wave2DRepositoryPaths.py" --ems-root $root --review-queue $queue | Set-Content $repoMap -Encoding UTF8
    if($LASTEXITCODE){Fail "Repository path discovery failed."}
}
Write-Host "=== Repository map ===" -ForegroundColor Cyan
Get-Content $repoMap
& $py "$root\scripts\Assess-Wave2DRepositoryContent.py" --review-queue $queue --repo-map $repoMap --out "$outDir\repository_content_applicability_assessment.csv" --summary "$outDir\repository_content_applicability_summary.json"
if($LASTEXITCODE){Fail "Repository content assessment failed."}
& $py "$root\scripts\Prepare-Wave2DAssistedHumanReview.py" --assessment "$outDir\repository_content_applicability_assessment.csv" --review-queue $queue --out "$root\registry\wave2d\applicability_review_decisions.csv"
if($LASTEXITCODE){Fail "Assisted review preparation failed."}
Write-Host "PASS: repository-content assessment complete." -ForegroundColor Green
