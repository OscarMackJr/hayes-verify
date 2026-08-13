[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$pkg=Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force|Out-Null
Copy-Item "$pkg\registry\hs_continuous_compliance_spec.json" "$EMSPath\registry\hs_continuous_compliance_spec.json" -Force
Copy-Item "$pkg\schemas\hs_continuous_compliance_envelope.schema.json" "$EMSPath\schemas\hs_continuous_compliance_envelope.schema.json" -Force
Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py" "$EMSPath\scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py" -Force
foreach($n in @("Validate-HSContinuousCompliance.py","Qualify-HSContinuousCompliance.py","Promote-HSContinuousCompliance.py","Record-CTRL072-Remediation.ps1","Run-Wave2B23-HSContinuousCompliance.ps1","Show-Wave2B23-HSContinuousCompliance.ps1")){Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
foreach($p in @("scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py","scripts\Validate-HSContinuousCompliance.py","scripts\Qualify-HSContinuousCompliance.py","scripts\Promote-HSContinuousCompliance.py")){& $py -m py_compile "$EMSPath\$p";if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}}
Write-Host "Wave 2B.2.3 tooling installed." -ForegroundColor Green
