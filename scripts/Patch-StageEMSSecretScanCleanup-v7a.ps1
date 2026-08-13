[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"

$target = Join-Path $EMSPath "scripts\Stage-EMSSecretScanCleanup-v7.ps1"
if(-not(Test-Path $target)){
    throw "Stage-EMSSecretScanCleanup-v7.ps1 not found: $target"
}

$backup = "$target.pre-v7a.bak"
Copy-Item $target $backup -Force

$text = Get-Content $target -Raw

$old = @'
    $staged = @(git diff --cached --name-only)

    $transientStillAdded = @(
        $staged | Where-Object {
            $_ -match '^scripts/(Patch|Test|Install)-EMSValidateSecretScan'
        }
    )

    if($transientStillAdded.Count -gt 0){
        throw "Transient secret-scan maintenance scripts are still staged: $($transientStillAdded -join ', ')"
    }
'@

$new = @'
    $stagedStatus = @(git diff --cached --name-status)

    $badTransient = @()

    foreach($entry in $stagedStatus){
        if([string]::IsNullOrWhiteSpace($entry)){ continue }

        $parts = $entry -split "`t"
        $status = $parts[0]
        $path = $parts[-1]

        if($path -match '^scripts/(Patch|Test|Install)-EMSValidateSecretScan'){
            # Deletion is the desired cleanup outcome. Any add/modify/rename/copy
            # means transient maintenance tooling would remain in the baseline.
            if($status -notmatch '^D'){
                $badTransient += "$status`t$path"
            }
        }
    }

    if($badTransient.Count -gt 0){
        throw "Transient secret-scan maintenance scripts remain staged as non-deletions: $($badTransient -join ', ')"
    }
'@

if(-not $text.Contains($old)){
    Copy-Item $backup $target -Force
    throw "Expected v7 staging guard not found; original restored."
}

$text = $text.Replace($old,$new)
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
    throw "v7a parser validation failed; original restored."
}

Write-Host "PASS: v7 staging guard patched to allow transient-script deletions." -ForegroundColor Green
Write-Host "Backup: $backup"
