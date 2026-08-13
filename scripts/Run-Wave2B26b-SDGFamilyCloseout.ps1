[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"

$requal=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance-requalified"
$qualified=Join-Path $requal "qualified_security_data_governance_requalified.csv"
$matrix=Join-Path $requal "assertion_evidence_matrix_requalified.csv"
$gaps=Join-Path $requal "security_data_governance_gaps_requalified.csv"
$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance-closeout"

New-Item -ItemType Directory -Path $out -Force|Out-Null

foreach($p in @($qualified,$matrix,$gaps)){
    if(-not(Test-Path $p)){throw "Required 2B.2.6a artifact missing: $p"}
}

$q=Import-Csv $qualified
$eligible=@($q|Where-Object promotion_eligible -eq "True")
$ineligible=@($q|Where-Object promotion_eligible -ne "True")
$gapRows=Import-Csv $gaps

Write-Host "Security & Data Governance family qualification:" -ForegroundColor Cyan
$q|Select-Object control_id,control_name,status,sufficiency,promotion_eligible|Format-Table -AutoSize

$expectedEligible=@("EMS-CTRL-023","EMS-CTRL-024")
$actualEligible=@($eligible.control_id|Sort-Object)
$unexpected=@($actualEligible|Where-Object{$_ -notin $expectedEligible})

if($unexpected.Count -gt 0){
    throw "Unexpected controls became promotion eligible: $($unexpected -join ', ')"
}

$closeout=[ordered]@{
    wave="2B.2.6b"
    collector_family="HS-SECURITY-DATA-GOVERNANCE"
    control_count=$q.Count
    promotion_eligible_count=$eligible.Count
    promotion_eligible_controls=$actualEligible
    remediation_count=$gapRows.Count
    remediation_controls=@($gapRows.control_id)
    family_state=if($gapRows.Count -eq 0){"FULLY_QUALIFIED"}else{"QUALIFIED_WITH_CONTROLLED_REMEDIATION"}
    promotion_performed=$false
    inheritance_rerun=$false
}

if($Promote){
    Write-Host ""
    Write-Host "Promoting currently qualified family controls..." -ForegroundColor Cyan

    $py=Join-Path $EMSPath ".venv\Scripts\python.exe"
    if(-not(Test-Path $py)){$py="python"}

    & $py (Join-Path $EMSPath "scripts\Promote-HSSecurityDataGovernance-Requalified.py") `
      --qualified $qualified `
      --matrix $matrix `
      --evidence-root (Join-Path $EMSPath "evidence") `
      --report (Join-Path $out "promotion_report.json")

    if($LASTEXITCODE-ne 0){throw "Security/Data Governance promotion failed."}

    $promotion=Get-Content (Join-Path $out "promotion_report.json") -Raw|ConvertFrom-Json
    $promotedIds=@($promotion.promoted.control_id|Sort-Object)

    if(@($promotedIds|Where-Object{$_ -notin $actualEligible}).Count -gt 0){
        throw "Promotion report contains controls not eligible in requalification."
    }

    $closeout.promotion_performed=$true

    Write-Host ""
    Write-Host "Re-running Wave 2B.1 inheritance..." -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
    $closeout.inheritance_rerun=$true

    $impact=Join-Path $EMSPath "generated\wave2\inheritance\inheritance_impact_report.json"
    if(Test-Path $impact){
        $impactObj=Get-Content $impact -Raw|ConvertFrom-Json
        $closeout.inheritance=[ordered]@{
            row_count=$impactObj.row_count
            changed_count=$impactObj.changed_count
            inherited_count=$impactObj.inherited_count
            unresolved_higher_scope_count=$impactObj.unresolved_higher_scope_count
        }
    }
}

$remediationOut=Join-Path $out "open_remediation.csv"
$gapRows | ForEach-Object {
    [pscustomobject]@{
        control_id=$_.control_id
        control_name=$_.control_name
        scope=$_.scope
        disposition="REMEDIATE"
        current_status="WARNING"
        missing_assertions=$_.missing_assertions
        remediation_state="OPEN"
    }
} | Export-Csv $remediationOut -NoTypeInformation

$closeout|ConvertTo-Json -Depth 8|Set-Content (Join-Path $out "family_closeout.json") -Encoding UTF8

Write-Host ""
Write-Host "Family closeout:" -ForegroundColor Cyan
Get-Content (Join-Path $out "family_closeout.json")

Write-Host ""
Write-Host "Open remediation:" -ForegroundColor Cyan
Import-Csv $remediationOut|Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Wave 2B.2.6b complete." -ForegroundColor Green
