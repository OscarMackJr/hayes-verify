[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"

$runner = Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $runner)){
    throw "Runner not found: $runner"
}

$text = Get-Content $runner -Raw

$checks = [ordered]@{
    HasEMSPathParameter =
        $text.Contains('$EMSPath')

    HasPass45Parameter =
        $text.Contains('[string]$Pass45')

    HasPass45Default =
        $text.Contains('C:\temp\standars\Pass4_5')

    UsesPass45Fallback =
        $text.Contains('(Join-Path $Pass45 "generated\policy-review\effective_compliance_postpolicy.csv")')

    HasMaterializedBaselinePath =
        $text.Contains('releases\wave1-input')
}

$rows = $checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{
        Check = $_.Key
        Pass  = [bool]$_.Value
    }
}

$rows | Format-Table -AutoSize

$failed = @($rows | Where-Object { -not $_.Pass })
if($failed.Count -gt 0){
    throw "Wave 2B.1 Pass45 parameter validation failed."
}

Write-Host "PASS: Wave 2B.1 runner has a valid Pass45 fallback parameter." -ForegroundColor Green
