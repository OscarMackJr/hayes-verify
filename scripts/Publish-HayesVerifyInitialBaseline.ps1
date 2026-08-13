[CmdletBinding()]
param(
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$GitHubRepo="OscarMackJr/hayes-verify",
    [string]$Tag="hayes-verify-v0.1.0"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY INITIAL PUBLISH BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root
$py=Join-Path $root ".venv\Scripts\python.exe"
$spec=Join-Path $root "registry\hayes_verify_repository_bootstrap_spec.json"
$schema=Join-Path $root "schemas\hayes_verify_initial_baseline.schema.json"

if(-not(Test-Path "$root\.git")){Fail "repository is not initialized"}

$status=@(git status --porcelain)
if($status.Count){$status|ForEach-Object{Write-Host $_};Fail "working tree must be clean before baseline certification"}

& $py "$root\scripts\certify_hayes_verify_initial_baseline.py" --root $root --spec $spec --schema $schema
if($LASTEXITCODE){Fail "baseline certification failed"}

git add -f -- `
    "registry/release_baselines/hayes_verify_initial_baseline.json" `
    "generated/bootstrap/hayes_verify_initial_baseline_manifest.json" `
    "generated/bootstrap/hayes_verify_initial_baseline_certification.json"
if($LASTEXITCODE){Fail "failed to stage baseline registration/certification"}

git commit -m "persist Hayes Verify initial baseline certification"
if($LASTEXITCODE){Fail "baseline certification commit failed"}

& $py "$root\scripts\validate_hayes_verify_initial_baseline.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "baseline validation failed"}

gh repo view $GitHubRepo --json nameWithOwner 1>$null 2>$null
if($LASTEXITCODE -ne 0){
    gh repo create $GitHubRepo --private --source $root --remote origin
    if($LASTEXITCODE){Fail "GitHub repository creation failed"}
}

git push -u origin main
if($LASTEXITCODE){Fail "push main failed"}

if(-not(git tag --list $Tag)){
    git tag -a $Tag -m "Hayes Verify initial controlled baseline"
    if($LASTEXITCODE){Fail "tag creation failed"}
}
git push origin $Tag
if($LASTEXITCODE){Fail "tag push failed"}

Write-Host "PASS: Hayes Verify initial controlled baseline published." -ForegroundColor Green
Write-Host "Repository: $GitHubRepo"
Write-Host "Tag: $Tag"
