[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
$root=(Resolve-Path $HayesPath).Path

python "$root\scripts\Certify-HayesVerifyPilot.py" --root $root
if($LASTEXITCODE){
    throw "Hayes Verify pilot certification failed."
}

Write-Host "PASS: Hayes Verify pilot vertical slice certified." -ForegroundColor Green
