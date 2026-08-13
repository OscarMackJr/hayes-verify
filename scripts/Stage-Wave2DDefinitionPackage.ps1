[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D DEFINITION STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$validation="$root\generated\wave2d\applicability-freeze\applicability_freeze_validation.json"
if(-not(Test-Path $validation)){Fail "Freeze validation artifact missing"}
$v=Get-Content $validation -Raw|ConvertFrom-Json
if($v.status -ne "PASS"){Fail "Freeze validation not PASS"}

# Stage all Wave 2D definition-phase artifacts already created on this branch,
# but nothing outside the controlled roots below.
$roots=@(
    "generated/wave2d/",
    "registry/wave2d/",
    "schemas/wave2d_",
    "registry/wave2d_",
    "scripts/"
)

$trackedCandidates=@()
$trackedCandidates += @(git -C $root ls-files --others --exclude-standard)
$trackedCandidates += @(git -C $root diff --name-only)
$trackedCandidates += @(git -C $root diff --cached --name-only)
$trackedCandidates=$trackedCandidates|Sort-Object -Unique

$allowed=@()
foreach($p in $trackedCandidates){
    $n=$p.Replace("\","/")
    if($n.StartsWith("generated/wave2d/") -or
       $n.StartsWith("registry/wave2d/") -or
       $n.StartsWith("schemas/wave2d_") -or
       $n.StartsWith("registry/wave2d_") -or
       $n.StartsWith("scripts/")){
        $allowed += $n
    }
}

# Explicitly reject unrelated scripts that are not Wave2D tooling.
$badScripts=@($allowed|Where-Object{$_.StartsWith("scripts/") -and $_ -notmatch 'Wave2D'})
if($badScripts.Count -gt 0){
    $badScripts|ForEach-Object{Write-Host $_}
    Fail "Non-Wave2D script(s) are present in candidate scope."
}

foreach($rel in $allowed){
    if($rel.StartsWith("generated/")){
        git -C $root add -f -- $rel
    }else{
        git -C $root add -- $rel
    }
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

Write-Host "=== Staged Wave 2D definition package ===" -ForegroundColor Cyan
git -C $root diff --cached --name-status

Write-Host "PASS: Wave 2D definition-phase artifacts staged." -ForegroundColor Green
