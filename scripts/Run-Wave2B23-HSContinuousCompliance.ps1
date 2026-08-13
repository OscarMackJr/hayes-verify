[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)
$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance-qualified"
New-Item -ItemType Directory -Path $c -Force|Out-Null;New-Item -ItemType Directory -Path $q -Force|Out-Null
& (Join-Path $EMSPath "scripts\Record-CTRL072-Remediation.ps1") -EMSPath $EMSPath
& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py") --ems-root $EMSPath --outdir $c
if($LASTEXITCODE-ne 0){throw "Collector failed."}
& $py (Join-Path $EMSPath "scripts\Validate-HSContinuousCompliance.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --report (Join-Path $c "envelope_validation.json")
if($LASTEXITCODE-ne 0){throw "Envelope validation failed."}
& $py (Join-Path $EMSPath "scripts\Qualify-HSContinuousCompliance.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --outdir $q
if($LASTEXITCODE-ne 0){throw "Qualification failed."}
if($Promote){
 & $py (Join-Path $EMSPath "scripts\Promote-HSContinuousCompliance.py") --qualified (Join-Path $q "qualified_continuous_compliance.csv") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --evidence-root (Join-Path $EMSPath "evidence") --report (Join-Path $q "promotion_report.json")
 if($LASTEXITCODE-ne 0){throw "Promotion failed."}
 & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
 if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}else{Write-Host "No evidence promoted. Review qualification before using -Promote." -ForegroundColor Yellow}
Write-Host "Wave 2B.2.3 complete." -ForegroundColor Green
