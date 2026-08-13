[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$expected=@(
 "registry\hayes_verify_live_evaluation_certification_spec.json",
 "schemas\hayes_verify_ems_return_envelope.schema.json",
 "scripts\Certify-HayesVerifyLiveEvaluation.py",
 "scripts\Build-HayesVerifyEMSReturnEnvelope.py",
 "scripts\Validate-HayesVerifyEMSReturnEnvelope.py",
 "scripts\Run-HayesVerifyLiveEvaluationCertification.ps1",
 "scripts\Show-HayesVerifyLiveEvaluationCertification.ps1"
)
$missing=@()
foreach($rel in $expected){if(-not(Test-Path (Join-Path $HayesPath $rel))){$missing+=$rel}}
if($missing.Count){$missing|%{Write-Host "MISSING: $_"}; throw "Installation incomplete"}
Write-Host "PASS: live evaluation certification tooling installation verified." -ForegroundColor Green
