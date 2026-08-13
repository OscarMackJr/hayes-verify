[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D CONTRACT STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$v="$root\generated\wave2d\evaluation-contract\contract_freeze_validation.json"
if(-not(Test-Path $v)){Fail "Contract validation artifact missing"}
$j=Get-Content $v -Raw|ConvertFrom-Json
if($j.status -ne "PASS"){Fail "Contract validation not PASS"}
if($j.evaluation_performed -ne $false -or $j.promotion_performed -ne $false){Fail "Unexpected execution state"}

$allowed=@(
 "registry/wave2d_evaluation_contract_spec.json",
 "registry/wave2d/evaluation_status_vocabulary.json",
 "schemas/contracts/wave2d_evaluation_request.schema.json",
 "schemas/contracts/wave2d_evidence_record.schema.json",
 "schemas/contracts/wave2d_evaluation_result.schema.json",
 "schemas/contracts/wave2d_provenance_envelope.schema.json",
 "generated/wave2d/evaluation-contract/contract_freeze.json",
 "generated/wave2d/evaluation-contract/contract_freeze_validation.json",
 "scripts/Freeze-Wave2DEvaluationContract.py",
 "scripts/Validate-Wave2DEvaluationContract.py",
 "scripts/Run-Wave2DEvaluationContractFreeze.ps1",
 "scripts/Show-Wave2DEvaluationContractFreeze.ps1",
 "scripts/Stage-Wave2DEvaluationContractFreeze.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected contract artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D evaluation-contract artifacts staged." -ForegroundColor Green
