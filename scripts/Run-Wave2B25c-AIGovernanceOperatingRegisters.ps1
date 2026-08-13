[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$reg=Join-Path $EMSPath "registers\ai-governance"
$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-operating-registers"
New-Item -ItemType Directory -Path $out -Force|Out-Null

$defs=@(
    @{Register="ai_platform_register.json";Schema="ai_platform_register.schema.json"},
    @{Register="ai_data_handling_assessment.json";Schema="ai_data_handling_assessment.schema.json"},
    @{Register="ai_security_review_register.json";Schema="ai_security_review_register.schema.json"}
)

Write-Host "Validating AI governance operating registers..." -ForegroundColor Cyan
foreach($d in $defs){
    & $py (Join-Path $EMSPath "scripts\Validate-AIGovernanceRegister.py") `
      --register (Join-Path $reg $d.Register) `
      --schema (Join-Path $EMSPath "schemas\$($d.Schema)") `
      --report (Join-Path $out "$($d.Register).validation.json")
    if($LASTEXITCODE-ne 0){throw "Register validation failed: $($d.Register)"}
}

Write-Host ""
Write-Host "Capturing operating evidence..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Capture-AIGovernanceOperatingEvidence.py") `
  --register-dir $reg `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "AI governance evidence capture failed."}

if($Promote){
    Write-Host ""
    Write-Host "Promoting only controls with qualifying populated operating records..." -ForegroundColor Cyan
    & $py (Join-Path $EMSPath "scripts\Promote-AIGovernanceOperatingRegisterEvidence.py") `
      --envelopes (Join-Path $out "evidence_envelopes.jsonl") `
      --evidence-root (Join-Path $EMSPath "evidence") `
      --report (Join-Path $out "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "AI governance register promotion failed."}

    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}
else{
    Write-Host ""
    Write-Host "No evidence promoted. Empty or non-qualifying registers remain WARNING." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.5c complete." -ForegroundColor Green
