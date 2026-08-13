[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$pkg=Split-Path -Parent $here

Copy-Item "$pkg\registry\wave2c1c_ctrl072_promotion_spec.json" "$EMSPath\registry\wave2c1c_ctrl072_promotion_spec.json" -Force
Copy-Item "$pkg\schemas\wave2c1c_ctrl072_promotion_record.schema.json" "$EMSPath\schemas\wave2c1c_ctrl072_promotion_record.schema.json" -Force

foreach($n in @(
    "Promote-Wave2C1c-CTRL072.py",
    "Validate-Wave2C1c-CTRL072.py",
    "Run-Wave2C1c-CTRL072.ps1",
    "Show-Wave2C1c-CTRL072.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

$py=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$py=$candidate}
}
if(-not $py){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$py=$cmd.Source}
}
if(-not $py){throw "No usable Python interpreter found."}

foreach($n in @("Promote-Wave2C1c-CTRL072.py","Validate-Wave2C1c-CTRL072.py")){
    & $py -m py_compile (Join-Path $EMSPath "scripts\$n")
    if($LASTEXITCODE-ne 0){throw "Python syntax validation failed: $n"}
}

foreach($n in @("Run-Wave2C1c-CTRL072.ps1","Show-Wave2C1c-CTRL072.ps1")){
    $t=$null;$e=$null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $EMSPath "scripts\$n"),
        [ref]$t,[ref]$e
    )|Out-Null
    if($e.Count-gt 0){$e|Format-List;throw "PowerShell parser validation failed: $n"}
}

Write-Host "Wave 2C.1c CTRL-072 explicit-promotion tooling installed." -ForegroundColor Green
