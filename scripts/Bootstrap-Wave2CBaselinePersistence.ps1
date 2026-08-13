[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Branch="chore/wave2c-baseline-registration"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C BASELINE PERSISTENCE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Get-Content (Join-Path $root "registry\wave2c_baseline_persistence_spec.json") -Raw|ConvertFrom-Json

$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "main"){Fail "Expected main; current=$branch"}

git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed"}

$head=(git -C $root rev-parse HEAD).Trim()
$origin=(git -C $root rev-parse origin/main).Trim()
if($head -ne $origin){Fail "HEAD != origin/main"}

# Remove transient local-only artifacts from main before branching.
foreach($rel in @($spec.transient_paths)){
    $full=Join-Path $root ($rel -replace '/','\')
    if(Test-Path $full){
        $tracked=git -C $root ls-files --error-unmatch -- $rel 2>$null
        if($LASTEXITCODE -eq 0){
            Fail "Transient path is unexpectedly tracked: $rel"
        }
        Remove-Item $full -Recurse -Force
        Write-Host "Removed transient local artifact: $rel"
    }
}

$status=@(git -C $root status --porcelain)
$allowed=@($spec.durable_paths + "registry/wave2c_baseline_persistence_spec.json")
$bad=@()
foreach($line in $status){
    $p=$line.Substring(3).Replace("\","/")
    if($p -notin $allowed){$bad += $line}
}
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Unexpected working-tree changes remain."
}

git -C $root switch -c $Branch
if($LASTEXITCODE){Fail "Failed to create branch $Branch"}

Write-Host "PASS: baseline-persistence branch created." -ForegroundColor Green
