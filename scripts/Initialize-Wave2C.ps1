[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[string]$BranchName="feature/wave2c-remediation",[switch]$CreateBranch)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C INIT BLOCKED: $m"}
Push-Location $EMSPath
try{
 Write-Host "=== Wave 2C Initialization & Remediation Intake ===" -ForegroundColor Cyan
 $branch=(git branch --show-current).Trim(); if($LASTEXITCODE-ne 0){Fail "Unable to determine current branch."}
 if($branch -ne "main" -and $branch -ne $BranchName){Fail "Current branch '$branch' is neither main nor $BranchName."}
 git fetch origin; if($LASTEXITCODE-ne 0){Fail "git fetch origin failed."}
 if($branch -eq "main"){
   $head=(git rev-parse HEAD).Trim();$origin=(git rev-parse origin/main).Trim()
   if($head-ne$origin){Fail "main does not match origin/main."}
   $status=@(git status --porcelain); if($status.Count-gt 0){$status|%{Write-Host $_};Fail "Working tree must be clean."}
   if($CreateBranch){
     $exists=git branch --list $BranchName
     if([string]::IsNullOrWhiteSpace(($exists-join""))){git checkout -b $BranchName}else{git checkout $BranchName}
     if($LASTEXITCODE-ne 0){Fail "Failed to enter $BranchName."}
   }
 }
 $py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
 $spec=Join-Path $EMSPath "registry\wave2c_remediation_intake_spec.json";$out=Join-Path $EMSPath "generated\wave2c"
 New-Item -ItemType Directory -Path $out -Force|Out-Null
 if(-not(Test-Path $spec)){Fail "Wave 2C intake spec not found."}
 & $py (Join-Path $EMSPath "scripts\Build-Wave2CRemediationQueue.py") --ems-root $EMSPath --spec $spec --outdir $out
 if($LASTEXITCODE-ne 0){Fail "Queue build failed."}
 & $py (Join-Path $EMSPath "scripts\Validate-Wave2CRemediationQueue.py") --outdir $out --report (Join-Path $out "validation_report.json")
 if($LASTEXITCODE-ne 0){Fail "Queue validation failed."}
 Write-Host "PASS: Wave 2C initialized. No evidence promoted." -ForegroundColor Green
}finally{Pop-Location}
