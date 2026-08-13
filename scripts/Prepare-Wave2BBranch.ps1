[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$BranchName="feature/wave2-closeout",
    [switch]$Push
)

$ErrorActionPreference="Stop"
Push-Location $EMSPath
try{
    $cert=Join-Path $EMSPath "generated\wave2\closeout-certification\wave2b_certification.json"
    $freeze=Join-Path $EMSPath "release\wave2b-closeout\freeze_summary.json"

    if(-not(Test-Path $cert)){throw "Wave 2B certification not found."}
    if(-not(Test-Path $freeze)){throw "Wave 2B freeze not found. Run closeout with -Freeze first."}

    $c=Get-Content $cert -Raw|ConvertFrom-Json
    if($c.status -ne "PASS"){throw "Wave 2B certification status is not PASS."}

    git status --short
    if($LASTEXITCODE-ne 0){throw "git status failed."}

    git checkout -b $BranchName
    if($LASTEXITCODE-ne 0){throw "Failed to create branch $BranchName."}

    git add registry schemas evidence registers scripts generated/wave2 release/wave2b-closeout
    if($LASTEXITCODE-ne 0){throw "git add failed."}

    git commit -m "certify Wave 2B higher-scope closeout"
    if($LASTEXITCODE-ne 0){throw "git commit failed."}

    if($Push){
        git push -u origin $BranchName
        if($LASTEXITCODE-ne 0){throw "git push failed."}
    }

    Write-Host "Branch-ready Wave 2B closeout committed on $BranchName." -ForegroundColor Green
}
finally{
    Pop-Location
}
