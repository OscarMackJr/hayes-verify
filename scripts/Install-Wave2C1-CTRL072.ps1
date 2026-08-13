[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$pkg=Split-Path -Parent $here
Copy-Item "$pkg\registry\wave2c1_ctrl072_spec.json" "$EMSPath\registry\wave2c1_ctrl072_spec.json" -Force
Copy-Item "$pkg\schemas\wave2c1_ctrl072_evidence.schema.json" "$EMSPath\schemas\wave2c1_ctrl072_evidence.schema.json" -Force
foreach($n in @("Collect-Wave2C1-CTRL072.py","Validate-Wave2C1-CTRL072.py","Qualify-Wave2C1-CTRL072.py","Run-Wave2C1-CTRL072.ps1","Show-Wave2C1-CTRL072.ps1")){
 Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
foreach($n in @("Collect-Wave2C1-CTRL072.py","Validate-Wave2C1-CTRL072.py","Qualify-Wave2C1-CTRL072.py")){
 & $py -m py_compile (Join-Path $EMSPath "scripts\$n");if($LASTEXITCODE-ne 0){throw "Python syntax validation failed: $n"}
}
Write-Host "Wave 2C.1 CTRL-072 remediation tooling installed." -ForegroundColor Green
