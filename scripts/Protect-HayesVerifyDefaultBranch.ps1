[CmdletBinding()]
param(
    [string]$GitHubRepo="OscarMackJr/hayes-verify",
    [string]$Branch="main"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY BRANCH PROTECTION BLOCKED: $m"}

$repoJson=gh api "repos/$GitHubRepo"
if($LASTEXITCODE){Fail "repository metadata lookup failed"}

$body=@{
    required_status_checks = @{
        strict = $true
        contexts = @("EMS Validate/validate", "Hayes Verify Validate/validate")
    }
    enforce_admins = $true
    required_pull_request_reviews = @{
        required_approving_review_count = 1
    }
    restrictions = $null
    required_linear_history = $false
    allow_force_pushes = $false
    allow_deletions = $false
} | ConvertTo-Json -Depth 10

$tmp=[System.IO.Path]::GetTempFileName()
Set-Content $tmp $body -Encoding UTF8

gh api `
  --method PUT `
  -H "Accept: application/vnd.github+json" `
  "repos/$GitHubRepo/branches/$Branch/protection" `
  --input $tmp
$rc=$LASTEXITCODE
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
if($rc){Fail "branch protection update failed"}

Write-Host "PASS: Hayes Verify default branch protection configured." -ForegroundColor Green
