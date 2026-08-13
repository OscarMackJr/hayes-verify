[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$root=(Resolve-Path $EMSPath).Path
$out=Join-Path $root "generated\wave2c\annual-review"
$close=Join-Path $root "generated\wave2c\annual-review-closeout"
$queue=Join-Path $root "generated\wave2c\remediation_queue.csv"

Write-Host "CTRL-080 qualification:" -ForegroundColor Cyan
Get-Content (Join-Path $out "qualification.json")

Write-Host "`nAssertion evidence:" -ForegroundColor Cyan
$e=Get-Content (Join-Path $out "assertion_evidence.json") -Raw|ConvertFrom-Json
$e.assertions|Select control_id,assertion,record_count,qualifying_record_count,operating_evidence_sufficient,reason|Format-Table -Wrap -AutoSize

Write-Host "`nWave 2C queue:" -ForegroundColor Cyan
Import-Csv $queue|Select control_id,control_name,current_status,evidence_sufficiency,promotion_status,remediation_state,next_action|Format-Table -Wrap -AutoSize

if(Test-Path (Join-Path $close "review_record.json")){
    Write-Host "`nReview record:" -ForegroundColor Cyan
    Get-Content (Join-Path $close "review_record.json")
}
if(Test-Path (Join-Path $close "promotion_record.json")){
    Write-Host "`nPromotion record:" -ForegroundColor Cyan
    Get-Content (Join-Path $close "promotion_record.json")
}
if(Test-Path (Join-Path $close "wave2c_closeout_certification.json")){
    Write-Host "`nWave 2C closeout certification:" -ForegroundColor Cyan
    Get-Content (Join-Path $close "wave2c_closeout_certification.json")
}
