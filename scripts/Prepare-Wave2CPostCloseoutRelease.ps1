[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Stage
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C RELEASE PREP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2c_post_closeout_release_spec.json"
$out=Join-Path $root "release\wave2c\post-closeout"
New-Item -ItemType Directory -Force -Path $out|Out-Null

$py=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$py=$candidate}
}
if(-not $py){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$py=$cmd.Source}
}
if(-not $py){Fail "No usable Python interpreter found."}

Write-Host "=== Certify Wave 2C post-closeout branch state ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Certify-Wave2CPostCloseoutBranch.py") `
    --root $root `
    --spec $spec `
    --out (Join-Path $out "branch_certification.json")
if($LASTEXITCODE){Fail "Branch certification failed."}

Write-Host "`n=== Validate changed-path scope ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Validate-Wave2CPostCloseoutScope.py") `
    --root $root `
    --spec $spec `
    --report (Join-Path $out "scope_validation.json")
if($LASTEXITCODE){Fail "Changed-path scope validation failed."}

Write-Host "`n=== Freeze Wave 2C closeout artifacts ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Freeze-Wave2CPostCloseoutArtifacts.py") `
    --root $root `
    --spec $spec `
    --outdir $out
if($LASTEXITCODE){Fail "Artifact freeze/package creation failed."}

if(-not $Stage){
    Write-Host "`nPASS: Wave 2C release preparation validated. No files staged." -ForegroundColor Green
    Write-Host "Review release\wave2c\post-closeout, then rerun with -Stage."
    exit 0
}

Write-Host "`n=== Stage approved Wave 2C durable paths ===" -ForegroundColor Cyan

$approved=@(
    "registry",
    "schemas",
    "evidence",
    "registers",
    "scripts",
    "tests",
    ".github/workflows",
    "release/wave2c"
)

foreach($p in $approved){
    if(Test-Path (Join-Path $root $p)){
        git -C $root add -- $p
        if($LASTEXITCODE){Fail "git add failed for $p"}
    }
}

Write-Host "`nStaged paths:" -ForegroundColor Cyan
git -C $root diff --cached --name-status

Write-Host "`nPASS: approved Wave 2C release paths staged. No commit or push performed." -ForegroundColor Green
