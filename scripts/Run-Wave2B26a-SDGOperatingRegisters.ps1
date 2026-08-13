[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$reg=Join-Path $EMSPath "registers\security-data-governance"
$base=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance\assertion_evidence_matrix.csv"
$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance-requalified"
New-Item -ItemType Directory -Path $out -Force|Out-Null

if(-not(Test-Path $base)){throw "Base Wave 2B.2.6 assertion matrix not found."}

$defs=@(
 @{r="data_classification_register.json";s="data_classification_register.schema.json"},
 @{r="data_retention_register.json";s="data_retention_register.schema.json"},
 @{r="production_data_protection_register.json";s="production_data_protection_register.schema.json"}
)

Write-Host "Validating Security & Data Governance operating registers..." -ForegroundColor Cyan
foreach($d in $defs){
 & $py (Join-Path $EMSPath "scripts\Validate-SDGRegister.py") `
   --register (Join-Path $reg $d.r) `
   --schema (Join-Path $EMSPath "schemas\$($d.s)") `
   --report (Join-Path $out "$($d.r).validation.json")
 if($LASTEXITCODE-ne 0){throw "Register validation failed: $($d.r)"}
}

Write-Host ""
Write-Host "Capturing register-backed operating evidence..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Capture-SDGRegisterEvidence.py") `
  --register-dir $reg `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "Register evidence capture failed."}

Write-Host ""
Write-Host "Requalifying Security & Data Governance controls..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Requalify-HSSecurityDataGovernance.py") `
  --base-matrix $base `
  --register-evidence (Join-Path $out "register_assertion_evidence.csv") `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "Requalification failed."}

if($Promote){
 Write-Host ""
 Write-Host "Promoting only requalified controls..." -ForegroundColor Cyan
 & $py (Join-Path $EMSPath "scripts\Promote-HSSecurityDataGovernance-Requalified.py") `
   --qualified (Join-Path $out "qualified_security_data_governance_requalified.csv") `
   --matrix (Join-Path $out "assertion_evidence_matrix_requalified.csv") `
   --evidence-root (Join-Path $EMSPath "evidence") `
   --report (Join-Path $out "promotion_report.json")
 if($LASTEXITCODE-ne 0){throw "Promotion failed."}

 & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
 if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}
else{
 Write-Host ""
 Write-Host "No evidence promoted. Empty/incomplete registers remain fail-closed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.6a complete." -ForegroundColor Green
