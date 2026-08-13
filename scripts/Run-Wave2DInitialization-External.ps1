[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Branch="feature/wave2d-initialization"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D EXTERNAL BOOTSTRAP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$pkgRoot=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$specPath=Join-Path $pkgRoot "registry\wave2d_initialization_spec.json"
$spec=Get-Content $specPath -Raw|ConvertFrom-Json

Write-Host "=== Remove known installer-created untracked Wave 2D files from main ===" -ForegroundColor Cyan
$known=@(
    "registry/wave2d_initialization_spec.json",
    "schemas/wave2d_initialization_record.schema.json",
    "scripts/Bootstrap-Wave2D.ps1",
    "scripts/Initialize-Wave2D.py",
    "scripts/Show-Wave2DInitialization.ps1",
    "scripts/Stage-Wave2DInitialization.ps1",
    "scripts/Test-Wave2DProtectedBaseline.ps1",
    "scripts/Verify-Wave2DBaseline.py"
)
foreach($rel in $known){
    $full=Join-Path $root ($rel -replace '/','\')
    if(Test-Path $full){
        git -C $root ls-files --error-unmatch -- $rel 2>$null | Out-Null
        if($LASTEXITCODE -eq 0){Fail "Expected installer file to be untracked, but it is tracked: $rel"}
        Remove-Item $full -Force
        Write-Host "Removed $rel"
    }
}

Write-Host "`n=== Verify clean synchronized main ===" -ForegroundColor Cyan
$currentBranch=(git -C $root branch --show-current).Trim()
if($currentBranch -ne "main"){Fail "Expected main; current=$currentBranch"}

git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed"}

$head=(git -C $root rev-parse HEAD).Trim()
$origin=(git -C $root rev-parse origin/main).Trim()
if($head -ne $origin){Fail "HEAD $head != origin/main $origin"}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){
    $status|ForEach-Object{Write-Host $_}
    Fail "main is not clean after removing known installer files."
}

Write-Host "`n=== Verify authoritative Wave 2C baseline ===" -ForegroundColor Cyan
$regPath=Join-Path $root ($spec.baseline_registration -replace '/','\')
if(-not(Test-Path $regPath)){Fail "Missing baseline registration: $regPath"}
$reg=Get-Content $regPath -Raw|ConvertFrom-Json

if($reg.wave -ne "2C"){Fail "Baseline registration wave is not 2C."}
if($reg.release_tag -ne $spec.baseline_tag){Fail "Baseline release tag mismatch."}
if($reg.baseline_state -ne $spec.baseline_state_required){Fail "Baseline state is not AUTHORITATIVE."}
if($reg.control_results_changed -ne $false){Fail "Baseline registration reports control result changes."}

$tagSha=(git -C $root rev-list -n 1 $spec.baseline_tag).Trim()
if($tagSha -ne $reg.tag_commit_sha){Fail "Tag SHA does not match registered tag SHA."}

Write-Host "PASS: baseline $($spec.baseline_tag) verified at $tagSha." -ForegroundColor Green

Write-Host "`n=== Create Wave 2D branch ===" -ForegroundColor Cyan
git -C $root switch -c $Branch
if($LASTEXITCODE){Fail "Failed to create branch $Branch"}

Write-Host "`n=== Materialize Wave 2D durable initialization tooling/artifacts ===" -ForegroundColor Cyan
$dirs=@(
    "registry",
    "schemas",
    "scripts",
    "registry\wave2d",
    "generated\wave2d"
)
foreach($d in $dirs){New-Item -ItemType Directory -Force -Path (Join-Path $root $d)|Out-Null}

Copy-Item (Join-Path $pkgRoot "registry\wave2d_initialization_spec.json") (Join-Path $root "registry\wave2d_initialization_spec.json") -Force
Copy-Item (Join-Path $pkgRoot "schemas\wave2d_initialization_record.schema.json") (Join-Path $root "schemas\wave2d_initialization_record.schema.json") -Force

foreach($n in @(
    "Test-Wave2DProtectedBaseline.ps1",
    "Show-Wave2DInitialization.ps1",
    "Stage-Wave2DInitialization.ps1"
)){
    Copy-Item (Join-Path $pkgRoot "scripts\$n") (Join-Path $root "scripts\$n") -Force
}

$scope=[ordered]@{
    wave="2D"
    baseline_tag=$spec.baseline_tag
    baseline_commit_sha=$tagSha
    scope_count=0
    controls=@()
    population_policy="NO_IMPLICIT_CARRY_FORWARD"
    status="PASS"
}
$scope|ConvertTo-Json -Depth 20|Set-Content (Join-Path $root "registry\wave2d\scope.json") -Encoding UTF8

$population=[ordered]@{
    wave="2D"
    population_count=0
    items=@()
    source_wave="2C"
    carry_forward_performed=$false
    status="PASS"
}
$population|ConvertTo-Json -Depth 20|Set-Content (Join-Path $root "registry\wave2d\population.json") -Encoding UTF8

$record=[ordered]@{
    wave="2D"
    initialized_at_utc=[DateTime]::UtcNow.ToString("o")
    status="PASS"
    branch=$Branch
    baseline_tag=$spec.baseline_tag
    baseline_commit_sha=$tagSha
    baseline_state=$reg.baseline_state
    scope_count=0
    population_count=0
    carry_forward_performed=$false
    wave2c_mutation_detected=$false
    initialization_state="INITIALIZED"
}
$record|ConvertTo-Json -Depth 20|Set-Content (Join-Path $root "generated\wave2d\initialization_record.json") -Encoding UTF8

& (Join-Path $root "scripts\Test-Wave2DProtectedBaseline.ps1") -EMSPath $root
if(-not $?){Fail "Wave 2C protected-baseline gate failed"}

Write-Host "`nPASS: Wave 2D initialized from clean main using external runner." -ForegroundColor Green
