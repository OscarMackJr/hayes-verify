[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot
Copy-Item "$pkg\registry\control_definition_recovery_config.json" "$EMSPath\registry\control_definition_recovery_config.json" -Force
foreach($n in @(
 "Recover-ControlDefinitions.py",
 "Apply-RecoveredControlDefinitions.py",
 "Run-ControlDefinitionRecovery.ps1",
 "Apply-ControlDefinitionRecovery.ps1",
 "Show-ControlDefinitionRecovery.ps1"
)){
 Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
foreach($p in @("Recover-ControlDefinitions.py","Apply-RecoveredControlDefinitions.py")){
 & $py -m py_compile "$EMSPath\scripts\$p"
 if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}
Write-Host "Control Definition Recovery tooling installed." -ForegroundColor Green
