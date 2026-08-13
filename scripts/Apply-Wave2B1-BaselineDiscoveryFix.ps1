[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$Pass45 = "C:\temp\standars\Pass4_5"
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $runner)){
    throw "Wave 2B.1 runner not found: $runner"
}

Copy-Item $runner "$runner.pre-baseline-discovery-fix.bak" -Force
$text = Get-Content $runner -Raw

$old = @'
# Prefer final Wave 1 post-policy compliance.
$candidates=@(
    (Join-Path $EMSPath "releases\Pass4_5_Wave1_Baseline\generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\collector-acceptance\effective_compliance.csv")
)
$baseline=$candidates|Where-Object{Test-Path $_}|Select-Object -First 1
if(-not $baseline){throw "Wave 1 compliance baseline not found."}
'@

$new = @'
# Discover/materialize the frozen Wave 1 effective compliance input.
$materializedDir = Join-Path $EMSPath "releases\wave1-input"
New-Item -ItemType Directory -Path $materializedDir -Force | Out-Null
$materialized = Join-Path $materializedDir "effective_compliance_postpolicy.csv"

$candidates=@(
    $materialized,
    (Join-Path $EMSPath "releases\Pass4_5_Wave1_Baseline\generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "release\Pass4_5_Wave1_Baseline\generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\collector-acceptance\effective_compliance.csv"),
    (Join-Path $Pass45 "generated\policy-review\effective_compliance_postpolicy.csv")
)

$baseline=$candidates|Where-Object{Test-Path $_}|Select-Object -First 1

if(-not $baseline){
    $found = Get-ChildItem -Path $EMSPath -Recurse -File -Filter "effective_compliance_postpolicy.csv" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if($found){
        $baseline=$found.FullName
    }
}

if(-not $baseline){
    $zipCandidates = @(Get-ChildItem -Path $EMSPath -Recurse -File -Filter "*Wave1*Baseline*.zip" -ErrorAction SilentlyContinue)
    if($zipCandidates.Count -eq 0 -and (Test-Path $Pass45)){
        $zipCandidates = @(Get-ChildItem -Path $Pass45 -Recurse -File -Filter "*Wave1*Baseline*.zip" -ErrorAction SilentlyContinue)
    }

    foreach($zip in $zipCandidates){
        Write-Host "Inspecting Wave 1 baseline ZIP: $($zip.FullName)" -ForegroundColor Yellow
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $archive=[System.IO.Compression.ZipFile]::OpenRead($zip.FullName)
        try {
            $entry=$archive.Entries |
                Where-Object { $_.FullName -match 'effective_compliance_postpolicy\.csv$' } |
                Select-Object -First 1

            if($entry){
                $reader=New-Object System.IO.StreamReader($entry.Open())
                try {
                    [System.IO.File]::WriteAllText(
                        $materialized,
                        $reader.ReadToEnd(),
                        [System.Text.UTF8Encoding]::new($false)
                    )
                }
                finally {
                    $reader.Dispose()
                }

                $baseline=$materialized
                Write-Host "Materialized frozen Wave 1 compliance input:" -ForegroundColor Green
                Write-Host "  $baseline"
                break
            }
        }
        finally {
            $archive.Dispose()
        }
    }
}

if(-not $baseline){
    throw "Wave 1 compliance baseline not found in EMS repo, Pass4_5, or frozen Wave 1 ZIP."
}

if([System.IO.Path]::GetFullPath($baseline) -ine [System.IO.Path]::GetFullPath($materialized)){
    Copy-Item $baseline $materialized -Force
    $baseline=$materialized
}

Write-Host "Using Wave 1 compliance baseline:" -ForegroundColor Green
Write-Host "  $baseline"
'@

if(-not $text.Contains($old)){
    throw "Expected baseline discovery block not found. No changes applied."
}

$text=$text.Replace($old,$new)
Set-Content $runner $text -Encoding UTF8

Write-Host "Wave 2B.1 baseline discovery patched." -ForegroundColor Green
Write-Host "Backup:"
Write-Host "  $runner.pre-baseline-discovery-fix.bak"
