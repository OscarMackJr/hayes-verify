[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[string]$DefaultOwner="Engineering Management")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D ASSISTED HUMAN REVIEW BLOCKED: $m"}
$file=Join-Path $EMSPath "registry\wave2d\applicability_review_decisions.csv"
if(-not(Test-Path $file)){Fail "Assisted review file missing: $file"}
$rows=@(Import-Csv $file)
for($i=0;$i -lt $rows.Count;$i++){
    $r=$rows[$i]
    $complete=($r.human_decision -in @("APPLICABLE","NOT_APPLICABLE") -and -not [string]::IsNullOrWhiteSpace($r.human_rationale) -and -not [string]::IsNullOrWhiteSpace($r.human_decision_owner) -and $r.human_decision_source -match '^HUMAN_')
    if($complete){Write-Host "[$($i+1)/$($rows.Count)] Prepopulated: $($r.control_id) / $($r.repository_name) -> $($r.human_decision)" -ForegroundColor DarkGray;continue}
    Write-Host "";Write-Host "[$($i+1)/$($rows.Count)] $($r.control_id) - $($r.control_name)" -ForegroundColor Yellow
    Write-Host "Repository: $($r.repository_name)"
    Write-Host "Assessment: $($r.assessment_proposal) / $($r.assessment_confidence)"
    Write-Host "Evidence: $($r.assessment_evidence_paths)"
    Write-Host "Assessment rationale: $($r.assessment_rationale)"
    $decision=$null
    while($decision -notin @("APPLICABLE","NOT_APPLICABLE")){
        $raw=Read-Host "Decision [A=APPLICABLE, N=NOT_APPLICABLE]"
        switch($raw.Trim().ToUpperInvariant()){
            "A"{$decision="APPLICABLE"};"APPLICABLE"{$decision="APPLICABLE"};"N"{$decision="NOT_APPLICABLE"};"NA"{$decision="NOT_APPLICABLE"};"NOT_APPLICABLE"{$decision="NOT_APPLICABLE"};default{Write-Host "Enter A/APPLICABLE or N/NA/NOT_APPLICABLE." -ForegroundColor Red}
        }
    }
    $rat=Read-Host "Rationale [Enter=use assessment rationale]"
    if([string]::IsNullOrWhiteSpace($rat)){$rat=$r.assessment_rationale}
    if([string]::IsNullOrWhiteSpace($rat)){Fail "Rationale is required."}
    $owner=Read-Host "Decision owner [$DefaultOwner]"
    if([string]::IsNullOrWhiteSpace($owner)){$owner=$DefaultOwner}
    $r.human_decision=$decision;$r.human_rationale=$rat.Trim();$r.human_decision_owner=$owner.Trim();$r.human_decision_source="HUMAN_REPOSITORY_EVIDENCE_REVIEW"
    $rows|Export-Csv $file -NoTypeInformation -Encoding UTF8
}
Write-Host "PASS: assisted human applicability review complete." -ForegroundColor Green
