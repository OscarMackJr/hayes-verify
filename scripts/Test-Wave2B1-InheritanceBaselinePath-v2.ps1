[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$target=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $target)){throw "Inheritance runner not found: $target"}

$text=Get-Content $target -Raw

$checks=[ordered]@{
    HasBaselinePathParameter = $text -match '\$BaselinePath'
    UsesExplicitTestPath     = $text -match 'Test-Path \$BaselinePath'
    ResolvesExplicitPath     = $text -match 'Resolve-Path \$BaselinePath'
    RetainsFailClosedGuard   = $text -match 'Wave 1 compliance baseline not found'
}

$rows=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows | Format-Table -AutoSize

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "Inheritance runner parser validation failed."
}

if(@($rows | Where-Object {-not $_.Pass}).Count -gt 0){
    throw "Inheritance baseline-path hotfix validation failed."
}

Write-Host "PASS: inheritance baseline-path hotfix validated." -ForegroundColor Green
