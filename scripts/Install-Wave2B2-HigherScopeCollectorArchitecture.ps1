[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$pkg=Split-Path -Parent $PSScriptRoot;New-Item -ItemType Directory -Path "$EMSPath\registry" -Force|Out-Null;New-Item -ItemType Directory -Path "$EMSPath\scripts" -Force|Out-Null
Copy-Item "$pkg\registry\higher_scope_collector_families.json" "$EMSPath\registry\higher_scope_collector_families.json" -Force
foreach($n in @('Build-HigherScopeEvidenceArchitecture.py','Validate-HigherScopeEvidenceArchitecture.py','New-HigherScopeCollectorScaffolds.py','Run-Wave2B2-HigherScopeCollectorArchitecture.ps1','Show-Wave2B2-HigherScopeCollectorArchitecture.ps1')){Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"};foreach($n in @('Build-HigherScopeEvidenceArchitecture.py','Validate-HigherScopeEvidenceArchitecture.py','New-HigherScopeCollectorScaffolds.py')){& $py -m py_compile "$EMSPath\scripts\$n";if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $n"}}
Write-Host "Wave 2B.2 Higher-Scope Evidence Collector Architecture installed." -ForegroundColor Green
