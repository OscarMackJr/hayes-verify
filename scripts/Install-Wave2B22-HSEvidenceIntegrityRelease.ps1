[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$pkg=Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force|Out-Null
Copy-Item "$pkg\registry\hs_evidence_integrity_release_spec.json" "$EMSPath\registry\hs_evidence_integrity_release_spec.json" -Force
Copy-Item "$pkg\schemas\hs_evidence_integrity_release_envelope.schema.json" "$EMSPath\schemas\hs_evidence_integrity_release_envelope.schema.json" -Force
Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-HSEvidenceIntegrityRelease.py" "$EMSPath\scripts\collectors\higher-scope\Collect-HSEvidenceIntegrityRelease.py" -Force
foreach($n in @("Validate-HSEvidenceIntegrityRelease.py","Qualify-HSEvidenceIntegrityRelease.py","Promote-HSEvidenceIntegrityRelease.py","Run-Wave2B22-HSEvidenceIntegrityRelease.ps1","Show-Wave2B22-HSEvidenceIntegrityRelease.ps1")){Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
foreach($p in @("scripts\collectors\higher-scope\Collect-HSEvidenceIntegrityRelease.py","scripts\Validate-HSEvidenceIntegrityRelease.py","scripts\Qualify-HSEvidenceIntegrityRelease.py","scripts\Promote-HSEvidenceIntegrityRelease.py")){& $py -m py_compile "$EMSPath\$p";if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}}
Write-Host "Wave 2B.2.2 tooling installed." -ForegroundColor Green
