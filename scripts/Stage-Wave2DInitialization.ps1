[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
& (Join-Path $root "scripts\Test-Wave2DProtectedBaseline.ps1") -EMSPath $root
if(-not $?){Fail "Protected baseline validation failed"}

$allowed=@(
    "registry/wave2d_initialization_spec.json",
    "schemas/wave2d_initialization_record.schema.json",
    "registry/wave2d/scope.json",
    "registry/wave2d/population.json",
    "generated/wave2d/initialization_record.json",
    "scripts/Test-Wave2DProtectedBaseline.ps1",
    "scripts/Show-Wave2DInitialization.ps1",
    "scripts/Stage-Wave2DInitialization.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected initialization artifact: $rel"}
    git -C $root add -- $rel
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

$staged=@(git -C $root diff --cached --name-only)
$bad=@($staged|Where-Object{$_ -notin $allowed})
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Out-of-scope staged files detected."
}
git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D initialization staged." -ForegroundColor Green
