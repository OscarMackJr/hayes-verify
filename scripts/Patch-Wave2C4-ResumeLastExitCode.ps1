[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Resume-Wave2C4-Closeout.ps1"
if(-not(Test-Path $target)){throw "Resume script not found: $target"}

$backup="$target.pre-lastexitcode-hotfix.bak"
Copy-Item $target $backup -Force

$lines=[System.Collections.Generic.List[string]](Get-Content $target)

$changed=0

for($i=0;$i -lt $lines.Count;$i++){
    $trim=$lines[$i].Trim()

    if($trim -eq 'if($LASTEXITCODE){throw "Already-promoted CTRL-080 state validation failed."}'){
        $lines[$i]='if(-not $?){throw "Already-promoted CTRL-080 state validation failed."}'
        $changed++
        continue
    }

    if($trim -eq 'if($LASTEXITCODE){throw "Wave 2C.4 closeout resume failed."}'){
        $lines[$i]='if(-not $?){throw "Wave 2C.4 closeout resume failed."}'
        $changed++
        continue
    }
}

if($changed -lt 1){
    Copy-Item $backup $target -Force
    throw "Expected stale LASTEXITCODE checks not found; original restored."
}

Set-Content $target $lines -Encoding UTF8

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,[ref]$tokens,[ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors|Format-List
    throw "Patched resume script failed parser validation; original restored."
}

Write-Host "PASS: Wave 2C.4 resume stale-LASTEXITCODE hotfix applied." -ForegroundColor Green
Write-Host "Changed checks: $changed"
Write-Host "Backup: $backup"
