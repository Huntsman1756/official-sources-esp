param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [int]$MaxTurns = 8
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib.ps1") -HermesRoot $HermesRoot -RepoRoot $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$query = @"
Revisa los limites operativos de official-sources para una flota Hermes local.

Lee:
- /repo/AGENTS.md
- /repo/PROJECT_STATE.md
- /repo/TASK_QUEUE.md
- /repo/docs/SOURCES_POLICY.md
- /repo/docs/ARCHITECTURE.md
- /repo/docs/DOWNSTREAM_CONTRACT.md si existe
- /repo/docs/reports/NEXT_OPERATIONS_SYNTHESIS_2026-05-24.md si existe

Salida markdown:
# Evidence and boundary policy review $stamp
## Decision
PASS | WARNING | BLOCKER | UNKNOWN
## Politicas no negociables
## Operaciones permitidas para Hermes
## Operaciones bloqueadas para Hermes
## Riesgos de scope creep
## Stop conditions

Marca BLOCKER si detectas que la flota deberia escribir candidatos/evidencia/PDF/downstream/VPS.
"@

$result = Invoke-HermesProfile -Profile "evidence-policy-reviewer" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/policy-review/policy-$stamp.md" -Body $result.Text -Meta @{
  profile = "evidence-policy-reviewer"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE policy review: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
