[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ScopedRegistry,
    [Parameter(Mandatory = $true)][string]$RepositoryPathOverrides,
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$HayesPath = (Split-Path -Parent $PSScriptRoot),
    [string]$RepositoryMap,
    [string]$OrganizationTargets,
    [string]$RuntimeApplicability,
    [string]$OrganizationEvidenceOverrides,
    [string]$PythonPath
)
$ErrorActionPreference = "Stop"
function Fail([string]$Message) { throw "HAYES IMMUTABLE BATCH BLOCKED: $Message" }
function Resolve-HayesPython {
    param([string]$Requested, [string]$Root)
    $candidates = @()
    if ($Requested) { $candidates += $Requested }
    if ($env:VIRTUAL_ENV) { $candidates += (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe") }
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if ($onPath) { $candidates += $onPath.Source }
    $candidates += (Join-Path $Root ".venv\Scripts\python.exe")
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (-not (Test-Path -LiteralPath $candidate)) { continue }
        & $candidate -c "import hayes_verify, jsonschema" 2>$null
        if ($LASTEXITCODE -eq 0) { return (Resolve-Path $candidate).Path }
    }
    Fail "no usable Python interpreter with hayes_verify and jsonschema was found; provide -PythonPath or activate the required environment"
}
$root = (Resolve-Path $HayesPath).Path
$ems = (Resolve-Path $EMSPath).Path
if (-not $RepositoryMap) { $RepositoryMap = Join-Path $root "registry\wave2d_repository_map.json" }
if (-not $OrganizationTargets) { $OrganizationTargets = Join-Path $root "registry\wave2d_organization_targets.json" }
if (-not $RuntimeApplicability) { $RuntimeApplicability = Join-Path $root "registry\wave2d_organization_runtime_applicability.json" }
$scoped = (Resolve-Path $ScopedRegistry).Path
$overrides = (Resolve-Path $RepositoryPathOverrides).Path
$map = (Resolve-Path $RepositoryMap).Path
$organizationTargets = (Resolve-Path $OrganizationTargets).Path
$runtimeApplicability = (Resolve-Path $RuntimeApplicability).Path
$spec = Join-Path $root "registry\wave2d_batch_run_identity_spec.json"
$latest = Join-Path $root "generated\wave2d\batch\latest_run.json"
$active = Join-Path $root "generated\wave2d\batch\active_runtime_registry.json"
$backup = "$active.backup"
$python = Resolve-HayesPython -Requested $PythonPath -Root $root
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($active)) | Out-Null
Write-Host "Wave 2D batch Python interpreter: $python"
if (Test-Path -LiteralPath $active) { Copy-Item -LiteralPath $active -Destination $backup -Force }
try {
    Copy-Item -LiteralPath $scoped -Destination $active -Force
    & $python "$root\scripts\create_wave2d_batch_run.py" --root $root --spec $spec
    if ($LASTEXITCODE) { Fail "batch identity creation failed" }
    $builderArgs = @("$root\scripts\build_wave2d_batch_requests_scoped.py", "--ems-root", $ems, "--run-identity", $latest, "--repository-map", $map, "--repository-path-overrides", $overrides, "--organization-targets", $organizationTargets, "--runtime-applicability", $runtimeApplicability)
    if ($OrganizationEvidenceOverrides) { $builderArgs += @("--organization-evidence-overrides", $OrganizationEvidenceOverrides) }
    & $python @builderArgs
    if ($LASTEXITCODE) { Fail "request build failed" }
    & $python "$root\scripts\run_wave2d_batch_registry_scoped.py" --root $root --run-identity $latest --registry $active --runner "$root\scripts\run_registry_evaluator.py"
    if ($LASTEXITCODE) { Fail "batch evaluation failed" }
}
finally {
    if (Test-Path -LiteralPath $backup) { Move-Item -LiteralPath $backup -Destination $active -Force } elseif (Test-Path -LiteralPath $active) { Remove-Item -LiteralPath $active -Force }
}
Write-Host "PASS: immutable Wave 2D Hayes batch complete." -ForegroundColor Green