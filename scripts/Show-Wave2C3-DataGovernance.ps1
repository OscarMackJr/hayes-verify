[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$root=(Resolve-Path $EMSPath).Path
$out=Join-Path $root "generated\wave2c\data-governance"

Write-Host "Register validation:"
Get-Content (Join-Path $out "register_validation.json")

Write-Host "`nQualification summary:"
Get-Content (Join-Path $out "qualification_summary.json")

Write-Host "`nQualified controls:"
$q=Get-Content (Join-Path $out "qualification.json") -Raw|ConvertFrom-Json
$q.controls|
    Select-Object control_id,control_name,status,sufficiency,promotion_eligible,promotion_status,remediation_state,missing_assertions|
    Format-Table -Wrap -AutoSize

Write-Host "`nAssertion evidence:"
$e=Get-Content (Join-Path $out "assertion_evidence.json") -Raw|ConvertFrom-Json
$e.assertions|
    Select-Object control_id,assertion,record_count,qualifying_record_count,operating_evidence_sufficient,reason|
    Format-Table -Wrap -AutoSize

Write-Host "`nRegister counts:"
Get-ChildItem (Join-Path $root "registers\wave2c\data-governance") -Filter *.csv|
    ForEach-Object{
        [pscustomobject]@{
            Register=$_.Name
            RecordCount=(Import-Csv $_.FullName).Count
        }
    }|Format-Table -AutoSize
