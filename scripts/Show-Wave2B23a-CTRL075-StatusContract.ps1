[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
Write-Host "Relevant status lines:" -ForegroundColor Cyan
Select-String -Path $collector -Pattern 'def status','collector_status','status(A)' |
    Select-Object LineNumber,Line |
    Format-Table -Wrap -AutoSize
