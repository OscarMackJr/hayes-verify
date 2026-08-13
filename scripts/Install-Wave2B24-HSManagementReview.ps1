[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$pkg=Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force|Out-Null
Copy-Item "$pkg\registry\hs_management_review_spec.json" "$EMSPath\registry\hs_management_review_spec.json" -Force
Copy-Item "$pkg\schemas\hs_management_review_envelope.schema.json" "$EMSPath\schemas\hs_management_review_envelope.schema.json" -Force
Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-HSManagementReview.py" "$EMSPath\scripts\collectors\higher-scope\Collect-HSManagementReview.py" -Force
foreach($n in @("Validate-HSManagementReview.py","Qualify-HSManagementReview.py","Promote-HSManagementReview.py","Run-Wave2B24-HSManagementReview.ps1","Show-Wave2B24-HSManagementReview.ps1")){Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
foreach($p in @("scripts\collectors\higher-scope\Collect-HSManagementReview.py","scripts\Validate-HSManagementReview.py","scripts\Qualify-HSManagementReview.py","scripts\Promote-HSManagementReview.py")){& $py -m py_compile "$EMSPath\$p";if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}}
Write-Host "Wave 2B.2.4 HS-MANAGEMENT-REVIEW tooling installed." -ForegroundColor Green
