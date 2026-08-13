[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"
$target = Join-Path $EMSPath "scripts\Finalize-Wave2B.ps1"

if(-not(Test-Path $target)){
    throw "Finalize-Wave2B.ps1 not found."
}

$text = Get-Content $target -Raw
$backup = "$target.pre-branch-closeout-patch.bak"
Copy-Item $target $backup -Force

# Remove generated/wave2 from the git add list if present.
$text = $text -replace '(?m)^\s*"generated/wave2",?\s*\r?\n',''
$text = $text -replace '(?m)^\s*generated/wave2\s*$',''

Set-Content $target $text -Encoding UTF8

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors | Format-List
    throw "Finalize-Wave2B.ps1 parser validation failed; original restored."
}

Write-Host "PASS: Finalize-Wave2B.ps1 patched to stop staging ignored generated/wave2 content." -ForegroundColor Green
Write-Host "Backup: $backup"
