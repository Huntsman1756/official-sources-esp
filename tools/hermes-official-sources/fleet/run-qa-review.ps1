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
  $matches = Select-String -Path $file.FullName -Pattern '^#|^##|PASS|WARNING|BLOCKER|UNKNOWN|TASK-|BOCYL|BOE|candidate|evidence|PDF|downstream|VPS|write' -CaseSensitive:$false | Select-Object -First 28
  $lines = $matches |
    ForEach-Object { $_.Line.TrimStart("+", " ") } |
    Where-Object { $_ -notmatch '<tool_call|</|docker\.exe|^\s*\[?\{|\berror:\s+unrecognized arguments' }
  $text = ($lines -join "`n")
  if ($text.Length -gt 600) { $text = $text.Substring(0, 600) }
  $extracts.Add("## $($file.Name)`n$text")
}
$payload = ($extracts -join "`n`n")

$query = @"
Actua como QA reviewer de informes Hermes official-sources.

Contexto fijo:
- El repositorio official-sources esta montado en /repo.
- AGENTS.md, PROJECT_STATE.md y TASK_QUEUE.md viven en /repo.
- Los docs viven bajo /repo/docs.
- config/sources.yaml vive bajo /repo/config/sources.yaml.
- No declares un archivo inexistente sin comprobar su ruta esperada bajo /repo.

Extractos de informes:
$payload

Evalua:
- Overclaiming o conclusiones sin evidencia.
- Violaciones de AGENTS.md/PROJECT_STATE.md/TASK_QUEUE.md.
- Mezcla indebida entre monitor, candidates, evidence, PDFs y downstream.
- Recomendaciones que deberian ser UNKNOWN.

Salida markdown:
# QA review $stamp
## Decision
PASS | WARNING | BLOCKER | UNKNOWN
## Hallazgos
## Informes que requieren revision humana
## Bloqueos
## Recomendacion para Codex
"@

$result = Invoke-HermesProfile -Profile "qa-reviewer" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/qa-review/qa-$stamp.md" -Body $result.Text -Meta @{
  profile = "qa-reviewer"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE QA review: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
