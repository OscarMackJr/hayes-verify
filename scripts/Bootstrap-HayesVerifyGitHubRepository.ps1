[CmdletBinding()]
param(
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$GitHubRepo="OscarMackJr/hayes-verify",
    [string]$DefaultBranch="main"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY GITHUB BOOTSTRAP BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

if(-not(Test-Path ".gitignore")){
    Copy-Item "$root\templates\.gitignore" "$root\.gitignore" -Force
}
if(-not(Test-Path "AUTHORITY.md")){
    Copy-Item "$root\templates\AUTHORITY.md" "$root\AUTHORITY.md" -Force
}
New-Item -ItemType Directory -Force -Path "$root\.github\workflows" | Out-Null
Copy-Item "$root\templates\validate.yml" "$root\.github\workflows\validate.yml" -Force

& "$root\scripts\Run-HayesVerifyPrePublicationCertification.ps1" -HayesPath $root
if(-not $?){Fail "pre-publication certification failed"}

if(-not(Test-Path "$root\.git")){
    git init
    if($LASTEXITCODE){Fail "git init failed"}
}

$current=(git branch --show-current).Trim()
if([string]::IsNullOrWhiteSpace($current)){
    git checkout -b $DefaultBranch
    if($LASTEXITCODE){Fail "failed to create default branch"}
}
elseif($current -ne $DefaultBranch){
    Fail "expected branch $DefaultBranch; current=$current"
}

$remote = git remote get-url origin 2>$null
if($LASTEXITCODE -ne 0){
    git remote add origin "https://github.com/$GitHubRepo.git"
    if($LASTEXITCODE){Fail "failed to add origin remote"}
}
elseif($remote -notmatch [regex]::Escape($GitHubRepo)){
    Fail "origin remote does not point to $GitHubRepo"
}

$trackedSensitive = @(git ls-files |
    Where-Object {
        $_ -match '(^|/)(evidence|generated)/' -or
        $_ -match '(^|/)\.env($|\.)' -or
        $_ -match '(^|/)\.venv/'
    })
if($trackedSensitive.Count){
    $trackedSensitive | ForEach-Object {Write-Host "BLOCKED TRACKED PATH: $_" -ForegroundColor Red}
    Fail "sensitive/runtime path already tracked"
}

git add .gitignore AUTHORITY.md README.md pyproject.toml src tests contracts scripts `
    registry schemas .github
if($LASTEXITCODE){Fail "initial staging failed"}

$staged=@(git diff --cached --name-only)
$bad=@($staged | Where-Object {
    $_ -match '(^|/)(evidence|generated)/' -or
    $_ -match '(^|/)\.env($|\.)' -or
    $_ -match '(^|/)\.venv/'
})
if($bad.Count){
    $bad | ForEach-Object {Write-Host "BLOCKED STAGED PATH: $_" -ForegroundColor Red}
    Fail "sensitive/runtime file staged"
}

if(-not(git diff --cached --quiet)){
    git commit -m "establish Hayes Verify initial controlled baseline"
    if($LASTEXITCODE){Fail "initial commit failed"}
}

Write-Host "PASS: local initial controlled baseline commit prepared." -ForegroundColor Green
