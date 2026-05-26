param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [int]$MaxTurns = 8
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib.ps1") -HermesRoot $HermesRoot -RepoRoot $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$files = @()
foreach ($subdir in @("structure-audit", "source-registry-audit", "rss-monitor-scout", "policy-review")) {
  $latest = Get-LatestHermesReports -Subdirs @($subdir) -Limit 10 |
    Where-Object { Select-String -Path $_.FullName -Pattern '^status:\s+OK\s*$' -Quiet } |
    Select-Object -First 1
  if ($latest) { $files += $latest }
}
$extracts = New-Object System.Collections.Generic.List[string]
foreach ($file in $files) {
  $matches = Select-String -Path $file.FullName -Pattern '^#|^##|Decision|PASS|WARNING|BLOCKER|UNKNOWN|TASK-|BOCYL|BOE|candidate|evidence|PDF|downstream|VPS|Validacion|Bloqueos' -CaseSensitive:$false | Select-Object -First 24
  $lines = $matches |
    ForEach-Object { $_.Line.TrimStart("+", " ") } |
    Where-Object { $_ -notmatch '<tool_call|</|docker\.exe|^\s*\[?\{|\berror:\s+unrecognized arguments' }
  $text = ($lines -join "`n")
  if ($text.Length -gt 420) { $text = $text.Substring(0, 420) }
  $extracts.Add("## $($file.Name)`n$text")
}
$payload = ($extracts -join "`n`n")

$query = @"
Consolida estos informes Hermes en un resumen operativo para Codex/humano.

Contexto fijo:
- El repositorio official-sources esta montado en /repo.
- Los informes Hermes se generan fuera del repo y se pasan aqui como extractos.
- No declares que el repositorio no existe si no has inspeccionado /repo.

Extractos de informes:
$payload

Salida markdown:
# Official-sources Hermes daily summary $stamp
## Decision
READY_FOR_CODEX_REVIEW | NEEDS_HUMAN_DECISION | BLOCKED | UNKNOWN
## Resumen
## Hallazgos accionables
## Siguiente tarea pequena recomendada
## Validacion requerida
## Bloqueos y UNKNOWN

No declares nada implementado si solo fue propuesto. No ocultes bloqueos.
"@

$result = Invoke-HermesProfile -Profile "writer" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/daily-summary/summary-$stamp.md" -Body $result.Text -Meta @{
  profile = "writer"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE writer summary: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
