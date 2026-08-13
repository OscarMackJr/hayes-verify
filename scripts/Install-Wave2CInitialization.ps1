[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$here=Split-Path -Parent $MyInvocation.MyCommand.Path;$pkg=Split-Path -Parent $here
New-Item -ItemType Directory -Path "$EMSPath\registry" -Force|Out-Null
New-Item -ItemType Directory -Path "$EMSPath\scripts" -Force|Out-Null
Copy-Item "$pkg\registry\wave2c_remediation_intake_spec.json" "$EMSPath\registry\wave2c_remediation_intake_spec.json" -Force
foreach($n in @("Build-Wave2CRemediationQueue.py","Validate-Wave2CRemediationQueue.py","Initialize-Wave2C.ps1","Show-Wave2CRemediationQueue.ps1")){
 Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
foreach($n in @("Build-Wave2CRemediationQueue.py","Validate-Wave2CRemediationQueue.py")){
 & $py -m py_compile (Join-Path $EMSPath "scripts\$n");if($LASTEXITCODE-ne 0){throw "Python syntax validation failed: $n"}
}
foreach($n in @("Initialize-Wave2C.ps1","Show-Wave2CRemediationQueue.ps1")){
 $t=$null;$e=$null;[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $EMSPath "scripts\$n"),[ref]$t,[ref]$e)|Out-Null
 if($e.Count-gt 0){$e|Format-List;throw "PowerShell parser validation failed: $n"}
}
Write-Host "Wave 2C Initialization & Remediation Intake tooling installed." -ForegroundColor Green
