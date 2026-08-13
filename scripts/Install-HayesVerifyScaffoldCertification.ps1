[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$HayesPath\scripts","$HayesPath\registry","$HayesPath\schemas"|Out-Null
foreach($n in @(
  "Configure-HayesVerifyPytestBasetemp.py",
  "Certify-HayesVerifyScaffold.py",
  "Validate-HayesVerifyScaffoldCertification.py",
  "Run-HayesVerifyScaffoldCertification.ps1",
  "Show-HayesVerifyScaffoldCertification.ps1"
)){
  Copy-Item "$pkg\scripts\$n" "$HayesPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\hayes_verify_scaffold_certification_spec.json" "$HayesPath\registry\hayes_verify_scaffold_certification_spec.json" -Force
Copy-Item "$pkg\schemas\hayes_verify_scaffold_certification.schema.json" "$HayesPath\schemas\hayes_verify_scaffold_certification.schema.json" -Force

# keep local test temp out of git
$gitignore="$HayesPath\.gitignore"
if(Test-Path $gitignore){
  $content=Get-Content $gitignore -Raw
  if($content -notmatch '(?m)^\.pytest-temp/$'){
    Add-Content $gitignore ".pytest-temp/"
  }
}

Write-Host "Hayes Verify Windows Test Determinism & Scaffold Certification tooling installed." -ForegroundColor Green
