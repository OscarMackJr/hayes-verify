[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RecordId,
    [Parameter(Mandatory=$true)][string]$SystemOrDataset,
    [Parameter(Mandatory=$true)][string]$DataScope,
    [Parameter(Mandatory=$true)][string]$ProtectionControlOrHandling,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][string]$ValidationResult,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ValidationDate=(Get-Date)
)
$path=Join-Path $EMSPath "registers\wave2c\data-governance\production_data_protection_register.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
if(Import-Csv $path|Where-Object {$_.record_id -ieq $RecordId}){throw "Duplicate record_id: $RecordId"}
[pscustomobject]@{
record_id=$RecordId;system_or_dataset=$SystemOrDataset;data_scope=$DataScope;
protection_control_or_handling=$ProtectionControlOrHandling;owner=$Owner;
validation_date=$ValidationDate.ToUniversalTime().ToString("o");validation_result=$ValidationResult;
evidence_reference=$EvidenceReference
}|Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: production-data-protection operating record added."
