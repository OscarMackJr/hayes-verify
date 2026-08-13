[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$Repo = "OscarMackJr/ems",
    [string]$Tag = "ems-v0.5.0-wave2b",
    [string]$ReleaseTitle = "EMS v0.5.0 Wave 2B",
    [switch]$Publish
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    throw "RELEASE BLOCKED: $Message"
}

function Assert-File([string]$Path,[string]$Label) {
    if(-not(Test-Path $Path)){
        Fail "$Label not found: $Path"
    }
}

Push-Location $EMSPath
try {
    Write-Host "=== Wave 2B Post-Merge Release Certification ===" -ForegroundColor Cyan

    if(-not(Get-Command git -ErrorAction SilentlyContinue)){
        Fail "git is not available."
    }

    if(-not(Get-Command gh -ErrorAction SilentlyContinue)){
        Fail "GitHub CLI (gh) is not available."
    }

    Write-Host ""
    Write-Host "=== Verify repository state ===" -ForegroundColor Cyan

    git fetch origin
    if($LASTEXITCODE -ne 0){
        Fail "git fetch origin failed."
    }

    $branch = (git branch --show-current).Trim()
    if($LASTEXITCODE -ne 0){
        Fail "Unable to determine current branch."
    }

    if($branch -ne "main"){
        Fail "Current branch is '$branch'; expected 'main'."
    }

    $status = @(git status --porcelain)
    if($LASTEXITCODE -ne 0){
        Fail "git status failed."
    }

    if($status.Count -gt 0){
        Write-Host "Working tree changes:" -ForegroundColor Yellow
        $status | ForEach-Object { Write-Host $_ }
        Fail "Working tree is not clean."
    }

    $head = (git rev-parse HEAD).Trim()
    $originMain = (git rev-parse origin/main).Trim()

    if($head -ne $originMain){
        Fail "HEAD does not match origin/main. HEAD=$head origin/main=$originMain"
    }

    Write-Host "Branch:        $branch"
    Write-Host "HEAD:          $head"
    Write-Host "origin/main:   $originMain"

    Write-Host ""
    Write-Host "=== Validate Wave 2B certification ===" -ForegroundColor Cyan

    $certPath = Join-Path $EMSPath "generated\wave2\closeout-certification\wave2b_certification.json"
    $freezePath = Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"
    $zipPath = Join-Path $EMSPath "release\wave2b-closeout\EMS_Wave2B_BranchReady_Closeout.zip"

    Assert-File $certPath "Wave 2B certification"
    Assert-File $freezePath "Wave 2B freeze summary"
    Assert-File $zipPath "Wave 2B closeout ZIP"

    $cert = Get-Content $certPath -Raw | ConvertFrom-Json
    $freeze = Get-Content $freezePath -Raw | ConvertFrom-Json

    if($cert.status -ne "PASS"){
        Fail "Wave 2B certification status is '$($cert.status)'."
    }

    if($cert.certification_state -notin @(
        "CERTIFIED",
        "CERTIFIED_WITH_CONTROLLED_REMEDIATION"
    )){
        Fail "Unexpected certification_state '$($cert.certification_state)'."
    }

    if([int]$cert.higher_scope_authority.undispositioned_control_count -ne 0){
        Fail "Undispositioned higher-scope controls remain."
    }

    if([int]$cert.repository_reconciliation.undispositioned_row_count -ne 0){
        Fail "Undispositioned higher-scope rows remain."
    }

    if(-not $cert.repository_reconciliation.authoritative_unresolved_count_matches){
        Fail "Authoritative unresolved count does not reconcile."
    }

    $controlledRows = [int]$cert.repository_reconciliation.controlled_remediation_row_count
    $unresolvedRows = [int]$cert.inheritance_authority.unresolved_higher_scope_count

    if($controlledRows -ne $unresolvedRows){
        Fail "Controlled remediation rows ($controlledRows) do not equal unresolved higher-scope rows ($unresolvedRows)."
    }

    if($freeze.status -ne "PASS"){
        Fail "Freeze summary is not PASS."
    }

    $actualHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
    $expectedHash = ([string]$freeze.zip_sha256).ToLower()

    if($actualHash -ne $expectedHash){
        Fail "Frozen ZIP SHA-256 mismatch."
    }

    [pscustomobject]@{
        CertificationState        = $cert.certification_state
        HigherScopeControls       = $cert.higher_scope_authority.control_count
        PassingControls           = $cert.higher_scope_authority.pass_control_count
        RemediationControls       = $cert.higher_scope_authority.controlled_remediation_control_count
        InheritedRows             = $cert.inheritance_authority.inherited_count
        ControlledRemediationRows = $controlledRows
        UndispositionedControls   = $cert.higher_scope_authority.undispositioned_control_count
        UndispositionedRows       = $cert.repository_reconciliation.undispositioned_row_count
        ZipSha256                 = $actualHash
    } | Format-List

    Write-Host ""
    Write-Host "=== Check tag/release uniqueness ===" -ForegroundColor Cyan

    $localTag = git tag --list $Tag
    if($LASTEXITCODE -ne 0){
        Fail "Unable to query local tags."
    }

    $remoteTag = git ls-remote --tags origin "refs/tags/$Tag"
    if($LASTEXITCODE -ne 0){
        Fail "Unable to query remote tag state."
    }

    if(-not [string]::IsNullOrWhiteSpace(($localTag -join ""))){
        Fail "Local tag '$Tag' already exists."
    }

    if(-not [string]::IsNullOrWhiteSpace(($remoteTag -join ""))){
        Fail "Remote tag '$Tag' already exists."
    }

    gh release view $Tag --repo $Repo *> $null
    $releaseExists = ($LASTEXITCODE -eq 0)

    if($releaseExists){
        Fail "GitHub release '$Tag' already exists."
    }

    Write-Host "Tag '$Tag' is available."
    Write-Host "GitHub release '$Tag' does not exist."

    Write-Host ""
    Write-Host "PASS: Wave 2B post-merge release gate satisfied." -ForegroundColor Green

    if(-not $Publish){
        Write-Host ""
        Write-Host "Dry run only. Nothing published." -ForegroundColor Yellow
        Write-Host "To publish:"
        Write-Host "  .\scripts\Publish-Wave2BPostMergeRelease.ps1 -Publish"
        exit 0
    }

    Write-Host ""
    Write-Host "=== Create annotated tag ===" -ForegroundColor Cyan

    $tagMessage = @"
EMS Wave 2B certified higher-scope closeout

Certification state: $($cert.certification_state)
Higher-scope controls: $($cert.higher_scope_authority.control_count)
Passing controls: $($cert.higher_scope_authority.pass_control_count)
Controlled remediation controls: $($cert.higher_scope_authority.controlled_remediation_control_count)
Inherited rows: $($cert.inheritance_authority.inherited_count)
Controlled remediation rows: $controlledRows
Undispositioned controls: $($cert.higher_scope_authority.undispositioned_control_count)
Undispositioned rows: $($cert.repository_reconciliation.undispositioned_row_count)
Frozen ZIP SHA-256: $actualHash
Commit: $head
"@

    git tag -a $Tag $head -m $tagMessage
    if($LASTEXITCODE -ne 0){
        Fail "Failed to create annotated tag '$Tag'."
    }

    git push origin $Tag
    if($LASTEXITCODE -ne 0){
        Fail "Failed to push tag '$Tag'."
    }

    Write-Host ""
    Write-Host "=== Create GitHub release ===" -ForegroundColor Cyan

    $releaseNotes = @"
## Wave 2B Higher-Scope Closeout

Wave 2B is certified and released from commit `$head`.

### Certification
- State: **$($cert.certification_state)**
- Higher-scope controls: $($cert.higher_scope_authority.control_count)
- Passing controls: $($cert.higher_scope_authority.pass_control_count)
- Controlled-remediation controls: $($cert.higher_scope_authority.controlled_remediation_control_count)
- Inherited repository rows: $($cert.inheritance_authority.inherited_count)
- Controlled-remediation repository rows: $controlledRows
- Undispositioned controls: $($cert.higher_scope_authority.undispositioned_control_count)
- Undispositioned rows: $($cert.repository_reconciliation.undispositioned_row_count)

### Frozen Baseline
- Artifact: `EMS_Wave2B_BranchReady_Closeout.zip`
- SHA-256: `$actualHash`

The release preserves the Wave 2B certified evidence baseline and open controlled-remediation state.
"@

    gh release create $Tag `
        $zipPath `
        --repo $Repo `
        --title $ReleaseTitle `
        --notes $releaseNotes `
        --verify-tag

    if($LASTEXITCODE -ne 0){
        Fail "GitHub release creation failed."
    }

    Write-Host ""
    Write-Host "=== Verify published release ===" -ForegroundColor Cyan

    $published = gh release view $Tag --repo $Repo --json tagName,name,url,isDraft,isPrerelease,targetCommitish | ConvertFrom-Json
    if($LASTEXITCODE -ne 0){
        Fail "Unable to verify published GitHub release."
    }

    if($published.tagName -ne $Tag){
        Fail "Published release tag mismatch."
    }

    if($published.isDraft){
        Fail "Published release is unexpectedly still a draft."
    }

    Write-Host ""
    [pscustomobject]@{
        Tag         = $published.tagName
        ReleaseName = $published.name
        Url         = $published.url
        Commit      = $head
        ZipSha256   = $actualHash
    } | Format-List

    Write-Host ""
    Write-Host "PASS: Wave 2B post-merge release published successfully." -ForegroundColor Green
}
finally {
    Pop-Location
}
