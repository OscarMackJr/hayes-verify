[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$expected=@(
  "src\hayes_verify\pilots\github_collectors.py",
  "tests\test_github_api_invocation.py",
  "registry\hayes_verify_github_api_invocation_hotfix_spec.json",
  "scripts\Test-HayesVerifyGitHubApiInvocationHotfix.ps1",
  "scripts\Test-HayesVerifyGitHubApiInvocationInstall.ps1"
)

$missing=@()
foreach($rel in $expected){
    if(-not(Test-Path (Join-Path $HayesPath $rel))){
        $missing += $rel
    }
}

if($missing.Count -gt 0){
    $missing|ForEach-Object{Write-Host "MISSING: $_" -ForegroundColor Red}
    throw "GitHub API invocation hotfix installation incomplete."
}

Write-Host "PASS: GitHub API invocation hotfix installation verified." -ForegroundColor Green
