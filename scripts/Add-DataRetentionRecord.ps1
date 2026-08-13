[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RecordId,
    [Parameter(Mandatory=$true)][string]$DataScopeOrCategory,
    [Parameter(Mandatory=$true)][string]$RetentionPeriod,
    [Parameter(Mandatory=$true)][string]$RetentionAuthority,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][string]$ExecutionOrDisposition,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ExecutionDate=(Get-Date)
)
$path=Join-Path $EMSPath "registers\wave2c\data-governance\data_retention_register.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
if(Import-Csv $path|Where-Object {$_.record_id -ieq $RecordId}){throw "Duplicate record_id: $RecordId"}
[pscustomobject]@{
record_id=$RecordId;data_scope_or_category=$DataScopeOrCategory;retention_period=$RetentionPeriod;
retention_authority=$RetentionAuthority;owner=$Owner;execution_or_disposition=$ExecutionOrDisposition;
execution_date=$ExecutionDate.ToUniversalTime().ToString("o");evidence_reference=$EvidenceReference
}|Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: data-retention operating record added."
