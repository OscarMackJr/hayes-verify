$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
& "$PSScriptRoot/Test-Wave2DEvaluatorRegistryV18PublicationPreflight.ps1"
if ($LASTEXITCODE -ne 0) { throw "Publication preflight failed" }
$paths = Get-Content -LiteralPath "registry/wave2d_evaluator_registry_v1_8_publication_allowlist.txt"
foreach ($path in $paths) {
    if (!(Test-Path -LiteralPath $path)) { throw "Allowlisted publication path is absent: $path" }
    git add -f -- $path
    if ($LASTEXITCODE -ne 0) { throw "Failed to stage: $path" }
}
$staged = @(git diff --cached --name-only)
foreach ($path in $staged) { if ($path -notin $paths) { throw "Unexpected staged path: $path" } }
