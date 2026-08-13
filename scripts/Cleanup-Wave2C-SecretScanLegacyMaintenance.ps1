[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "SECRET-SCAN CLEANUP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path

$obsolete=@(
    "scripts/Test-EMSValidateSecretScanSelfMatchFix.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch-v3.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch-v2.ps1",
    "scripts/Patch-EMSValidateSecretScanMaintenanceSource-v5.ps1",
    "scripts/Patch-EMSValidateSecretScanSelfMatch.ps1",
    "scripts/Test-EMSValidateSecretScanSelfMatchFix-v3.ps1",
    "scripts/Patch-EMSValidateSecretScanFalsePositives-v4.ps1",
    "scripts/Test-EMSValidateSecretScanSelfMatchFix-v2.ps1",
    "scripts/Patch-EMSValidateSecretScanMaintenanceSource-v6.ps1"
)

$durable=@(
    "scripts/Test-EMSSecretScanRepository-v7.ps1",
    "scripts/Cleanup-EMSSecretScanTransientScripts-v7.ps1",
    "scripts/Stage-EMSSecretScanCleanup-v7.ps1"
)

foreach($p in $durable){
    if(-not(Test-Path (Join-Path $root $p))){
        Write-Host "WARNING: durable scanner artifact not present: $p" -ForegroundColor Yellow
    }
}

Write-Host "=== Remove obsolete secret-scan maintenance sources ===" -ForegroundColor Cyan
$removed=@()
foreach($rel in $obsolete){
    $full=Join-Path $root $rel
    if(Test-Path $full){
        Remove-Item $full -Force
        $removed += $rel
        Write-Host "Removed $rel"
    }
}

if($removed.Count -eq 0){
    Write-Host "No obsolete maintenance files were present." -ForegroundColor Yellow
}

Write-Host "`n=== Stage deletions ===" -ForegroundColor Cyan
foreach($rel in $removed){
    git -C $root add -A -- $rel
    if($LASTEXITCODE){Fail "Failed to stage deletion: $rel"}
}

Write-Host "`n=== Windows-native secret-pattern preflight ===" -ForegroundColor Cyan
$pattern='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|(AZURE_CLIENT_SECRET|AWS_SECRET_ACCESS_KEY)\s*=)'
$hits=@()

Get-ChildItem $root -Recurse -File -Force |
    Where-Object {
        $_.FullName -notmatch '\\.git\\' -and
        $_.FullName -notmatch '\\.venv\\' -and
        $_.Extension -ne ".md"
    } |
    ForEach-Object {
        $file=$_
        $lineNo=0
        Get-Content $file.FullName -ErrorAction SilentlyContinue | ForEach-Object {
            $lineNo++
            if($_ -match $pattern){
                $hits += [pscustomobject]@{
                    File=$file.FullName.Substring($root.Length+1)
                    Line=$lineNo
                    Text=$_
                }
            }
        }
    }

if($hits.Count -gt 0){
    $hits | Format-Table -Wrap -AutoSize
    Fail "Secret-pattern preflight still found $($hits.Count) candidate match(es)."
}

Write-Host "PASS: repository preflight found no secret-pattern candidates." -ForegroundColor Green

Write-Host "`n=== Staged cleanup ===" -ForegroundColor Cyan
git -C $root diff --cached --name-status

Write-Host "`nPASS: legacy secret-scan maintenance cleanup staged." -ForegroundColor Green
