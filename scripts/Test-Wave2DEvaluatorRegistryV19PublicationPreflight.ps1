[CmdletBinding()]
param([string]$HayesPath = (Split-Path -Parent $PSScriptRoot), [string]$PythonPath = "python")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path $HayesPath).Path
function RequireHash($path, $expected) { if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() -ne $expected) { throw "v1.9 publication blocked: hash mismatch $path" } }
RequireHash "$root\registry\wave2d_evaluator_registry_v1_9.json" "4336fa4a7391d68fc45dc8fe9051ccfbbdbc9f06e9d75c19630b3111524dae97"
RequireHash "$root\generated\wave2d\evaluator-expansion\test-quality-v19-verification\verification_manifest.json" "47479400121e86f8860b57974928b4fe53c561124169c08ef244d289a951878a"
RequireHash "$root\generated\wave2d\evaluator-expansion\test_quality_registry_v1_9_certification.json" "8cb91343b69f3c99915659f3a8d6ec7faca43be41b68e4fe30060f52cf2d1808"
& $PythonPath -m pytest -q
if ($LASTEXITCODE) { throw "v1.9 publication blocked: pytest failed" }
Write-Host "PASS: Wave 2D v1.9 publication preflight"