[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RecordId,
    [Parameter(Mandatory=$true)][string]$PlatformName,
    [Parameter(Mandatory=$true)][string]$UseCase,
    [Parameter(Mandatory=$true)][ValidateSet("PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED")][string]$DataClassification,
    [Parameter(Mandatory=$true)][string]$SensitiveDataHandling,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ReviewedAt=(Get-Date)
)
$ErrorActionPreference="Stop"
$path=Join-Path $EMSPath "registers\wave2c\ai-governance\prompt_data_classification.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
$rows=@(Import-Csv $path)
if($rows | Where-Object {$_.record_id -ieq $RecordId}){throw "Duplicate prompt data classification record_id: $RecordId"}
[pscustomobject]@{
    record_id=$RecordId
    platform_name=$PlatformName
    use_case=$UseCase
    data_classification=$DataClassification
    sensitive_data_handling=$SensitiveDataHandling
    owner=$Owner
    reviewed_at=$ReviewedAt.ToUniversalTime().ToString("o")
    evidence_reference=$EvidenceReference
} | Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: Prompt data classification operating record added."
