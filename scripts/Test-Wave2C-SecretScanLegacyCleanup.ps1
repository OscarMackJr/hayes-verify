[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$root=(Resolve-Path $EMSPath).Path

$obsolete=@(
    "scripts/Test-EMSValidateSecretScanSelfMatchFix.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch-v3.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch-v2.ps1",
    "scripts/Patch-EMSValidateSecretScanMaintenanceSource-v5.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch.ps1",
    "scripts/Test-EMSValidateSecretScanSelfMatchFix-v3.ps1",
    "scripts/Patch-EMSValidateSecretScanFalsePositives-v4.ps1",
    "scripts/Test-EMSValidateSecretScanSelfMatchFix-v2.ps1",
    "scripts/Patch-EMSValidateSecretScanMaintenanceSource-v6.ps1"
)

$remaining=@($obsolete | Where-Object { Test-Path (Join-Path $root $_) })

$workflow=Join-Path $root ".github\workflows\ems-validate.yml"
$wf=if(Test-Path $workflow){Get-Content $workflow -Raw}else{""}

$checks=[ordered]@{
    ObsoleteMaintenanceRemoved = ($remaining.Count -eq 0)
    WorkflowStillPresent       = (Test-Path $workflow)
    ExplicitGithubPrefixes     = ($wf -match 'gh\[pousr\]_')
    FineGrainedPrefix          = ($wf -match 'github_pat_')
    AzureDetectionRetained     = ($wf -match 'AZURE_CLIENT_SECRET')
    AwsDetectionRetained       = ($wf -match 'AWS_SECRET_ACCESS_KEY')
    PrivateKeyDetectionRetained= ($wf -match 'PRIVATE KEY')
}

$rows=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows | Format-Table -AutoSize

if($remaining.Count -gt 0){
    Write-Host "Remaining obsolete files:" -ForegroundColor Red
    $remaining | ForEach-Object {Write-Host $_}
}

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Legacy secret-scan cleanup validation failed."
}

Write-Host "PASS: secret-scan cleanup state validated." -ForegroundColor Green
