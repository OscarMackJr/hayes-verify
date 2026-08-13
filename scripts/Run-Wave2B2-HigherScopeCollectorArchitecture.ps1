[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop";$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
$gaps=Join-Path $EMSPath "generated\wave2\higher-scope-evidence-qualified\qualified_evidence_gaps.csv";$scope=Join-Path $EMSPath "registry\control_scope_registry.yaml";$catalog=Join-Path $EMSPath "registry\control_catalog.yaml"
foreach($p in @($gaps,$scope,$catalog)){if(-not(Test-Path $p)){throw "Required input not found: $p"}}
$out=Join-Path $EMSPath "generated\wave2\higher-scope-collector-architecture";New-Item -ItemType Directory -Path $out -Force|Out-Null
Write-Host "Building higher-scope evidence requirements and collector registry..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Build-HigherScopeEvidenceArchitecture.py") --scope-registry $scope --catalog $catalog --gaps $gaps --outdir $out;if($LASTEXITCODE-ne 0){throw "Architecture build failed."}
Write-Host "`nValidating fail-closed collector architecture..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-HigherScopeEvidenceArchitecture.py") --requirements (Join-Path $out "higher_scope_evidence_requirements.csv") --collectors (Join-Path $out "higher_scope_collector_registry.csv") --report (Join-Path $out "architecture_validation.json");if($LASTEXITCODE-ne 0){throw "Architecture validation failed."}
Write-Host "`nCreating disabled collector scaffolds..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\New-HigherScopeCollectorScaffolds.py") --collectors (Join-Path $out "higher_scope_collector_registry.csv") --outdir (Join-Path $EMSPath "scripts\collectors\higher-scope");if($LASTEXITCODE-ne 0){throw "Scaffold generation failed."}
Write-Host "`nWave 2B.2 collector architecture complete. No evidence was promoted." -ForegroundColor Green
