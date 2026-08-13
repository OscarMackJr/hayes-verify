[CmdletBinding()]
param(
    [string]$EMSPath = (Get-Location).Path,
    [switch]$Promote
)

$ErrorActionPreference = "Stop"
Push-Location $EMSPath
try {
    Write-Host "=== Validate hotfix ==="
    & ".\scripts\Test-Wave2B23a-CTRL075-Hotfix.ps1"
    if ($LASTEXITCODE -ne 0) { throw "Hotfix validation failed." }

    Write-Host "`n=== Rerun CTRL-075 refinement without promotion ==="
    & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1"
    if ($LASTEXITCODE -ne 0) { throw "CTRL-075 refinement run failed." }

    Write-Host "`n=== Show corrected result ==="
    & ".\scripts\Show-Wave2B23a-CTRL075Refinement.ps1"
    if ($LASTEXITCODE -ne 0) { throw "CTRL-075 result display failed." }

    if ($Promote) {
        Write-Host "`n=== Promotion requested ==="
        & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1" -Promote
        if ($LASTEXITCODE -ne 0) { throw "CTRL-075 promotion failed." }
    } else {
        Write-Host "`nNo promotion requested. Review CTRL-075 qualification first."
    }
}
finally {
    Pop-Location
}
