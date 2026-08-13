[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Tag="ems-v0.6.0-wave2c"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C POST-MERGE EXTERNAL RUNNER BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$external=Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Preflight main branch ===" -ForegroundColor Cyan
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "main"){Fail "Expected main; current=$branch"}

git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed."}

$head=(git -C $root rev-parse HEAD).Trim()
$origin=(git -C $root rev-parse origin/main).Trim()
if($head -ne $origin){Fail "HEAD $head does not match origin/main $origin"}

# Installer-created post-merge files are expected to be untracked and must be removed
# before certification. Preserve unrelated untracked files.
$known=@(
    "registry/wave2c_post_merge_release_spec.json",
    "schemas/wave2c_post_merge_certification.schema.json",
    "scripts/Certify-Wave2CPostMerge.py",
    "scripts/Freeze-Wave2CPostMergeRelease.py",
    "scripts/Publish-Wave2CPostMergeTag.ps1",
    "scripts/Run-Wave2CPostMergeRelease.ps1",
    "scripts/Show-Wave2CPostMergeRelease.ps1"
)
foreach($rel in $known){
    $full=Join-Path $root ($rel -replace '/','\')
    if(Test-Path $full){
        $tracked=git -C $root ls-files --error-unmatch -- $rel 2>$null
        if($LASTEXITCODE -ne 0){
            Remove-Item $full -Force
            Write-Host "Removed installer-created untracked file: $rel"
        }
    }
}

$status=@(git -C $root status --porcelain)
$tracked=@($status | Where-Object {$_ -notmatch '^\?\?'})
$untracked=@($status | Where-Object {$_ -match '^\?\?'})

if($tracked.Count -gt 0){
    $tracked | ForEach-Object {Write-Host $_}
    Fail "Tracked working-tree changes remain."
}

# Known legacy-cleanup helper files may also have been copied untracked to main.
$legacyKnown=@(
    "scripts/Cleanup-Wave2C-SecretScanLegacyMaintenance.ps1",
    "scripts/CommitPush-Wave2C-SecretScanLegacyCleanup.ps1",
    "scripts/Test-Wave2C-SecretScanLegacyCleanup.ps1"
)
foreach($rel in $legacyKnown){
    $full=Join-Path $root ($rel -replace '/','\')
    if(Test-Path $full){
        $trackedFile=git -C $root ls-files --error-unmatch -- $rel 2>$null
        if($LASTEXITCODE -ne 0){
            Remove-Item $full -Force
            Write-Host "Removed untracked legacy helper: $rel"
        }
    }
}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){
    $status | ForEach-Object {Write-Host $_}
    Fail "Repository is not clean after removing known installer/helper files. Review remaining paths manually."
}

Write-Host "PASS: main is clean and synchronized." -ForegroundColor Green

$closeout=Join-Path $root "generated\wave2c\annual-review-closeout\wave2c_closeout_certification.json"
$recon=Join-Path $root "generated\wave2c\annual-review-closeout\inheritance_status_reconciliation.json"
$queue=Join-Path $root "generated\wave2c\remediation_queue.csv"
$impact=Join-Path $root "generated\wave2\inheritance\inheritance_impact_report.json"
$higher=Join-Path $root "generated\wave2\inheritance\higher_scope_results.json"

foreach($p in @($closeout,$recon,$queue,$impact,$higher)){
    if(-not(Test-Path $p)){Fail "Required artifact missing: $p"}
}

$c=Get-Content $closeout -Raw|ConvertFrom-Json
$r=Get-Content $recon -Raw|ConvertFrom-Json

if($c.status -ne "PASS"){Fail "Closeout status is not PASS."}
if($c.wave2c_state -ne "CLOSED"){Fail "Wave 2C state is not CLOSED."}
if([int]$c.open_remediation_count -ne 0){Fail "Open remediation count is not zero."}
if($c.inheritance_validation -ne "PASS"){Fail "Inheritance validation is not PASS."}
if($r.status -ne "PASS"){Fail "Inheritance reconciliation is not PASS."}
if($r.control_results_changed -ne $false){Fail "Control results changed flag is not false."}
if($r.remediation_population_changed -ne $false){Fail "Remediation population changed flag is not false."}
if($r.evidence_artifacts_changed -ne $false){Fail "Evidence artifacts changed flag is not false."}

$rows=@(Import-Csv $queue)
if(@($rows|Where-Object{$_.remediation_state -eq "OPEN"}).Count -ne 0){
    Fail "Open remediation rows remain."
}

function Hash([string]$p){
    (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
}

$out=Join-Path $root "release\wave2c\post-merge"
New-Item -ItemType Directory -Force -Path $out|Out-Null

$cert=[ordered]@{
    wave="2C"
    release=$Tag
    status="PASS"
    certified_at_utc=[DateTime]::UtcNow.ToString("o")
    branch="main"
    merge_commit_sha=$head
    origin_main_sha=$origin
    closeout_status="PASS"
    wave2c_state="CLOSED"
    open_remediation_count=0
    inheritance_validation="PASS"
    closeout_certification_sha256=Hash $closeout
    reconciliation_record_sha256=Hash $recon
    remediation_queue_sha256=Hash $queue
    inheritance_impact_sha256=Hash $impact
    higher_scope_results_sha256=Hash $higher
    tag_ready=$true
    control_results_changed=$false
}
$certPath=Join-Path $out "post_merge_certification.json"
$cert|ConvertTo-Json -Depth 20|Set-Content $certPath -Encoding UTF8

$artifacts=@($closeout,$recon,$queue,$impact,$higher,$certPath)
$manifestRows=@()
foreach($p in $artifacts){
    $manifestRows += [pscustomobject]@{
        path=$p.Substring($root.Length+1).Replace("\","/")
        size_bytes=(Get-Item $p).Length
        sha256=Hash $p
    }
}
$manifest=[ordered]@{
    wave="2C"
    release=$Tag
    frozen_at_utc=[DateTime]::UtcNow.ToString("o")
    merge_commit_sha=$head
    artifact_count=$manifestRows.Count
    control_results_changed=$false
    artifacts=$manifestRows
}
$manifestPath=Join-Path $out "wave2c_post_merge_manifest.json"
$manifest|ConvertTo-Json -Depth 20|Set-Content $manifestPath -Encoding UTF8

$zipPath=Join-Path $out "$Tag.zip"
if(Test-Path $zipPath){Remove-Item $zipPath -Force}

$stage=Join-Path $env:TEMP ("wave2c-postmerge-"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $stage|Out-Null
try{
    foreach($p in $artifacts){
        $rel=$p.Substring($root.Length+1)
        $dest=Join-Path $stage $rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest)|Out-Null
        Copy-Item $p $dest
    }
    $manifestDest=Join-Path $stage "release-manifest\wave2c_post_merge_manifest.json"
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $manifestDest)|Out-Null
    Copy-Item $manifestPath $manifestDest
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -CompressionLevel Optimal
} finally {
    Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
}

$summary=[ordered]@{
    status="PASS"
    release=$Tag
    merge_commit_sha=$head
    release_zip=$zipPath
    release_zip_sha256=Hash $zipPath
    manifest_sha256=Hash $manifestPath
    control_results_changed=$false
}
$summary|ConvertTo-Json -Depth 20|Set-Content (Join-Path $out "release_summary.json") -Encoding UTF8

Write-Host "`n=== Certification ===" -ForegroundColor Cyan
$cert|ConvertTo-Json -Depth 20
Write-Host "`n=== Release summary ===" -ForegroundColor Cyan
$summary|ConvertTo-Json -Depth 20

Write-Host "`nPASS: Wave 2C post-merge release certified from clean main." -ForegroundColor Green
Write-Host "NOTE: release artifacts are now untracked under release\wave2c\post-merge; tagging is authorized against commit $head."
