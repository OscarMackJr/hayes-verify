[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Run-Wave2C4-AnnualReviewCloseout.ps1"
if(-not(Test-Path $target)){throw "Wave 2C.4 orchestrator not found: $target"}

$backup="$target.pre-wave2c4-resume-hotfix.bak"
Copy-Item $target $backup -Force

$lines=[System.Collections.Generic.List[string]](Get-Content $target)
$joined=$lines -join "`n"

if($joined -match 'Already-promoted closeout resume path'){
    Write-Host "Wave 2C.4 orchestrator already contains resume hotfix." -ForegroundColor Yellow
    exit 0
}

# Insert resume gate immediately after runtime variables are established and before annual-review initialization.
$insertIndex=-1
for($i=0;$i -lt $lines.Count;$i++){
    if($lines[$i] -match 'Write-Host "=== Wave 2C\.4 initialize Annual EMS Review register ==="'){
        $insertIndex=$i
        break
    }
}
if($insertIndex -lt 0){
    Copy-Item $backup $target -Force
    throw "Expected Wave 2C.4 initialization marker not found; original restored."
}

$block=@(
    '',
    '# === Already-promoted closeout resume path ===',
    '$promotionRecordPath=Join-Path $root "generated\wave2c\annual-review-closeout\promotion_record.json"',
    '$authoritativeEvidencePath=Join-Path $root "evidence\ems\EMS-CTRL-080.yaml"',
    '$queuePath=Join-Path $root "generated\wave2c\remediation_queue.csv"',
    '',
    'if((Test-Path $promotionRecordPath) -and (Test-Path $authoritativeEvidencePath) -and (Test-Path $queuePath)){',
    '    $resumePromotion=Get-Content $promotionRecordPath -Raw | ConvertFrom-Json',
    '    $resumeRows=@(Import-Csv $queuePath)',
    '    $resumeCtrl=@($resumeRows | Where-Object {$_.control_id -eq "EMS-CTRL-080"})',
    '    $resumeOpen=@($resumeRows | Where-Object {$_.remediation_state -eq "OPEN"})',
    '',
    '    $alreadyPromoted=(',
    '        $resumePromotion.wave -eq "2C.4" -and',
    '        $resumePromotion.control_id -eq "EMS-CTRL-080" -and',
    '        $resumePromotion.promotion_performed -eq $true -and',
    '        $resumePromotion.pre_open_count -eq 1 -and',
    '        $resumePromotion.post_open_count -eq 0 -and',
    '        $resumeCtrl.Count -eq 1 -and',
    '        $resumeCtrl[0].current_status -eq "PASS" -and',
    '        $resumeCtrl[0].evidence_sufficiency -eq "SUFFICIENT" -and',
    '        $resumeCtrl[0].promotion_status -eq "PROMOTED" -and',
    '        $resumeCtrl[0].remediation_state -eq "CLOSED" -and',
    '        $resumeOpen.Count -eq 0',
    '    )',
    '',
    '    if($alreadyPromoted){',
    '        $actualHash=(Get-FileHash -Algorithm SHA256 $authoritativeEvidencePath).Hash.ToLowerInvariant()',
    '        $expectedHash=([string]$resumePromotion.authoritative_evidence_sha256).ToLowerInvariant()',
    '        if($actualHash -ne $expectedHash){',
    '            Fail "Already-promoted CTRL-080 evidence hash mismatch."',
    '        }',
    '',
    '        Write-Host "=== Wave 2C.4 already-promoted closeout resume ===" -ForegroundColor Cyan',
    '        Write-Host "CTRL-080 promotion already verified; skipping qualification/review/promotion." -ForegroundColor Green',
    '',
    '        Write-Host "`n=== Rerun higher-scope / inheritance evaluation ===" -ForegroundColor Cyan',
    '        $inheritance=Join-Path $root "scripts\Run-Wave2B1-Inheritance.ps1"',
    '        if(-not(Test-Path $inheritance)){Fail "Inheritance runner not found."}',
    '        if(-not(Test-Path $BaselinePath)){Fail "Wave 1 baseline not found: $BaselinePath"}',
    '        & $inheritance -BaselinePath $BaselinePath',
    '        if($LASTEXITCODE){Fail "Inheritance rerun failed."}',
    '',
    '        Write-Host "`n=== Certify Wave 2C closeout ===" -ForegroundColor Cyan',
    '        & $py (Join-Path $root "scripts\Closeout-Wave2C4.py") `',
    '            --root $root `',
    '            --out (Join-Path $close "wave2c_closeout_certification.json")',
    '        if($LASTEXITCODE){Fail "Wave 2C closeout certification failed."}',
    '',
    '        Write-Host "`nPASS: Wave 2C closeout resumed from existing CTRL-080 promotion." -ForegroundColor Green',
    '        exit 0',
    '    }',
    '}',
    ''
)

for($j=$block.Count-1;$j -ge 0;$j--){
    $lines.Insert($insertIndex,$block[$j])
}

Set-Content $target $lines -Encoding UTF8

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,[ref]$tokens,[ref]$errors
)|Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors|Format-List
    throw "Patched Wave 2C.4 orchestrator failed parser validation; original restored."
}

Write-Host "PASS: Wave 2C.4 already-promoted closeout resume hotfix applied." -ForegroundColor Green
Write-Host "Backup: $backup"
