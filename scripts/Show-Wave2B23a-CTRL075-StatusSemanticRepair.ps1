[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"

Select-String -Path $collector -Pattern `
    'def status', `
    'row_status', `
    'r.get("status")', `
    'st=status(A)', `
    '"status":st', `
    'e["status"]' |
    Select-Object LineNumber,Line |
    Format-Table -Wrap -AutoSize
