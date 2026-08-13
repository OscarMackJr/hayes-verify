[CmdletBinding()]
param(
    [string]$Repo = "OscarMackJr/ems",
    [int]$PR = 1,
    [string]$EMSPath = "C:\temp\standars\ems",
    [switch]$MarkReady,
    [switch]$Merge
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    throw "NOT READY: $Message"
}

Write-Host "=== Inspect Wave 2B PR ===" -ForegroundColor Cyan

if(-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Fail "GitHub CLI (gh) is not installed."
}

gh auth status
if($LASTEXITCODE -ne 0) {
    Fail "gh is not authenticated."
}

$jsonFields = "number,title,url,state,isDraft,mergeable,mergeStateStatus,reviewDecision,headRefName,baseRefName,headRefOid,statusCheckRollup"

$raw = gh pr view $PR --repo $Repo --json $jsonFields
if($LASTEXITCODE -ne 0) {
    Fail "Unable to inspect PR #$PR."
}

$pr = $raw | ConvertFrom-Json

Write-Host ""
[pscustomobject]@{
    PR               = $pr.number
    Title            = $pr.title
    State            = $pr.state
    Draft            = $pr.isDraft
    Head             = $pr.headRefName
    Base             = $pr.baseRefName
    Mergeable        = $pr.mergeable
    MergeStateStatus = $pr.mergeStateStatus
    ReviewDecision   = $pr.reviewDecision
    HeadSha          = $pr.headRefOid
    Url              = $pr.url
} | Format-List

if($pr.state -ne "OPEN") {
    Fail "PR state is $($pr.state), expected OPEN."
}

if($pr.headRefName -ne "feature/wave2-closeout") {
    Fail "Unexpected head branch: $($pr.headRefName)."
}

if($pr.baseRefName -ne "main") {
    Fail "Unexpected base branch: $($pr.baseRefName)."
}

if($pr.mergeable -eq "CONFLICTING") {
    Fail "PR has merge conflicts."
}

if($pr.mergeable -eq "UNKNOWN") {
    Fail "GitHub mergeability is still UNKNOWN. Re-run after GitHub finishes calculating it."
}

$blockingMergeStates = @(
    "BEHIND",
    "BLOCKED",
    "DIRTY",
    "DRAFT",
    "HAS_HOOKS",
    "UNSTABLE"
)

if($pr.mergeStateStatus -in $blockingMergeStates) {
    Fail "mergeStateStatus is $($pr.mergeStateStatus)."
}

Write-Host ""
Write-Host "=== Inspect changed paths ===" -ForegroundColor Cyan

$files = @(gh pr diff $PR --repo $Repo --name-only)
if($LASTEXITCODE -ne 0) {
    Fail "Unable to retrieve PR changed files."
}

$files | Sort-Object | ForEach-Object { Write-Host $_ }

if(-not $files) {
    Fail "PR contains no changed files."
}

$generated = @($files | Where-Object { $_ -like "generated/*" })
if($generated.Count -gt 0) {
    Fail "Ignored generated/ working output is present in the PR: $($generated -join ', ')"
}

if(-not (@($files | Where-Object { $_ -like "release/wave2b-closeout/*" }).Count -gt 0)) {
    Fail "Frozen Wave 2B closeout package is missing from the PR."
}

$allowedRoots = @(
    "registry/",
    "schemas/",
    "evidence/",
    "registers/",
    "scripts/",
    "release/wave2b-closeout/"
)

$unexpected = @(
    $files | Where-Object {
        $f = $_
        -not ($allowedRoots | Where-Object { $f.StartsWith($_) })
    }
)

if($unexpected.Count -gt 0) {
    Fail "Unexpected paths are included in the PR: $($unexpected -join ', ')"
}

Write-Host ""
Write-Host "=== Validate local Wave 2B certification ===" -ForegroundColor Cyan

$certPath = Join-Path $EMSPath "generated\wave2\closeout-certification\wave2b_certification.json"
$freezePath = Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"
$zipPath = Join-Path $EMSPath "release\wave2b-closeout\EMS_Wave2B_BranchReady_Closeout.zip"

foreach($required in @($certPath,$freezePath,$zipPath)) {
    if(-not(Test-Path $required)) {
        Fail "Required closeout artifact missing: $required"
    }
}

$cert = Get-Content $certPath -Raw | ConvertFrom-Json
$freeze = Get-Content $freezePath -Raw | ConvertFrom-Json

