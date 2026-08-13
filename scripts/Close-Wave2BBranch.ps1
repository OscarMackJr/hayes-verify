[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$BranchName = "feature/wave2-closeout",
    [string]$BaseBranch = "main",
    [string]$CommitMessage = "certify Wave 2B higher-scope closeout",
    [switch]$Push,
    [switch]$CreatePR
)

$ErrorActionPreference = "Stop"

function Assert-File {
    param([string]$Path,[string]$Label)
    if(-not(Test-Path $Path)){
        throw "$Label not found: $Path"
    }
}

Push-Location $EMSPath
try {
    Write-Host "=== Wave 2B Branch Closeout Patch ===" -ForegroundColor Cyan

    $certPath = Join-Path $EMSPath "generated\wave2\closeout-certification\wave2b_certification.json"
    $freezePath = Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"
    $zipPath = Join-Path $EMSPath "release\wave2b-closeout\EMS_Wave2B_BranchReady_Closeout.zip"

    Assert-File $certPath "Wave 2B certification"
    Assert-File $freezePath "Wave 2B freeze summary"
    Assert-File $zipPath "Wave 2B closeout ZIP"

    $cert = Get-Content $certPath -Raw | ConvertFrom-Json
    $freeze = Get-Content $freezePath -Raw | ConvertFrom-Json

    if($cert.status -ne "PASS"){
        throw "Wave 2B certification is not PASS."
    }

    if($cert.repository_reconciliation.undispositioned_row_count -ne 0){
        throw "Undispositioned Wave 2B repository rows remain."
    }

    if($cert.higher_scope_authority.undispositioned_control_count -ne 0){
        throw "Undispositioned Wave 2B controls remain."
    }

    if(-not $cert.repository_reconciliation.authoritative_unresolved_count_matches){
        throw "Wave 2B unresolved/remediation reconciliation does not match."
    }

    $actualHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
    $expectedHash = ([string]$freeze.zip_sha256).ToLower()

    if($actualHash -ne $expectedHash){
        throw "Wave 2B closeout ZIP SHA-256 mismatch."
    }

    Write-Host ""
    Write-Host "Certification checkpoint passed." -ForegroundColor Green
    [pscustomobject]@{
        CertificationState = $cert.certification_state
        HigherScopeControls = $cert.higher_scope_authority.control_count
        PassingControls = $cert.higher_scope_authority.pass_control_count
        RemediationControls = $cert.higher_scope_authority.controlled_remediation_control_count
        InheritedRows = $cert.inheritance_authority.inherited_count
        UnresolvedRows = $cert.inheritance_authority.unresolved_higher_scope_count
        UndispositionedRows = $cert.repository_reconciliation.undispositioned_row_count
        ZipSha256 = $actualHash
    } | Format-List

    Write-Host ""
    Write-Host "=== Prepare branch ===" -ForegroundColor Cyan

    git fetch origin
    if($LASTEXITCODE -ne 0){ throw "git fetch failed." }

    $current = (git branch --show-current).Trim()
    if($LASTEXITCODE -ne 0){ throw "Unable to determine current branch." }

    if($current -ne $BranchName){
        $exists = git branch --list $BranchName
        if($LASTEXITCODE -ne 0){ throw "Unable to inspect local branches." }

        if([string]::IsNullOrWhiteSpace(($exists -join ""))){
            git checkout -b $BranchName
            if($LASTEXITCODE -ne 0){ throw "Failed to create branch $BranchName." }
        }
        else{
            git checkout $BranchName
            if($LASTEXITCODE -ne 0){ throw "Failed to checkout branch $BranchName." }
        }
    }

    Write-Host ""
    Write-Host "=== Stage controlled Wave 2B source ===" -ForegroundColor Cyan

    # Do NOT stage generated/. It is intentionally ignored working output.
    # The immutable Wave 2B evidence snapshot is carried by release/wave2b-closeout/.
    $stagePaths = @(
        "registry",
        "schemas",
        "evidence",
        "registers",
        "scripts",
        "release/wave2b-closeout"
    )

    foreach($p in $stagePaths){
        if(Test-Path $p){
            git add -- $p
            if($LASTEXITCODE -ne 0){ throw "git add failed for path: $p" }
        }
    }

    Write-Host ""
    Write-Host "Staged changes:" -ForegroundColor Cyan
    git status --short
    if($LASTEXITCODE -ne 0){ throw "git status failed." }

    $staged = git diff --cached --name-only
    if($LASTEXITCODE -ne 0){ throw "Unable to inspect staged changes." }

    if(-not $staged){
        throw "No staged Wave 2B closeout changes found."
    }

    $badGenerated = @($staged | Where-Object { $_ -like "generated/*" })
    if($badGenerated.Count -gt 0){
        throw "Generated working artifacts were staged unexpectedly: $($badGenerated -join ', ')"
    }

    if(-not (@($staged | Where-Object { $_ -like "release/wave2b-closeout/*" }).Count -gt 0)){
        throw "Frozen Wave 2B release package is not staged."
    }

    Write-Host ""
    Write-Host "=== Commit Wave 2B closeout ===" -ForegroundColor Cyan
    git commit -m $CommitMessage
    if($LASTEXITCODE -ne 0){ throw "git commit failed." }

    $commitSha = (git rev-parse HEAD).Trim()
    if($LASTEXITCODE -ne 0){ throw "Unable to determine closeout commit SHA." }

    Write-Host "Committed Wave 2B closeout: $commitSha" -ForegroundColor Green

    if($Push){
        Write-Host ""
        Write-Host "=== Push Wave 2B closeout branch ===" -ForegroundColor Cyan
        git push -u origin $BranchName
        if($LASTEXITCODE -ne 0){ throw "git push failed." }
    }
    else{
        Write-Host ""
        Write-Host "Push not requested." -ForegroundColor Yellow
    }

    if($CreatePR){
        if(-not $Push){
            throw "-CreatePR requires -Push so the remote branch exists."
        }

        Write-Host ""
        Write-Host "=== Create draft pull request ===" -ForegroundColor Cyan

        $gh = Get-Command gh -ErrorAction SilentlyContinue
        if(-not $gh){
            throw "GitHub CLI 'gh' is required to create the PR."
        }

        $existing = gh pr list --head $BranchName --base $BaseBranch --json number,url --limit 1 | ConvertFrom-Json
        if($LASTEXITCODE -ne 0){ throw "Unable to query existing PRs." }

        if($existing -and $existing.Count -gt 0){
            Write-Host "Existing PR already found: $($existing[0].url)" -ForegroundColor Yellow
        }
        else{
            $body = @"
## Wave 2B Closeout

Wave 2B higher-scope implementation is certified and frozen.

- Certification: $($cert.certification_state)
- Higher-scope controls: $($cert.higher_scope_authority.control_count)
- Passing controls: $($cert.higher_scope_authority.pass_control_count)
- Controlled remediation controls: $($cert.higher_scope_authority.controlled_remediation_control_count)
- Inherited repository rows: $($cert.inheritance_authority.inherited_count)
- Controlled-remediation repository rows: $($cert.repository_reconciliation.controlled_remediation_row_count)
- Undispositioned controls: $($cert.higher_scope_authority.undispositioned_control_count)
- Undispositioned rows: $($cert.repository_reconciliation.undispositioned_row_count)
- Frozen package SHA-256: $actualHash

Generated working artifacts remain ignored by design. The frozen release package under
`release/wave2b-closeout/` is the immutable Wave 2B evidence snapshot.
"@

            gh pr create `
                --base $BaseBranch `
                --head $BranchName `
                --title "Wave 2B higher-scope closeout" `
                --body $body `
                --draft

            if($LASTEXITCODE -ne 0){ throw "Failed to create Wave 2B PR." }
        }
    }

    Write-Host ""
    Write-Host "PASS: Wave 2B branch closeout completed without changing EMS control results." -ForegroundColor Green
}
finally {
    Pop-Location
}
