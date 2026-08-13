[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ReviewId,
    [Parameter(Mandatory=$true)][string]$PlatformOrUseCase,
    [Parameter(Mandatory=$true)][string]$Reviewer,
    [Parameter(Mandatory=$true)][string]$FindingOrRisk,
    [Parameter(Mandatory=$true)][ValidateSet("LOW","MEDIUM","HIGH","CRITICAL","NONE")][string]$Severity,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][ValidateSet("OPEN","ACCEPTED","REMEDIATED","MITIGATED","EXCEPTION_APPROVED","CLOSED")][string]$Disposition,
    [Parameter(Mandatory=$true)][string]$EvidenceReference,
    [string]$EMSPath="C:\temp\standars\ems",
    [datetime]$ReviewDate=(Get-Date)
)
$ErrorActionPreference="Stop"
$path=Join-Path $EMSPath "registers\wave2c\ai-governance\ai_security_reviews.csv"
if(!(Test-Path $path)){throw "Register not found: $path"}
$rows=@(Import-Csv $path)
if($rows | Where-Object {$_.review_id -ieq $ReviewId}){throw "Duplicate AI security review_id: $ReviewId"}
[pscustomobject]@{
    review_id=$ReviewId
    platform_or_use_case=$PlatformOrUseCase
    review_date=$ReviewDate.ToUniversalTime().ToString("o")
    reviewer=$Reviewer
    finding_or_risk=$FindingOrRisk
    severity=$Severity
    owner=$Owner
    disposition=$Disposition
    evidence_reference=$EvidenceReference
} | Export-Csv $path -Append -NoTypeInformation
Write-Host "PASS: AI security review operating record added."
