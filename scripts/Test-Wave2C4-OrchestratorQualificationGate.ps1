[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Run-Wave2C4-AnnualReviewCloseout.ps1"
if(-not(Test-Path $target)){throw "Wave 2C.4 orchestrator not found: $target"}

$text=Get-Content $target -Raw

$checks=[ordered]@{
    ReadsQualificationArtifact = $text -match 'qualificationPath=Join-Path \$out "qualification\.json"'
    RequiresPass               = $text -match '\$ctrl\.status -eq "PASS"'
    RequiresSufficient         = $text -match '\$ctrl\.sufficiency -eq "SUFFICIENT"'
    RequiresPromotionEligible  = $text -match '\$ctrl\.promotion_eligible -eq \$true'
    RequiresQualifiedState     = $text -match 'QUALIFIED_NOT_PROMOTED'
    SkipsReviewWhenUnqualified = $text -match 'CTRL-080 not yet qualified; review/promotion skipped'
    PreservesFailClosedMessage = $text -match 'Wave 2C\.4 remains fail-closed with no promotion performed'
    KeepsExplicitCloseout      = $text -match '\$PromoteAndCloseout'
}

$rows=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,
    [ref]$tokens,
    [ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    $errors|Format-List
    throw "Wave 2C.4 orchestrator parser validation failed."
}

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2C.4 qualification-gate validation failed."
}

Write-Host "PASS: Wave 2C.4 qualification-gate hotfix validated." -ForegroundColor Green
