[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$BaselinePath="C:\temp\standars\ems-local-archive\wave1-input\effective_compliance_postpolicy.csv",
    [switch]$PromoteAndCloseout
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.4 BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$branch=(git -C $root branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){Fail "Expected feature/wave2c-remediation; current=$branch"}

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

$out=Join-Path $root "generated\wave2c\annual-review"
$close=Join-Path $root "generated\wave2c\annual-review-closeout"
New-Item -ItemType Directory -Force -Path $out,$close|Out-Null

Write-Host "=== Wave 2C.4 initialize Annual EMS Review register ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Initialize-Wave2C4AnnualReview.py") --root $root
if($LASTEXITCODE){Fail "Annual review register initialization failed."}

Write-Host "`n=== Validate Annual EMS Review register ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Validate-Wave2C4AnnualReview.py") `
    --root $root `
    --report (Join-Path $out "register_validation.json")
if($LASTEXITCODE){Fail "Annual review register validation failed."}

Write-Host "`n=== Qualify EMS-CTRL-080 ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Qualify-Wave2C4AnnualReview.py") --root $root
if($LASTEXITCODE){Fail "CTRL-080 qualification failed."}

Write-Host "`n=== Review CTRL-080 evidence ===" -ForegroundColor Cyan
$args=@(
    (Join-Path $root "scripts\ReviewPromote-Wave2C4AnnualReview.py"),
    "--root",$root,
    "--outdir",$close
)
if($PromoteAndCloseout){$args += "--promote"}
& $py @args
if($LASTEXITCODE){Fail "CTRL-080 review/promotion failed."}

if(-not $PromoteAndCloseout){
    Write-Host "`nPASS: CTRL-080 review complete. No promotion performed." -ForegroundColor Green
    Write-Host "After reviewing evidence, rerun with -PromoteAndCloseout."
    exit 0
}

Write-Host "`n=== Rerun higher-scope / inheritance evaluation ===" -ForegroundColor Cyan
$inheritance=Join-Path $root "scripts\Run-Wave2B1-Inheritance.ps1"
if(Test-Path $inheritance){
    if(-not(Test-Path $BaselinePath)){Fail "Wave 1 baseline not found: $BaselinePath"}
    & $inheritance -BaselinePath $BaselinePath
    if($LASTEXITCODE){Fail "Inheritance rerun failed."}
}else{
    Fail "Inheritance runner not found."
}

Write-Host "`n=== Certify Wave 2C closeout ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Closeout-Wave2C4.py") `
    --root $root `
    --out (Join-Path $close "wave2c_closeout_certification.json")
if($LASTEXITCODE){Fail "Wave 2C closeout certification failed."}

Write-Host "`nPASS: Wave 2C closed with zero open remediation controls." -ForegroundColor Green
