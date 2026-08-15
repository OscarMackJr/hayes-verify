$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
& "$PSScriptRoot/Stage-Wave2DEvaluatorRegistryV18ForPublish.ps1"
git commit -m "publish Wave 2D evaluator registry v1.8 and certify Priority-2 completion"
if ($LASTEXITCODE -ne 0) { throw "Commit failed" }
git push origin "feature/wave2d-evaluator-registry-v1-8-priority2-complete"
if ($LASTEXITCODE -ne 0) { throw "Push failed" }
