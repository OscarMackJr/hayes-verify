[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$merge=Join-Path $EMSPath "scripts\Inspect-And-Merge-Wave2CPR.ps1"
$post=Join-Path $EMSPath "scripts\Test-Wave2C-PostPushReadiness.ps1"

foreach($p in @($merge,$post)){
    if(-not(Test-Path $p)){throw "Required script missing: $p"}
}

$text=Get-Content $merge -Raw
$postText=Get-Content $post -Raw

$checks=[ordered]@{
    MergeUsesPostPushReadiness = $text -match 'Test-Wave2C-PostPushReadiness\.ps1'
    MergeNoPreCommitReadiness  = -not ($text -match 'Test-Wave2C-PRReadiness\.ps1')
    NoStagedRequirement        = -not ($postText -match 'No staged files')
    RequiresCertificationPass  = $postText -match 'Branch certification is not PASS'
    RequiresClosedState        = $postText -match 'Wave 2C is not CLOSED'
    RequiresZeroRemediation    = $postText -match 'Open remediation count is not zero'
    RequiresInheritancePass    = $postText -match 'Inheritance validation is not PASS'
    RequiresRemoteHeadMatch    = $postText -match 'Local HEAD does not match origin'
}

$rows=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

$tokens=$null;$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $merge,[ref]$tokens,[ref]$errors
)|Out-Null
if($errors.Count -gt 0){throw "Merge gate parser validation failed."}

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2C post-push merge-gate hotfix validation failed."
}

Write-Host "PASS: Wave 2C post-push merge-gate hotfix validated." -ForegroundColor Green
