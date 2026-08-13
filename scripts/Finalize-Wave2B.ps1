[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [switch]$PrepareBranch,
    [string]$BranchName = "feature/wave2-closeout"
)

$ErrorActionPreference = "Stop"

function Assert-File {
    param([string]$Path,[string]$Label)
    if(-not(Test-Path $Path)){
        throw "$Label not found: $Path"
    }
}

Write-Host "=== Wave 2B Finalization ===" -ForegroundColor Cyan

# Required tooling
$testScript = Join-Path $EMSPath "scripts\Test-Wave2BAuthoritativePopulationHotfix.ps1"
$rerunScript = Join-Path $EMSPath "scripts\Rerun-Wave2BAuthoritativePopulationHotfix.ps1"
$closeoutScript = Join-Path $EMSPath "scripts\Run-Wave2BCloseoutCertification.ps1"
$showScript = Join-Path $EMSPath "scripts\Show-Wave2BCloseoutCertification.ps1"

Assert-File $testScript "Authoritative population validation script"
Assert-File $rerunScript "Authoritative population rerun script"
Assert-File $closeoutScript "Wave 2B closeout script"
Assert-File $showScript "Wave 2B closeout display script"

Write-Host ""
Write-Host "=== Validate authoritative population semantics ===" -ForegroundColor Cyan
& $testScript -EMSPath $EMSPath
if($LASTEXITCODE -ne 0){
    throw "Authoritative population validation failed."
}

Write-Host ""
Write-Host "=== Run corrected certification and freeze ===" -ForegroundColor Cyan
& $rerunScript -EMSPath $EMSPath -Freeze
if($LASTEXITCODE -ne 0){
    throw "Wave 2B certification/freeze failed."
}

$certPath = Join-Path $EMSPath "generated\wave2\closeout-certification\wave2b_certification.json"
$freezePath = Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"
$zipPath = Join-Path $EMSPath "release\wave2b-closeout\EMS_Wave2B_BranchReady_Closeout.zip"

Assert-File $certPath "Wave 2B certification"
Assert-File $freezePath "Wave 2B freeze summary"
Assert-File $zipPath "Wave 2B closeout ZIP"

$cert = Get-Content $certPath -Raw | ConvertFrom-Json
$freeze = Get-Content $freezePath -Raw | ConvertFrom-Json

if($cert.status -ne "PASS"){
    throw "Wave 2B certification status is not PASS."
}

if($cert.certification_state -notin @("CERTIFIED","CERTIFIED_WITH_CONTROLLED_REMEDIATION")){
    throw "Unexpected certification_state: $($cert.certification_state)"
}

if(-not $cert.repository_reconciliation.authoritative_unresolved_count_matches){
    throw "Authoritative unresolved count did not reconcile."
}

if([int]$cert.repository_reconciliation.undispositioned_row_count -ne 0){
    throw "Undispositioned higher-scope rows remain."
}

if([int]$cert.higher_scope_authority.undispositioned_control_count -ne 0){
    throw "Undispositioned higher-scope controls remain."
}

if($freeze.status -ne "PASS"){
    throw "Wave 2B freeze summary is not PASS."
}

if(-not(Test-Path $freeze.zip)){
    throw "Freeze summary references a missing ZIP: $($freeze.zip)"
}

$actualHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
$expectedHash = ([string]$freeze.zip_sha256).ToLower()

if($actualHash -ne $expectedHash){
    throw "Wave 2B ZIP SHA-256 mismatch."
}

Write-Host ""
Write-Host "=== Wave 2B certification checkpoint ===" -ForegroundColor Cyan
[pscustomobject]@{
    Status                         = $cert.status
    CertificationState             = $cert.certification_state
    ScopeControls                  = $cert.scope_control_count
    HigherScopeControls            = $cert.higher_scope_authority.control_count
    HigherScopePass                = $cert.higher_scope_authority.pass_control_count
    RemediationControls            = $cert.higher_scope_authority.controlled_remediation_control_count
    UndispositionedControls        = $cert.higher_scope_authority.undispositioned_control_count
    InheritedRows                  = $cert.inheritance_authority.inherited_count
    UnresolvedHigherScopeRows      = $cert.inheritance_authority.unresolved_higher_scope_count
    ControlledRemediationRows      = $cert.repository_reconciliation.controlled_remediation_row_count
    UndispositionedRows            = $cert.repository_reconciliation.undispositioned_row_count
    Reconciled                     = $cert.repository_reconciliation.authoritative_unresolved_count_matches
} | Format-List

Write-Host ""
Write-Host "=== Frozen package ===" -ForegroundColor Cyan
[pscustomobject]@{
    Zip       = $zipPath
    Sha256    = $actualHash
    FileCount = $freeze.file_count
} | Format-List

if($PrepareBranch){
    Write-Host ""
    Write-Host "=== Prepare Wave 2B closeout branch ===" -ForegroundColor Cyan

    Push-Location $EMSPath
    try{
        $current = (git branch --show-current).Trim()
        if($LASTEXITCODE -ne 0){ throw "Unable to determine current Git branch." }

        if($current -ne $BranchName){
            $exists = git branch --list $BranchName
            if($LASTEXITCODE -ne 0){ throw "Unable to inspect branch state." }

            if([string]::IsNullOrWhiteSpace(($exists -join ""))){
                git checkout -b $BranchName
                if($LASTEXITCODE -ne 0){ throw "Failed to create branch $BranchName." }
            }
            else{
                git checkout $BranchName
                if($LASTEXITCODE -ne 0){ throw "Failed to checkout branch $BranchName." }
            }
        }

        git add registry schemas evidence registers scripts generated/wave2 release/wave2b-closeout
        if($LASTEXITCODE -ne 0){ throw "git add failed." }

        Write-Host ""
        Write-Host "Branch prepared and changes staged. No commit or push was performed." -ForegroundColor Yellow
        git status --short
    }
    finally{
        Pop-Location
    }
}

Write-Host ""
Write-Host "PASS: Wave 2B is certified, frozen, integrity-verified, and ready for branch closeout." -ForegroundColor Green
