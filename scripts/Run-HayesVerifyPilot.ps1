[CmdletBinding()]
param(
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [Parameter(Mandatory=$true)][string]$ControlId,
    [Parameter(Mandatory=$true)][string]$TargetId,
    [Parameter(Mandatory=$true)][string]$RepositoryPath,
    [Parameter(Mandatory=$true)][string]$GitHubRepo
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY PILOT BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$req="$root\examples\pilot_request.json"

$payload=[ordered]@{
  contract_version="1.0"
  wave="2D"
  request_id="PILOT-$ControlId-$TargetId"
  control_id=$ControlId
  target_id=$TargetId
  repository_name=$RepositoryPath
  applicability_state="APPLICABLE"
  requested_at_utc=[DateTimeOffset]::UtcNow.ToString("o")
  control_definition_sha256=("0"*64)
  applicability_matrix_sha256=("0"*64)
  requested_evidence_types=@("GITHUB_CONFIGURATION")
}
$payload|ConvertTo-Json -Depth 10|Set-Content $req -Encoding UTF8

python "$root\scripts\Run-HayesVerifyPilot.py" `
  --root $root `
  --request $req `
  --repository-path $RepositoryPath `
  --github-repo $GitHubRepo

if($LASTEXITCODE){Fail "Pilot execution failed"}

Write-Host "PASS: Hayes Verify pilot execution complete. No evidence promotion performed." -ForegroundColor Green
