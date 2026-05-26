param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [string]$QueueFile = "",
  [int]$MaxTurns = 10
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib.ps1") -HermesRoot $HermesRoot -RepoRoot $RepoRoot

if (-not $QueueFile.Trim()) {
  $QueueFile = Join-Path $HermesRoot "queues\rss-monitor-pilots.txt"
}
if (-not (Test-Path -LiteralPath $QueueFile)) {
  throw "Missing queue file: $QueueFile"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$items = Get-Content -LiteralPath $QueueFile | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") }
$payload = ($items -join "`n")
$resolvedRepo = Get-RepoRoot
$agentsPath = Join-Path $resolvedRepo "AGENTS.md"
$statePath = Join-Path $resolvedRepo "PROJECT_STATE.md"
$queuePath = Join-Path $resolvedRepo "TASK_QUEUE.md"
$registryPath = Join-Path $resolvedRepo "config\sources.yaml"
$policyPath = Join-Path $resolvedRepo "docs\SOURCES_POLICY.md"
$registryReportPath = Join-Path $resolvedRepo "docs\reports\source-registry-2026-05-24.md"
$sourcesDir = Join-Path $resolvedRepo "src\official_sources\sources"
$bocylDir = Join-Path $sourcesDir "bocyl"
$boeDir = Join-Path $sourcesDir "boe"
$preflight = @"
Host preflight before Hermes:
- repo_root: $resolvedRepo
- container_repo_mount: /repo
- AGENTS.md_exists: $(Test-Path -LiteralPath $agentsPath)
- PROJECT_STATE.md_exists: $(Test-Path -LiteralPath $statePath)
- TASK_QUEUE.md_exists: $(Test-Path -LiteralPath $queuePath)
- config_sources_exists: $(Test-Path -LiteralPath $registryPath)
- sources_policy_exists: $(Test-Path -LiteralPath $policyPath)
- source_registry_report_exists: $(Test-Path -LiteralPath $registryReportPath)
- source_adapters_dir_exists: $(Test-Path -LiteralPath $sourcesDir)
- bocyl_adapter_dir_exists: $(Test-Path -LiteralPath $bocylDir)
- boe_adapter_dir_exists: $(Test-Path -LiteralPath $boeDir)
"@

$query = @"
Prepara el preflight de TASK-SOURCE-RSS-MONITOR-001.

Cola:
$payload

El siguiente preflight fue calculado por el host antes de lanzar Hermes. Tratalo como evidencia
de ruta para evitar falsos UNKNOWN por buscar en /opt o /opt/data:

$preflight

Usa estas rutas canonicas dentro del contenedor:
- /repo/AGENTS.md
- /repo/PROJECT_STATE.md
- /repo/TASK_QUEUE.md
- /repo/config/sources.yaml
- /repo/docs/SOURCES_POLICY.md
- /repo/docs/reports/source-registry-2026-05-24.md
- /repo/src/official_sources/sources
- /repo/src/official_sources/sources/bocyl
- /repo/src/official_sources/sources/boe

No busques adaptadores en /repo/adaptadores ni en /opt/hermes.

Puedes hacer una prueba read-only acotada de endpoint oficial si el repo ya documenta la URL, pero no ejecutes writes.

Salida markdown:
# RSS monitor scout $stamp
## Decision
PASS | WARNING | BLOCKER | UNKNOWN
## BOCYL pilot
## BOE positive control
## Contrato monitor-only
## Datos que NO deben escribirse
## Implementacion minima sugerida
## Pruebas necesarias

No crees candidatos, evidencia, PDFs, DB, VPS ni downstream writes.
"@

$result = Invoke-HermesProfile -Profile "rss-monitor-scout" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/rss-monitor-scout/rss-monitor-$stamp.md" -Body $result.Text -Meta @{
  profile = "rss-monitor-scout"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE RSS monitor scout: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
