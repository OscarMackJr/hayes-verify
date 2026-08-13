[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$target=Join-Path $EMSPath "scripts\Resume-Wave2C4-Closeout.ps1"
if(-not(Test-Path $target)){throw "Resume script not found: $target"}

$text=Get-Content $target -Raw

$checks=[ordered]@{
    NoValidatorLASTEXITCODE = -not ($text -match 'LASTEXITCODE\)\{throw "Already-promoted CTRL-080 state validation failed')
    NoResumeLASTEXITCODE    = -not ($text -match 'LASTEXITCODE\)\{throw "Wave 2C\.4 closeout resume failed')
    UsesPowerShellStatus    = $text -match 'if\(-not \$\?\)'
    CallsStateValidator     = $text -match 'Test-Wave2C4-AlreadyPromotedState\.ps1'
    CallsCloseoutRunner     = $text -match 'Run-Wave2C4-AnnualReviewCloseout\.ps1'
}

$rows=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,[ref]$tokens,[ref]$errors
)|Out-Null
if($errors.Count -gt 0){
    $errors|Format-List
    throw "Resume script parser validation failed."
}

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Resume stale-LASTEXITCODE hotfix validation failed."
}

Write-Host "PASS: Wave 2C.4 resume stale-LASTEXITCODE hotfix validated." -ForegroundColor Green
