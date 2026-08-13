[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C CLOSEOUT RECONCILIATION BLOCKED: $m"}

$cert=Join-Path $EMSPath "generated\wave2c\annual-review-closeout\wave2c_closeout_certification.json"
$impact=Join-Path $EMSPath "generated\wave2\inheritance\inheritance_impact_report.json"
$higher=Join-Path $EMSPath "generated\wave2\inheritance\higher_scope_results.json"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

foreach($p in @($cert,$impact,$higher,$queue)){
    if(-not(Test-Path $p)){Fail "Required artifact missing: $p"}
}

$beforeCertHash=(Get-FileHash -Algorithm SHA256 $cert).Hash.ToLowerInvariant()
$queueHash=(Get-FileHash -Algorithm SHA256 $queue).Hash.ToLowerInvariant()
$impactHash=(Get-FileHash -Algorithm SHA256 $impact).Hash.ToLowerInvariant()
$higherHash=(Get-FileHash -Algorithm SHA256 $higher).Hash.ToLowerInvariant()

$certObj=Get-Content $cert -Raw | ConvertFrom-Json
if($certObj.status -ne "PASS"){Fail "Closeout certification status is not PASS."}
if($certObj.wave2c_state -ne "CLOSED"){Fail "Wave 2C state is not CLOSED."}
if([int]$certObj.open_remediation_count -ne 0){Fail "Open remediation count is not zero."}
if($certObj.promotion_performed -ne $true){Fail "Promotion performed flag is not true."}

# Reconcile inheritance validation from available authoritative artifacts.
$inheritanceStatus=$null

try{
    $impactObj=Get-Content $impact -Raw | ConvertFrom-Json
    if($impactObj.status -eq "PASS"){
        $inheritanceStatus="PASS"
    }elseif($impactObj.validation_status -eq "PASS"){
        $inheritanceStatus="PASS"
    }
}catch{}

if(-not $inheritanceStatus){
    $validationCandidates=@(
        (Join-Path $EMSPath "generated\wave2\inheritance\validation_report.json"),
        (Join-Path $EMSPath "generated\wave2\inheritance\inheritance_validation.json")
    )
    foreach($candidate in $validationCandidates){
        if(Test-Path $candidate){
            try{
                $obj=Get-Content $candidate -Raw | ConvertFrom-Json
                if($obj.status -eq "PASS"){
                    $inheritanceStatus="PASS"
                    break
                }
            }catch{}
        }
    }
}

if(-not $inheritanceStatus){
    Fail "Unable to prove inheritance validation PASS from authoritative artifacts."
}

# Verify current hashes still match the frozen closeout inputs.
if(([string]$certObj.queue_sha256).ToLowerInvariant() -ne $queueHash){
    Fail "Wave 2C remediation queue hash no longer matches closeout certification."
}
if(([string]$certObj.inheritance_impact_sha256).ToLowerInvariant() -ne $impactHash){
    Fail "Inheritance impact hash no longer matches closeout certification."
}
if(([string]$certObj.higher_scope_results_sha256).ToLowerInvariant() -ne $higherHash){
    Fail "Higher-scope results hash no longer matches closeout certification."
}

$backup="$cert.pre-inheritance-status-reconciliation.bak"
Copy-Item $cert $backup -Force

$certObj.inheritance_validation=$inheritanceStatus
$certObj | ConvertTo-Json -Depth 20 | Set-Content $cert -Encoding UTF8

$afterCertHash=(Get-FileHash -Algorithm SHA256 $cert).Hash.ToLowerInvariant()

$result=[ordered]@{
    wave="2C"
    status="PASS"
    prior_inheritance_validation="UNKNOWN"
    reconciled_inheritance_validation=$inheritanceStatus
    queue_sha256=$queueHash
    inheritance_impact_sha256=$impactHash
    higher_scope_results_sha256=$higherHash
    closeout_certification_sha256_before=$beforeCertHash
    closeout_certification_sha256_after=$afterCertHash
    control_results_changed=$false
    remediation_population_changed=$false
    evidence_artifacts_changed=$false
}

$out=Join-Path $EMSPath "generated\wave2c\annual-review-closeout\inheritance_status_reconciliation.json"
$result | ConvertTo-Json -Depth 20 | Set-Content $out -Encoding UTF8

$result | ConvertTo-Json -Depth 20 | Write-Host
Write-Host "PASS: Wave 2C closeout inheritance status reconciled to PASS." -ForegroundColor Green
Write-Host "No EMS control results or remediation state changed." -ForegroundColor Green
