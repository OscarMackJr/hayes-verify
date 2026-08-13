[CmdletBinding()]
param(
    [string]$EMSPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$collector = Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
if (-not (Test-Path $collector)) { throw "Collector not found: $collector" }

$text = Get-Content $collector -Raw
$checks = @(
    [pscustomobject]@{
        Check = "DefinesStatusFunction"
        Pass  = [bool]($text -match '(?m)^\s*def\s+status\s*\(')
    },
    [pscustomobject]@{
        Check = "NoStatusAssignmentShadow"
        Pass  = -not [bool]($text -match '(?m)^\s*status\s*=(?!=)')
    },
    [pscustomobject]@{
        Check = "CallsStatusFunction"
        Pass  = [bool]($text -match '\bstatus\s*\(\s*A\s*\)')
    },
    [pscustomobject]@{
        Check = "UsesRenamedCollectorStatus"
        Pass  = [bool]($text -match '\bcollector_status\b')
    }
)

& python -m py_compile $collector
$compilePass = ($LASTEXITCODE -eq 0)
$checks += [pscustomobject]@{ Check = "PythonCompile"; Pass = $compilePass }

$checks | Format-Table -AutoSize
if ($checks.Pass -contains $false) {
    throw "CTRL-075 hotfix validation failed."
}
Write-Host "PASS: CTRL-075 hotfix validation succeeded."
