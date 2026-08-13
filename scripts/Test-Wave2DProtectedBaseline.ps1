[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D PROTECTION BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Get-Content (Join-Path $root "registry\wave2d_initialization_spec.json") -Raw|ConvertFrom-Json
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne $spec.branch){Fail "Expected $($spec.branch); current=$branch"}

$changes=@(git -C $root status --porcelain)
$bad=@()
foreach($line in $changes){
    $p=$line.Substring(3).Replace("\","/")
    foreach($prefix in @($spec.wave2c_protected_roots)){
        if($p.StartsWith($prefix)){
            $bad += $line
            break
        }
    }
}
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Wave 2C protected artifacts were modified."
}
Write-Host "PASS: no Wave 2C protected artifact mutation detected." -ForegroundColor Green
