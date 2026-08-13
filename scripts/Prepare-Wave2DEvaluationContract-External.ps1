[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Branch="feature/wave2d-evaluation-contract"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D CONTRACT PREP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$current=(git -C $root branch --show-current).Trim()
if($current -ne "main"){Fail "Expected main; current=$current"}

git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed"}
if((git -C $root rev-parse HEAD).Trim() -ne (git -C $root rev-parse origin/main).Trim()){Fail "HEAD != origin/main"}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){
    $status|ForEach-Object{Write-Host $_}
    Fail "main must be clean"
}

git -C $root switch -c $Branch
if($LASTEXITCODE){Fail "Failed to create branch $Branch"}

New-Item -ItemType Directory -Force -Path "$root\scripts","$root\registry\wave2d","$root\schemas\contracts"|Out-Null
Copy-Item "$pkg\registry\wave2d_evaluation_contract_spec.json" "$root\registry\wave2d_evaluation_contract_spec.json" -Force
Copy-Item "$pkg\registry\wave2d\evaluation_status_vocabulary.json" "$root\registry\wave2d\evaluation_status_vocabulary.json" -Force
Copy-Item "$pkg\schemas\contracts\*" "$root\schemas\contracts\" -Force
foreach($n in @(
  "Freeze-Wave2DEvaluationContract.py",
  "Validate-Wave2DEvaluationContract.py",
  "Run-Wave2DEvaluationContractFreeze.ps1",
  "Show-Wave2DEvaluationContractFreeze.ps1",
  "Stage-Wave2DEvaluationContractFreeze.ps1"
)){
  Copy-Item "$pkg\scripts\$n" "$root\scripts\$n" -Force
}

Write-Host "PASS: Wave 2D evaluation-contract branch prepared." -ForegroundColor Green
