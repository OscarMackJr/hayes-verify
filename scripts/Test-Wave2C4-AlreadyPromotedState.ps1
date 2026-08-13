[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"

$promotion=Join-Path $EMSPath "generated\wave2c\annual-review-closeout\promotion_record.json"
$evidence=Join-Path $EMSPath "evidence\ems\EMS-CTRL-080.yaml"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

foreach($p in @($promotion,$evidence,$queue)){
    if(-not(Test-Path $p)){throw "Resume validation blocked: missing $p"}
}

$pr=Get-Content $promotion -Raw | ConvertFrom-Json
if($pr.wave -ne "2C.4"){throw "Resume validation blocked: unexpected promotion wave $($pr.wave)"}
if($pr.control_id -ne "EMS-CTRL-080"){throw "Resume validation blocked: unexpected control $($pr.control_id)"}
if($pr.promotion_performed -ne $true){throw "Resume validation blocked: promotion_performed is not true."}
if($pr.pre_open_count -ne 1 -or $pr.post_open_count -ne 0){
    throw "Resume validation blocked: promotion counts do not reconcile 1 -> 0."
}

$hash=(Get-FileHash -Algorithm SHA256 $evidence).Hash.ToLowerInvariant()
$expected=[string]$pr.authoritative_evidence_sha256
if($hash -ne $expected.ToLowerInvariant()){
    throw "Resume validation blocked: authoritative evidence SHA-256 mismatch."
}

$rows=@(Import-Csv $queue)
$ctrl=@($rows | Where-Object {$_.control_id -eq "EMS-CTRL-080"})
if($ctrl.Count -ne 1){throw "Resume validation blocked: CTRL-080 queue row missing or duplicated."}
$ctrl=$ctrl[0]

$checks=[ordered]@{
    CurrentStatusPass      = ($ctrl.current_status -eq "PASS")
    SufficiencySufficient  = ($ctrl.evidence_sufficiency -eq "SUFFICIENT")
    PromotionEligibleTrue  = ($ctrl.promotion_eligible -eq "True")
    PromotionStatusPromoted= ($ctrl.promotion_status -eq "PROMOTED")
    RemediationClosed      = ($ctrl.remediation_state -eq "CLOSED")
    NextActionNone         = ($ctrl.next_action -eq "NONE")
    ZeroOpenRemediation    = (@($rows | Where-Object {$_.remediation_state -eq "OPEN"}).Count -eq 0)
}

$table=$checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$table | Format-Table -AutoSize

$failed=@($table | Where-Object {-not $_.Pass})
if($failed.Count -gt 0){
    throw "Resume validation blocked: one or more queue-state checks failed."
}

$result=[ordered]@{
    status="PASS"
    control_id="EMS-CTRL-080"
    promotion_performed=$true
    authoritative_evidence=$evidence
    authoritative_evidence_sha256=$hash
    open_remediation_count=0
    resume_eligible=$true
}
$result | ConvertTo-Json | Write-Host

Write-Host "PASS: CTRL-080 is already promoted and Wave 2C closeout may resume." -ForegroundColor Green