if($cert.status -ne "PASS") {
    Fail "Wave 2B certification is not PASS."
}

if([int]$cert.higher_scope_authority.undispositioned_control_count -ne 0) {
    Fail "Undispositioned higher-scope controls remain."
}

if([int]$cert.repository_reconciliation.undispositioned_row_count -ne 0) {
    Fail "Undispositioned higher-scope rows remain."
}

if(-not $cert.repository_reconciliation.authoritative_unresolved_count_matches) {
    Fail "Unresolved higher-scope rows do not reconcile to controlled remediation."
}

$actualHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
$expectedHash = ([string]$freeze.zip_sha256).ToLower()

if($actualHash -ne $expectedHash) {
    Fail "Frozen closeout ZIP SHA-256 does not match freeze_summary.json."
}

Write-Host "Certification: $($cert.certification_state)"
Write-Host "Inherited rows: $($cert.inheritance_authority.inherited_count)"
Write-Host "Controlled remediation rows: $($cert.repository_reconciliation.controlled_remediation_row_count)"
Write-Host "ZIP SHA-256: $actualHash"

Write-Host ""
Write-Host "=== Inspect GitHub checks ===" -ForegroundColor Cyan

$checks = @($pr.statusCheckRollup)

if($checks.Count -eq 0) {
    Fail "No GitHub status checks are reported. EMS closeout should not be merged without a CI/check result."
}

$badChecks = @()
$checkRows = @()

foreach($c in $checks) {
    $name = if($c.name) { $c.name } elseif($c.context) { $c.context } else { "<unnamed>" }
    $state = if($c.conclusion) { $c.conclusion } elseif($c.state) { $c.state } elseif($c.status) { $c.status } else { "UNKNOWN" }

    $checkRows += [pscustomobject]@{
        Check = $name
        State = $state
    }

    if($state -notin @("SUCCESS","NEUTRAL","SKIPPED")) {
        $badChecks += "$name=$state"
    }
}

$checkRows | Format-Table -AutoSize

if($badChecks.Count -gt 0) {
    Fail "Non-successful checks remain: $($badChecks -join ', ')"
}

if($pr.reviewDecision -eq "CHANGES_REQUESTED") {
    Fail "PR has requested changes."
}

Write-Host ""
Write-Host "PASS: PR #$PR satisfies the Wave 2B merge gate." -ForegroundColor Green

if($pr.isDraft) {
    if($MarkReady -or $Merge) {
        Write-Host ""
        Write-Host "Marking PR ready for review..." -ForegroundColor Cyan
        gh pr ready $PR --repo $Repo
        if($LASTEXITCODE -ne 0) {
            Fail "Failed to mark PR ready."
        }
    }
    else {
        Write-Host ""
        Write-Host "PR is still a draft. Re-run with -MarkReady or -Merge when ready." -ForegroundColor Yellow
        exit 0
    }
}

if($Merge) {
    Write-Host ""
    Write-Host "=== Merge PR ===" -ForegroundColor Cyan

    $finalFields = "headRefOid,mergeable,mergeStateStatus,state"
    $latestRaw = gh pr view $PR --repo $Repo --json $finalFields
    if($LASTEXITCODE -ne 0) {
        Fail "Unable to perform final pre-merge inspection."
    }

    $latest = $latestRaw | ConvertFrom-Json

    if($latest.state -ne "OPEN") {
        Fail "PR is no longer OPEN."
    }

    if($latest.headRefOid -ne $pr.headRefOid) {
        Fail "PR head moved during inspection. Re-run the script."
    }

    if($latest.mergeable -ne "MERGEABLE") {
        Fail "PR is no longer mergeable."
    }

    if($latest.mergeStateStatus -in $blockingMergeStates) {
        Fail "PR merge state changed to $($latest.mergeStateStatus)."
    }

    gh pr merge $PR --repo $Repo --squash --delete-branch `
        --subject "Wave 2B higher-scope closeout" `
        --body "Merge certified Wave 2B higher-scope closeout. The frozen release package preserves the certified evidence baseline and controlled-remediation state."

    if($LASTEXITCODE -ne 0) {
        Fail "GitHub merge command failed."
    }

    Write-Host ""
    Write-Host "PASS: PR #$PR merged to main and remote branch deletion requested." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Inspection only. No merge performed." -ForegroundColor Yellow
    Write-Host "To merge after this gate passes:"
    Write-Host "  .\scripts\Inspect-And-Merge-Wave2BPR.ps1 -Merge"
}
