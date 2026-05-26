param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [int]$MaxParallel = 3,
  [int]$DelaySeconds = 12,
  [switch]$Sequential,
  [switch]$SkipStructure,
  [switch]$SkipSourceRegistry,
  [switch]$SkipRssScout,
  [switch]$SkipPolicy,
  [switch]$SkipQa,
  [switch]$SkipWriter
)

$ErrorActionPreference = "Stop"

if ($MaxParallel -lt 1 -or $MaxParallel -gt 4) {
  throw "MaxParallel must be between 1 and 4. Recommended: 3 while esdata Hermes is also running."
}

if (-not $RepoRoot.Trim()) {
  $RepoRoot = (git rev-parse --show-toplevel).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
    throw "Run this script inside official-sources or pass -RepoRoot."
  }
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

$scriptDir = $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $HermesRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$runLog = Join-Path $logDir "run-$stamp.log"

function Invoke-Step {
  param([string]$Name, [string]$ScriptName)
  $start = Get-Date
  "[$($start.ToString('o'))] START $Name" | Tee-Object -FilePath $runLog -Append | Out-Null
  $argsList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $scriptDir $ScriptName), "-HermesRoot", $HermesRoot)
  if ($RepoRoot.Trim()) { $argsList += @("-RepoRoot", $RepoRoot) }
  & powershell @argsList 2>&1 | Tee-Object -FilePath $runLog -Append | Out-Null
  $exitCode = $LASTEXITCODE
  $end = Get-Date
  if ($exitCode -eq 0) {
    "[$($end.ToString('o'))] OK $Name elapsed=$([int]($end-$start).TotalSeconds)s" | Tee-Object -FilePath $runLog -Append | Out-Null
  }
  else {
    "[$($end.ToString('o'))] ERROR $Name exit=$exitCode elapsed=$([int]($end-$start).TotalSeconds)s" | Tee-Object -FilePath $runLog -Append | Out-Null
  }
  return [int]$exitCode
}

$scoutSteps = @()
if (-not $SkipStructure) { $scoutSteps += @{ Name = "structure-audit"; Script = "run-structure-audit.ps1" } }
if (-not $SkipSourceRegistry) { $scoutSteps += @{ Name = "source-registry-audit"; Script = "run-source-registry-audit.ps1" } }
if (-not $SkipRssScout) { $scoutSteps += @{ Name = "rss-monitor-scout"; Script = "run-rss-monitor-scout.ps1" } }
if (-not $SkipPolicy) { $scoutSteps += @{ Name = "policy-review"; Script = "run-policy-review.ps1" } }

$failures = 0

if ($Sequential -or $MaxParallel -eq 1) {
  foreach ($step in $scoutSteps) {
    $failures += [int]((Invoke-Step -Name $step.Name -ScriptName $step.Script) -ne 0)
    if ($DelaySeconds -gt 0) { Start-Sleep -Seconds $DelaySeconds }
  }
}
else {
  $running = @()
  foreach ($step in $scoutSteps) {
    while (($running | Where-Object { $_.State -eq "Running" }).Count -ge $MaxParallel) {
      Start-Sleep -Seconds 2
      $completed = $running | Where-Object { $_.State -ne "Running" }
      foreach ($job in $completed) {
        Receive-Job $job -ErrorAction Continue | Tee-Object -FilePath $runLog -Append
        if ($job.State -ne "Completed") { $failures++ }
        Remove-Job $job
      }
      $running = $running | Where-Object { $_.State -eq "Running" }
    }

    $job = Start-Job -Name $step.Name -ScriptBlock {
      param($scriptDir, $scriptName, $name, $hermesRoot, $repoRoot)
      $argsList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $scriptDir $scriptName), "-HermesRoot", $hermesRoot)
      if ($repoRoot.Trim()) { $argsList += @("-RepoRoot", $repoRoot) }
      "START $name"
      & powershell @argsList
      $exitCode = $LASTEXITCODE
      "END $name exit=$exitCode"
      if ($exitCode -ne 0) { throw "$name failed with exit $exitCode" }
    } -ArgumentList $scriptDir, $step.Script, $step.Name, $HermesRoot, $RepoRoot
    $running += $job
    if ($DelaySeconds -gt 0) { Start-Sleep -Seconds $DelaySeconds }
  }

  while ($running.Count -gt 0) {
    Wait-Job -Job $running -Any | Out-Null
    $completed = $running | Where-Object { $_.State -ne "Running" }
    foreach ($job in $completed) {
      Receive-Job $job -ErrorAction Continue | Tee-Object -FilePath $runLog -Append
      if ($job.State -ne "Completed") { $failures++ }
      Remove-Job $job
    }
    $running = $running | Where-Object { $_.State -eq "Running" }
  }
}

if (-not $SkipQa) {
  $failures += [int]((Invoke-Step -Name "qa-review" -ScriptName "run-qa-review.ps1") -ne 0)
}
if (-not $SkipWriter) {
  $failures += [int]((Invoke-Step -Name "writer-summary" -ScriptName "run-writer-summary.ps1") -ne 0)
}

Write-Host "DONE Hermes official-sources run log: $runLog"
if ($failures -gt 0) {
  throw "$failures Hermes step(s) failed. Inspect $runLog."
}
