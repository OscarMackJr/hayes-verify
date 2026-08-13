[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$HayesPath = "C:\temp\standars\hayes-verify",
    [switch]$InitializeGit
)

$ErrorActionPreference = "Stop"
function Fail([string]$m){ throw "HAYES VERIFY BOOTSTRAP BLOCKED: $m" }

$ems = (Resolve-Path $EMSPath).Path
$pkg = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$freezePath = Join-Path $ems "generated\wave2d\evaluation-contract\contract_freeze.json"
if(-not(Test-Path $freezePath)){ Fail "EMS contract freeze not found: $freezePath" }

$freeze = Get-Content $freezePath -Raw | ConvertFrom-Json

if($freeze.status -ne "PASS"){ Fail "EMS contract freeze status is not PASS." }
if($freeze.freeze_state -ne "CONTRACT_FROZEN"){ Fail "EMS contract freeze_state is not CONTRACT_FROZEN." }
if($freeze.evaluation_performed -ne $false){ Fail "EMS contract freeze reports evaluation already performed." }
if($freeze.promotion_performed -ne $false){ Fail "EMS contract freeze reports promotion already performed." }

if($freeze.authority.control_catalog -ne "EMS"){ Fail "EMS must remain control catalog authority." }
if($freeze.authority.applicability -ne "EMS"){ Fail "EMS must remain applicability authority." }
if($freeze.authority.evidence_collection -ne "Hayes Verify"){ Fail "Hayes Verify must remain evidence collector." }
if($freeze.authority.evaluation_execution -ne "Hayes Verify"){ Fail "Hayes Verify must remain evaluation executor." }
if($freeze.authority.result_acceptance -ne "EMS"){ Fail "EMS must remain result acceptance authority." }
if($freeze.authority.evidence_promotion -ne "EMS"){ Fail "EMS must remain evidence promotion authority." }

Write-Host "=== Verify frozen EMS contract hashes ===" -ForegroundColor Cyan
foreach($prop in $freeze.contracts.PSObject.Properties){
    $name = $prop.Name
    $meta = $prop.Value
    $source = Join-Path $ems ($meta.path -replace '/','\')
    if(-not(Test-Path $source)){ Fail "Missing frozen contract $name at $source" }

    $sha = (Get-FileHash $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if($sha -ne $meta.sha256.ToLowerInvariant()){
        Fail "Contract hash mismatch for $name"
    }
    Write-Host "PASS: $name"
}

if(Test-Path $HayesPath){
    $items = @(Get-ChildItem $HayesPath -Force -ErrorAction SilentlyContinue)
    if($items.Count -gt 0){ Fail "Hayes target exists and is not empty: $HayesPath" }
}else{
    New-Item -ItemType Directory -Force -Path $HayesPath | Out-Null
}

Write-Host "`n=== Scaffold Hayes Verify repository ===" -ForegroundColor Cyan

Copy-Item (Join-Path $pkg "templates\*") $HayesPath -Recurse -Force

New-Item -ItemType Directory -Force -Path `
    (Join-Path $HayesPath "contracts"), `
    (Join-Path $HayesPath "contracts\schemas"), `
    (Join-Path $HayesPath "contracts\registry") | Out-Null

foreach($prop in $freeze.contracts.PSObject.Properties){
    $name = $prop.Name
    $meta = $prop.Value
    $source = Join-Path $ems ($meta.path -replace '/','\')

    if($name -eq "status_vocabulary"){
        $dest = Join-Path $HayesPath "contracts\registry\evaluation_status_vocabulary.json"
    }else{
        $dest = Join-Path $HayesPath ("contracts\schemas\" + [IO.Path]::GetFileName($meta.path))
    }
    Copy-Item $source $dest -Force
}

Copy-Item $freezePath (Join-Path $HayesPath "contracts\contract_freeze.json") -Force

$consumerManifest = [ordered]@{
    consumer = "Hayes Verify"
    contract_version = $freeze.contract_version
    source_wave = $freeze.wave
    source_contract_freeze = $freezePath
    source_contract_freeze_sha256 = (Get-FileHash $freezePath -Algorithm SHA256).Hash.ToLowerInvariant()
    authority = $freeze.authority
    contracts = $freeze.contracts
    applicability_mutation_allowed = $false
    evidence_promotion_allowed = $false
    scaffold_state = "CONTRACT_CONSUMER_BOOTSTRAPPED"
}
$consumerManifest | ConvertTo-Json -Depth 20 |
    Set-Content (Join-Path $HayesPath "contracts\consumer_manifest.json") -Encoding UTF8

Write-Host "`n=== Validate copied contract hashes ===" -ForegroundColor Cyan
python (Join-Path $HayesPath "scripts\validate_contract_bundle.py") --root $HayesPath
if($LASTEXITCODE){ Fail "Hayes Verify contract bundle validation failed." }

if($InitializeGit){
    Write-Host "`n=== Initialize Git repository ===" -ForegroundColor Cyan
    git -C $HayesPath init
    if($LASTEXITCODE){ Fail "git init failed." }
    git -C $HayesPath add .
    if($LASTEXITCODE){ Fail "git add failed." }
}

Write-Host "`nPASS: Hayes Verify repository scaffolded." -ForegroundColor Green
Write-Host "Path: $HayesPath"
Write-Host "Contract version: $($freeze.contract_version)"
Write-Host "No EMS applicability or promotion authority transferred."
