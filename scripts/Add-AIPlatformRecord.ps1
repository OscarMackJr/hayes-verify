[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlatformName,
    [Parameter(Mandatory=$true)][string]$BusinessUse,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][string]$ApprovalAuthority,
    [Parameter(Mandatory=$true)][ValidateSet("APPROVED","CONDITIONALLY_APPROVED","REJECTED","EXCEPTION")][string]$ApprovalStatus,
    [Parameter(Mandatory=$true)][string]$UnapprovedHandling,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ApprovedAt=(Get-Date)
)
$ErrorActionPreference="Stop"
$path=Join-Path $EMSPath "registers\wave2c\ai-governance\approved_ai_platforms.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
$rows=@(Import-Csv $path)
if($rows | Where-Object {$_.platform_name -ieq $PlatformName -and $_.approval_status -ieq $ApprovalStatus}){
    throw "Duplicate AI platform register key: platform_name=$PlatformName approval_status=$ApprovalStatus"
}
[pscustomobject]@{
    platform_name=$PlatformName
    business_use=$BusinessUse
    owner=$Owner
    approval_authority=$ApprovalAuthority
    approval_status=$ApprovalStatus
    approved_at=$ApprovedAt.ToUniversalTime().ToString("o")
    unapproved_handling=$UnapprovedHandling
    evidence_reference=$EvidenceReference
} | Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: AI platform operating record added."
