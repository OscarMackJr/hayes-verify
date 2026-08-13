[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$PackageRoot = "C:\temp\t4",
    [string]$BranchName = "feature/wave2c-remediation"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message){
    throw "WAVE 2C BOOTSTRAP BLOCKED: $Message"
}

Push-Location $EMSPath
try{
    Write-Host "=== Wave 2C Bootstrap ===" -ForegroundColor Cyan

    $branch = (git branch --show-current).Trim()
    if($LASTEXITCODE -ne 0){ Fail "Unable to determine current branch." }

    if($branch -ne "main"){
        Fail "Bootstrap must start from main; current branch is '$branch'."
    }

    Write-Host ""
    Write-Host "Cleaning previously installed untracked Wave 2C bootstrap files..." -ForegroundColor Cyan

    $bootstrapFiles = @(
        "registry\wave2c_remediation_intake_spec.json",
        "scripts\Build-Wave2CRemediationQueue.py",
        "scripts\Validate-Wave2CRemediationQueue.py",
        "scripts\Initialize-Wave2C.ps1",
        "scripts\Show-Wave2CRemediationQueue.ps1"
    )

    foreach($relative in $bootstrapFiles){
        $path = Join-Path $EMSPath $relative

        if(Test-Path $path){
            # Only remove if untracked. Never delete a tracked file from main.
            git ls-files --error-unmatch -- $relative *> $null
            if($LASTEXITCODE -eq 0){
                Fail "Refusing to remove tracked main-branch file: $relative"
            }

            Remove-Item $path -Force
            Write-Host "Removed untracked $relative"
        }
    }

    git fetch origin
    if($LASTEXITCODE -ne 0){ Fail "git fetch origin failed." }

    $status = @(git status --porcelain)
    if($status.Count -gt 0){
        Write-Host ""
        Write-Host "Remaining working tree changes:" -ForegroundColor Yellow
        $status | ForEach-Object { Write-Host $_ }
        Fail "Working tree is not clean after Wave 2C bootstrap cleanup."
    }

    $head = (git rev-parse HEAD).Trim()
    $origin = (git rev-parse origin/main).Trim()
    if($head -ne $origin){
        Fail "main does not match origin/main."
    }

    Write-Host ""
    Write-Host "Creating Wave 2C branch from clean main..." -ForegroundColor Cyan

    $existing = git branch --list $BranchName
    if([string]::IsNullOrWhiteSpace(($existing -join ""))){
        git checkout -b $BranchName
    }
    else{
        git checkout $BranchName
    }

    if($LASTEXITCODE -ne 0){
        Fail "Failed to enter branch $BranchName."
    }

    Write-Host ""
    Write-Host "Installing Wave 2C tooling onto $BranchName..." -ForegroundColor Cyan

    $installer = Join-Path $PackageRoot "scripts\Install-Wave2CInitialization.ps1"
    if(-not(Test-Path $installer)){
        Fail "Wave 2C installer not found: $installer"
    }

    & $installer -EMSPath $EMSPath
    if($LASTEXITCODE -ne 0){
        Fail "Wave 2C tooling installation failed."
    }

    Write-Host ""
    Write-Host "Running Wave 2C initialization..." -ForegroundColor Cyan

    & (Join-Path $EMSPath "scripts\Initialize-Wave2C.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE -ne 0){
        Fail "Wave 2C initialization failed."
    }

    Write-Host ""
    Write-Host "Showing Wave 2C intake..." -ForegroundColor Cyan

    & (Join-Path $EMSPath "scripts\Show-Wave2CRemediationQueue.ps1") -EMSPath $EMSPath

    Write-Host ""
    Write-Host "Wave 2C source changes are intentionally uncommitted at this checkpoint." -ForegroundColor Yellow
    git status --short

    Write-Host ""
    Write-Host "PASS: Wave 2C branch bootstrapped and remediation intake initialized." -ForegroundColor Green
}
finally{
    Pop-Location
}
