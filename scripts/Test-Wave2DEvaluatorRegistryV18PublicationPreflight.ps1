$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = "C:\\temp\\standars\\hayes-verify\\.venv\\Scripts\\python.exe"
Set-Location $root

function Require-Hash([string]$Path, [string]$Expected) {
    if (!(Test-Path -LiteralPath $Path)) { throw "Missing required artifact: $Path" }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected) { throw "SHA-256 mismatch for $Path" }
}

Require-Hash "registry/wave2d_evaluator_registry_v1_8.json" "49175ae4062541de8a2a9b4a5d74ede7f838f8b6f88385080da363885afd8ad8"
Require-Hash "generated/wave2d/evaluator-expansion/documentation-governance-verification/verification_manifest.json" "7db2c2f9a6300b6de19530f5a010f1ab19b0635ef150a6583bab9a5c92701b8d"
& $python "scripts/validate_priority2_completion.py"
if ($LASTEXITCODE -ne 0) { throw "Priority-2 completion validation failed" }
Write-Output '{"status":"PASS","registry":"1.8","priority2":"21/21/0","families":"4/4/0"}'
