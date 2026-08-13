param(
    [switch]$Promote
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Out = Join-Path $Root "generated\wave2\higher-scope-collectors\ai-governance"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host "Collecting HS-AI-GOVERNANCE operating evidence..."
python (Join-Path $Root "scripts\collectors\higher-scope\Collect-HSAIGovernance.py") --root $Root --outdir $Out
if($LASTEXITCODE -ne 0){ throw "AI governance collector failed." }

python (Join-Path $Root "scripts\Validate-HSAIGovernance.py") --input (Join-Path $Out "evidence_envelopes.jsonl")
if($LASTEXITCODE -ne 0){ throw "Envelope validation failed." }

python (Join-Path $Root "scripts\Qualify-HSAIGovernance.py") --input (Join-Path $Out "evidence_envelopes.jsonl") --outdir $Out
if($LASTEXITCODE -ne 0){ throw "Qualification failed." }

if($Promote){
    python (Join-Path $Root "scripts\Promote-HSAIGovernance.py") `
        --input (Join-Path $Out "evidence_envelopes.jsonl") `
        --qualification (Join-Path $Out "qualification.csv") `
        --root $Root
    if($LASTEXITCODE -ne 0){ throw "Promotion failed." }

    $inheritance = Join-Path $Root "scripts\Run-Wave2B1-Inheritance.ps1"
    if(Test-Path $inheritance){
        & $inheritance
        if($LASTEXITCODE -ne 0){ throw "Inheritance rerun failed." }
    } else {
        Write-Warning "Run-Wave2B1-Inheritance.ps1 not found; promotion completed but inheritance was not rerun."
    }
} else {
    Write-Host "No evidence promoted. Review AI-governance qualification first."
}
Write-Host "Wave 2B.2.5 complete."
