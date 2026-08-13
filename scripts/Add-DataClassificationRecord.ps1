[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RecordId,
    [Parameter(Mandatory=$true)][string]$SystemOrDataset,
    [Parameter(Mandatory=$true)][ValidateSet("PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED")][string]$DataClassification,
    [Parameter(Mandatory=$true)][string]$DataOwnerOrSteward,
    [Parameter(Mandatory=$true)][string]$Reviewer,
    [Parameter(Mandatory=$true)][string]$ReviewOutcome,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ReviewDate=(Get-Date)
)
$path=Join-Path $EMSPath "registers\wave2c\data-governance\data_classification_register.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
if(Import-Csv $path|Where-Object {$_.record_id -ieq $RecordId}){throw "Duplicate record_id: $RecordId"}
[pscustomobject]@{
record_id=$RecordId;system_or_dataset=$SystemOrDataset;data_classification=$DataClassification;
data_owner_or_steward=$DataOwnerOrSteward;review_date=$ReviewDate.ToUniversalTime().ToString("o");
reviewer=$Reviewer;review_outcome=$ReviewOutcome;evidence_reference=$EvidenceReference
}|Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: data-classification operating record added."
