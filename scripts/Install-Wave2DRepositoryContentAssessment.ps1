[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null
foreach($n in @("Discover-Wave2DRepositoryPaths.py","Assess-Wave2DRepositoryContent.py","Prepare-Wave2DAssistedHumanReview.py","Run-Wave2DRepositoryContentAssessment.ps1","Review-Wave2DAssistedApplicability.ps1","Show-Wave2DRepositoryContentAssessment.ps1")){Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force}
Copy-Item "$pkg\registry\wave2d_repository_content_assessment_spec.json" "$EMSPath\registry\wave2d_repository_content_assessment_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_repository_content_assessment_summary.schema.json" "$EMSPath\schemas\wave2d_repository_content_assessment_summary.schema.json" -Force
Write-Host "Wave 2D Repository Content Applicability Assessment tooling installed." -ForegroundColor Green
