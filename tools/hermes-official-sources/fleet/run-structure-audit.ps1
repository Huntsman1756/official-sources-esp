param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [int]$MaxTurns = 12
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib.ps1") -HermesRoot $HermesRoot -RepoRoot $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$query = @"
Audita la estructura actual de /repo official-sources en modo read-only.

Lee primero:
- /repo/AGENTS.md
- /repo/PROJECT_STATE.md
- /repo/TASK_QUEUE.md
- /repo/README.md
- /repo/docs/ARCHITECTURE.md
- /repo/docs/SOURCES_POLICY.md

Luego inspecciona src/, tests/, config/sources.yaml, tools/ y docs/reports solo lo necesario.

Salida markdown:
# Structure audit $stamp
## Decision
PASS | WARNING | BLOCKER | UNKNOWN
## Mapa real del repo
## Siguiente trabajo permitido
## Riesgos de atasco
## Guardrails que Hermes debe respetar
## Validaciones sugeridas

No modifiques archivos. Si falta prueba, usa UNKNOWN.
"@

$result = Invoke-HermesProfile -Profile "structure-auditor" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/structure-audit/structure-$stamp.md" -Body $result.Text -Meta @{
  profile = "structure-auditor"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE structure audit: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
