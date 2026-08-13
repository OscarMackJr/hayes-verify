[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.2b BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){
    Fail "Expected feature/wave2c-remediation; current=$branch"
}

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

$spec=Join-Path $EMSPath "registry\wave2c2b_ai_governance_promotion_spec.json"
$out=Join-Path $EMSPath "generated\wave2c\ai-governance-promotion"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "=== Wave 2C.2b AI Governance evidence review ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Review-Wave2C2b-AIGovernance.py") `
    --ems-root $EMSPath `
    --spec $spec `
    --outdir $out
if($LASTEXITCODE-ne 0){Fail "AI governance evidence review failed."}

if(-not $Promote){
    Write-Host "`nPASS: AI Governance evidence review complete. No promotion performed." -ForegroundColor Green
    Write-Host "Review generated\wave2c\ai-governance-promotion\review_record.json"
    Write-Host "Then explicitly run:"
    Write-Host "  .\scripts\Run-Wave2C2b-AIGovernance.ps1 -Promote"
    exit 0
}

Write-Host "`n=== Explicitly promote AI Governance controls ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Promote-Wave2C2b-AIGovernance.py") `
    --ems-root $EMSPath `
    --spec $spec `
    --review (Join-Path $out "review_record.json") `
    --outdir $out
if($LASTEXITCODE-ne 0){Fail "AI governance promotion failed."}

Write-Host "`n=== Validate promotion and Wave 2C population ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-Wave2C2b-AIGovernance.py") `
    --ems-root $EMSPath `
    --record (Join-Path $out "promotion_record.json") `
    --queue $queue `
    --report (Join-Path $out "validation_report.json")
if($LASTEXITCODE-ne 0){Fail "AI governance promotion validation failed."}

Write-Host "`n=== Rerun higher-scope / inheritance evaluation ===" -ForegroundColor Cyan
$inheritance=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(Test-Path $inheritance){
    & $inheritance
    if($LASTEXITCODE-ne 0){Fail "Inheritance rerun failed."}
}else{
    Write-Host "Run-Wave2B1-Inheritance.ps1 not found; inheritance rerun skipped." -ForegroundColor Yellow
}

Write-Host "`nPASS: AI Governance promoted. Wave 2C remediation population reduced from seven to four." -ForegroundColor Green
