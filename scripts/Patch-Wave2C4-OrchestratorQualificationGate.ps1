[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Run-Wave2C4-AnnualReviewCloseout.ps1"
if(-not(Test-Path $target)){throw "Wave 2C.4 orchestrator not found: $target"}

$backup="$target.pre-wave2c4-qualification-gate.bak"
Copy-Item $target $backup -Force

$lines=[System.Collections.Generic.List[string]](Get-Content $target)

# Do not double-patch.
$joined=$lines -join "`n"
if($joined -match 'CTRL-080 not yet qualified; review/promotion skipped'){
    Write-Host "Wave 2C.4 orchestrator already contains qualification gate." -ForegroundColor Yellow
    exit 0
}

# Find the review section marker.
$reviewIndex=-1
for($i=0;$i -lt $lines.Count;$i++){
    if($lines[$i] -match 'Write-Host "`n=== Review CTRL-080 evidence ==="'){
        $reviewIndex=$i
        break
    }
}

if($reviewIndex -lt 0){
    Copy-Item $backup $target -Force
    throw "Expected CTRL-080 review section not found; original restored."
}

$gate=@(
    '',
    '$qualificationPath=Join-Path $out "qualification.json"',
    'if(-not(Test-Path $qualificationPath)){',
    '    Fail "CTRL-080 qualification artifact not found: $qualificationPath"',
    '}',
    '$qualification=Get-Content $qualificationPath -Raw | ConvertFrom-Json',
    '$ctrl=$qualification.control',
    '',
    '$qualified=(',
    '    $ctrl.status -eq "PASS" -and',
    '    $ctrl.sufficiency -eq "SUFFICIENT" -and',
    '    $ctrl.promotion_eligible -eq $true -and',
    '    $ctrl.promotion_status -eq "QUALIFIED_NOT_PROMOTED" -and',
    '    $ctrl.remediation_state -eq "OPEN"',
    ')',
    '',
    'if(-not $qualified){',
    '    Write-Host ""',
    '    Write-Host "CTRL-080 not yet qualified; review/promotion skipped." -ForegroundColor Yellow',
    '    Write-Host "Status: $($ctrl.status)"',
    '    Write-Host "Sufficiency: $($ctrl.sufficiency)"',
    '    Write-Host "Promotion eligible: $($ctrl.promotion_eligible)"',
    '    Write-Host "Missing assertions: $($ctrl.missing_assertions)"',
    '    Write-Host ""',
    '    Write-Host "PASS: Wave 2C.4 remains fail-closed with no promotion performed." -ForegroundColor Green',
    '    exit 0',
    '}',
    ''
)

for($j=$gate.Count-1;$j -ge 0;$j--){
    $lines.Insert($reviewIndex,$gate[$j])
}

Set-Content $target $lines -Encoding UTF8

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,
    [ref]$tokens,
    [ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors|Format-List
    throw "Patched Wave 2C.4 orchestrator failed parser validation; original restored."
}

Write-Host "PASS: Wave 2C.4 qualification-gate hotfix applied." -ForegroundColor Green
Write-Host "Backup: $backup"
