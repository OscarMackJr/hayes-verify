[CmdletBinding()]
param([string]$HayesPath = (Split-Path -Parent $PSScriptRoot))
& "$PSScriptRoot\Test-Wave2DEvaluatorRegistryV19PublicationPreflight.ps1" -HayesPath $HayesPath
if ($LASTEXITCODE) { throw "v1.9 publication preflight failed" }
& "$PSScriptRoot\Stage-Wave2DEvaluatorRegistryV19ForPublish.ps1" -HayesPath $HayesPath