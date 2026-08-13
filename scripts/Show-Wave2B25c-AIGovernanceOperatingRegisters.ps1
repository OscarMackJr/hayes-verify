[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-operating-registers"
$reg=Join-Path $EMSPath "registers\ai-governance"

Write-Host "Operating evidence summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "evidence_summary.json")

Write-Host ""
Write-Host "Register row counts:" -ForegroundColor Cyan

$registerRows = foreach($f in @(
    "ai_platform_register.json",
    "ai_data_handling_assessment.json",
    "ai_security_review_register.json"
)){
    $path = Join-Path $reg $f

    if(-not(Test-Path $path)){
        [pscustomobject]@{
            Register    = $f
            RecordCount = $null
            Status      = "MISSING"
        }
        continue
    }

    $o = Get-Content $path -Raw | ConvertFrom-Json

    [pscustomobject]@{
        Register    = $f
        RecordCount = @($o.records).Count
        Status      = "PRESENT"
    }
}

$registerRows | Format-Table -AutoSize

Write-Host ""
Write-Host "Evidence envelopes:" -ForegroundColor Cyan

$envPath=Join-Path $out "evidence_envelopes.jsonl"
if(Test-Path $envPath){
    Get-Content $envPath |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { $_ | ConvertFrom-Json } |
        Select-Object control_id,
                      status,
                      sufficiency,
                      record_count,
                      qualifying_record_count,
                      promotion_eligible,
                      reason |
        Format-Table -AutoSize
}
else{
    Write-Host "No evidence_envelopes.jsonl found."
}

Write-Host ""
Write-Host "Promotion report:" -ForegroundColor Cyan
$p=Join-Path $out "promotion_report.json"
if(Test-Path $p){
    Get-Content $p
}
else{
    Write-Host "No promotion run yet."
}
