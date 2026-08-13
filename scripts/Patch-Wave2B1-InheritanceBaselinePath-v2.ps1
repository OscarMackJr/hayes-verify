[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"

$target=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $target)){throw "Inheritance runner not found: $target"}

$backup="$target.pre-wave2c2b-baseline-hotfix-v2.bak"
Copy-Item $target $backup -Force

$lines=[System.Collections.Generic.List[string]](Get-Content $target)

# Add BaselinePath parameter if missing.
$joined=$lines -join "`n"
if($joined -notmatch '\$BaselinePath'){
    $paramIndex=-1
    for($i=0;$i -lt $lines.Count;$i++){
        if($lines[$i] -match '^\s*param\s*\('){
            $paramIndex=$i
            break
        }
    }

    if($paramIndex -ge 0){
        $lines.Insert($paramIndex+1,'    [string]$BaselinePath,')
    }
    else{
        $lines.Insert(0,'param([string]$BaselinePath)')
        $lines.Insert(0,'[CmdletBinding()]')
    }
}

# Replace the exact historical failure guard.
$replaced=$false
for($i=0;$i -lt $lines.Count;$i++){
    if($lines[$i].Trim() -eq 'if(-not $baseline){throw "Wave 1 compliance baseline not found."}'){
        $new=@(
            'if($BaselinePath){',
            '    if(-not(Test-Path $BaselinePath)){',
            '        throw "Explicit Wave 1 compliance baseline not found: $BaselinePath"',
            '    }',
            '    $baseline=(Resolve-Path $BaselinePath).Path',
            '}',
            'if(-not $baseline){',
            '    throw "Wave 1 compliance baseline not found. Supply -BaselinePath <path-to-effective_compliance_postpolicy.csv>."',
            '}'
        )

        $lines.RemoveAt($i)
        for($j=$new.Count-1;$j -ge 0;$j--){
            $lines.Insert($i,$new[$j])
        }
        $replaced=$true
        break
    }
}

if(-not $replaced){
    Copy-Item $backup $target -Force
    throw "Expected Wave 1 baseline failure guard not found; original restored."
}

Set-Content $target $lines -Encoding UTF8

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $target,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    Copy-Item $backup $target -Force
    $errors | Format-List
    throw "Patched inheritance runner failed parser validation; original restored."
}

Write-Host "PASS: Run-Wave2B1-Inheritance.ps1 patched for explicit -BaselinePath." -ForegroundColor Green
Write-Host "Backup: $backup"
