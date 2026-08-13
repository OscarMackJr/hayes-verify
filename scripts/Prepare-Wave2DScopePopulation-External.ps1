[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[string]$Branch="feature/wave2d-scope-population")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D SCOPE BOOTSTRAP BLOCKED: $m"}
$root=(Resolve-Path $EMSPath).Path
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$current=(git -C $root branch --show-current).Trim()
if($current -ne "main"){Fail "Expected main; current=$current"}
git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed"}
if((git -C $root rev-parse HEAD).Trim() -ne (git -C $root rev-parse origin/main).Trim()){Fail "HEAD != origin/main"}
$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){$status|ForEach-Object{Write-Host $_};Fail "main must be clean"}
git -C $root switch -c $Branch
if($LASTEXITCODE){Fail "Failed to create branch $Branch"}
New-Item -ItemType Directory -Force -Path "$root\scripts","$root\registry","$root\schemas"|Out-Null
Copy-Item "$pkg\registry\wave2d_scope_population_spec.json" "$root\registry\wave2d_scope_population_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_scope_population_summary.schema.json" "$root\schemas\wave2d_scope_population_summary.schema.json" -Force
foreach($n in @("Discover-Wave2DScopeCandidates.py","Initialize-Wave2DDecisions.py","Build-Wave2DScopePopulation.py","Validate-Wave2DScopePopulation.py","Run-Wave2DScopePopulation.ps1","Show-Wave2DScopePopulation.ps1","Stage-Wave2DScopePopulation.ps1")){Copy-Item "$pkg\scripts\$n" "$root\scripts\$n" -Force}
Write-Host "PASS: Wave 2D scope-definition branch prepared." -ForegroundColor Green
