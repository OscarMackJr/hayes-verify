[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $target)){throw "Inheritance runner not found: $target"}

$backup="$target.pre-wave2c2b-baseline-hotfix.bak"
Copy-Item $target $backup -Force

$text=Get-Content $target -Raw

# Add BaselinePath parameter only if the script does not already expose one.
if($text -notmatch '\[string\]\$BaselinePath'){
    if($text -match '^\s*\[CmdletBinding\(\)\]\s*\r?\nparam\('){
        $text=$text -replace '(^\s*\[CmdletBinding\(\)\]\s*\r?\nparam\()',
            '$1' + "`r`n    [string]`$BaselinePath,"
    }
    elseif($text -match '^\s*param\('){
        $text=$text -replace '(^\s*param\()',
            '$1' + "`r`n    [string]`$BaselinePath,"
    }
    else{
        $text="[CmdletBinding()]`r`nparam([string]`$BaselinePath)`r`n" + $text
    }
}

# Replace the historical baseline discovery block with explicit-path-aware logic.
$needle='if\(-not \$baseline\)\{throw "Wave 1 compliance baseline not found\."\}'
if($text -notmatch $needle){
    Copy-Item $backup $target -Force
    throw "Expected Wave 1 baseline failure guard not found; original restored."
}

$replacement=@'
if($BaselinePath){
    if(-not(Test-Path $BaselinePath)){
        throw "Explicit Wave 1 compliance baseline not found: $BaselinePath"
    }
    $baseline=(Resolve-Path $BaselinePath).Path
}
if(-not $baseline){
    throw "Wave 1 compliance baseline not found. Supply -BaselinePath <path-to-effective_compliance_postpolicy.csv>."
}
'@

$text=[regex]::Replace($text,$needle,[System.Text.RegularExpressions.MatchEvaluator]{param($m)$replacement},1)
Set-Content $target $text -Encoding UTF8

$tokens=$null;$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,[ref]$tokens,[ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors|Format-List
    throw "Patched inheritance runner failed parser validation; original restored."
}

Write-Host "PASS: Run-Wave2B1-Inheritance.ps1 patched for explicit -BaselinePath." -ForegroundColor Green
Write-Host "Backup: $backup"
