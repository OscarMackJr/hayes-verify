[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ReviewId,
    [Parameter(Mandatory=$true)][string]$Participants,
    [Parameter(Mandatory=$true)][string]$FindingsOrObservations,
    [Parameter(Mandatory=$true)][string]$Decisions,
    [Parameter(Mandatory=$true)][string]$ActionsAndOwners,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [ValidateSet("COMPLETED","APPROVED","CLOSED")][string]$ReviewStatus="COMPLETED",
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ReviewDate=(Get-Date)
)
$ErrorActionPreference="Stop"
$path=Join-Path $EMSPath "registers\wave2c\ems-review\annual_ems_review_register.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
if(Import-Csv $path|Where-Object {$_.review_id -ieq $ReviewId}){throw "Duplicate review_id: $ReviewId"}

[pscustomobject]@{
 review_id=$ReviewId
 review_date=$ReviewDate.ToUniversalTime().ToString("o")
 participants=$Participants
 findings_or_observations=$FindingsOrObservations
 decisions=$Decisions
 actions_and_owners=$ActionsAndOwners
 review_status=$ReviewStatus
 evidence_reference=$EvidenceReference
}|Export-Csv $path -Append -NoTypeInformation

Write-Host "PASS: annual EMS review operating record added."
