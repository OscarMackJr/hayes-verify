[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Inspect-And-Merge-Wave2CPR.ps1"
if(-not(Test-Path $target)){throw "Merge gate script not found: $target"}

$backup="$target.pre-postpush-hotfix.bak"
Copy-Item $target $backup -Force

$lines=[System.Collections.Generic.List[string]](Get-Content $target)
$joined=$lines -join "`n"

if($joined -match 'Test-Wave2C-PostPushReadiness\.ps1'){
    Write-Host "Wave 2C merge gate already uses post-push readiness." -ForegroundColor Yellow
    exit 0
}

$replaced=$false
for($i=0;$i -lt $lines.Count;$i++){
    if($lines[$i] -match 'Test-Wave2C-PRReadiness\.ps1'){
        $lines[$i]=$lines[$i] -replace 'Test-Wave2C-PRReadiness\.ps1','Test-Wave2C-PostPushReadiness.ps1'
        $replaced=$true
    }
}

if(-not $replaced){
    Copy-Item $backup $target -Force
    throw "Expected pre-commit readiness call not found; original restored."
}

Set-Content $target $lines -Encoding UTF8

$tokens=$null;$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,[ref]$tokens,[ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors|Format-List
    throw "Patched merge gate failed parser validation; original restored."
}

Write-Host "PASS: Wave 2C merge gate patched for post-push readiness." -ForegroundColor Green
Write-Host "Backup: $backup"
