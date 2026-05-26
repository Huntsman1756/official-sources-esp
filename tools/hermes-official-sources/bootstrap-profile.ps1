param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [string]$BaseUrl = "https://api.nan.builders/v1",
  [string]$ApiKeyEnv = "HERMES_OFFICIAL_SOURCES_API_KEY",
  [string]$FallbackApiKeyEnv = "",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function ConvertTo-YamlDoubleQuotedValue {
  param([Parameter(Mandatory = $true)][string]$Value)
  return ($Value -replace '\\', '\\' -replace '"', '\"')
}

if (-not $RepoRoot.Trim()) {
  $RepoRoot = (git rev-parse --show-toplevel).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
    throw "Run this script inside the official-sources git repository or pass -RepoRoot."
  }
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TemplateDir = Join-Path $ToolRoot "templates"
$ConfigTemplate = Join-Path $TemplateDir "config.template.yaml"

if (-not (Test-Path -LiteralPath $ConfigTemplate)) {
  throw "Missing config template: $ConfigTemplate"
}

$apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnv, "Process")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnv, "User") }
if ((-not $apiKey) -and $FallbackApiKeyEnv.Trim()) {
  $apiKey = [Environment]::GetEnvironmentVariable($FallbackApiKeyEnv, "Process")
}
if ((-not $apiKey) -and $FallbackApiKeyEnv.Trim()) {
  $apiKey = [Environment]::GetEnvironmentVariable($FallbackApiKeyEnv, "User")
}
if (-not $apiKey) {
  throw "No API key found. Set $ApiKeyEnv, or pass -FallbackApiKeyEnv if this provider should use another env var."
}
if ($BaseUrl -match 'nan\.builders' -and $apiKey -notmatch '^sk-') {
  throw "The configured base URL expects a LiteLLM-style key beginning with sk-. Set $ApiKeyEnv to the correct provider key."
}

$profiles = @(
  @{ Name = "structure-auditor"; Model = "qwen3.6"; Soul = "SOUL.structure-auditor.md" },
  @{ Name = "source-registry-auditor"; Model = "gemma4"; Soul = "SOUL.source-registry-auditor.md" },
  @{ Name = "rss-monitor-scout"; Model = "gemma4"; Soul = "SOUL.rss-monitor-scout.md" },
  @{ Name = "evidence-policy-reviewer"; Model = "qwen3.6"; Soul = "SOUL.evidence-policy-reviewer.md" },
  @{ Name = "qa-reviewer"; Model = "qwen3.6"; Soul = "SOUL.qa-reviewer.md" },
  @{ Name = "writer"; Model = "qwen3.6"; Soul = "SOUL.writer.md" }
)

New-Item -ItemType Directory -Force -Path $HermesRoot | Out-Null
foreach ($dir in @("profiles", "queues", "reports", "logs", "snapshots")) {
  New-Item -ItemType Directory -Force -Path (Join-Path $HermesRoot $dir) | Out-Null
}

$template = Get-Content -Raw -LiteralPath $ConfigTemplate
$escapedBaseUrl = ConvertTo-YamlDoubleQuotedValue $BaseUrl
$escapedApiKey = ConvertTo-YamlDoubleQuotedValue $apiKey

foreach ($profile in $profiles) {
  $profileDir = Join-Path (Join-Path $HermesRoot "profiles") $profile.Name
  New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

  $configPath = Join-Path $profileDir "config.yaml"
  if ((Test-Path -LiteralPath $configPath) -and -not $Force) {
    Write-Host "SKIP existing config: $configPath"
  }
  else {
    $config = $template.Replace("__MODEL__", $profile.Model).
      Replace("__BASE_URL__", $escapedBaseUrl).
      Replace("__API_KEY__", $escapedApiKey)
    [System.IO.File]::WriteAllText($configPath, $config, [System.Text.UTF8Encoding]::new($false))
  }

  $soulSource = Join-Path $TemplateDir $profile.Soul
  $soulTarget = Join-Path $profileDir "SOUL.md"
  Copy-Item -LiteralPath $soulSource -Destination $soulTarget -Force
}

$queueDir = Join-Path $HermesRoot "queues"
$rssQueue = Join-Path $queueDir "rss-monitor-pilots.txt"
if ((-not (Test-Path -LiteralPath $rssQueue)) -or $Force) {
  @(
    "BOCYL|first real monitor pilot; verify official RSS/Atom/API/HTML metadata surface only",
    "BOE|positive control; verify monitor shape without changing BOE evidence policy"
  ) | Set-Content -LiteralPath $rssQueue -Encoding UTF8
}

$policyQueue = Join-Path $queueDir "policy-checks.txt"
if ((-not (Test-Path -LiteralPath $policyQueue)) -or $Force) {
  @(
    "monitor_vs_candidate|monitor output must not create source_candidates",
    "pdf_policy|PDF is never default and remains scoped explicit evidence",
    "downstream_boundary|official-sources must not write product repos",
    "vps_boundary|VPS/DB/deploy require separate explicit task"
  ) | Set-Content -LiteralPath $policyQueue -Encoding UTF8
}

$statePath = Join-Path $HermesRoot "PROJECT_BINDING.txt"
@(
  "repo_root=$RepoRoot",
  "created_at=$(Get-Date -Format o)",
  "concurrency_default=3",
  "concurrency_reason=global limit 5; reserve 1 for existing esdata Hermes run and 1 for manual/headroom",
  "chat_rpm_limit=100",
  "embedding_rpm_limit=60",
  "phase=1-read-only-local-auditor"
) | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host "Hermes official-sources profile prepared at: $HermesRoot"
Write-Host "Repo binding: $RepoRoot"
Write-Host "Profiles: $($profiles.Name -join ', ')"
Write-Host "No secret values were printed."
