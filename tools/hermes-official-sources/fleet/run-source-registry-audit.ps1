param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [int]$MaxTurns = 10
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib.ps1") -HermesRoot $HermesRoot -RepoRoot $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$resolvedRepo = Get-RepoRoot
$registryPath = Join-Path $resolvedRepo "config\sources.yaml"
$sourcesDir = Join-Path $resolvedRepo "src\official_sources\sources"
$testsPath = Join-Path $resolvedRepo "tests\test_source_registry.py"
$reportPath = Join-Path $resolvedRepo "docs\reports\source-registry-2026-05-24.md"
$policyPath = Join-Path $resolvedRepo "docs\SOURCES_POLICY.md"
$adapterDirs = if (Test-Path -LiteralPath $sourcesDir) {
  (Get-ChildItem -LiteralPath $sourcesDir -Directory |
    Where-Object { $_.Name -ne "__pycache__" } |
    Select-Object -ExpandProperty Name) -join ", "
} else {
  "MISSING"
}
$adapterFileMatrix = if (Test-Path -LiteralPath $sourcesDir) {
  (Get-ChildItem -LiteralPath $sourcesDir -Directory |
    Where-Object { $_.Name -ne "__pycache__" } |
    Sort-Object Name |
    ForEach-Object {
      $files = Get-ChildItem -LiteralPath $_.FullName -File -Filter "*.py" |
        Where-Object { $_.Name -ne "__init__.py" } |
        Sort-Object Name |
        Select-Object -ExpandProperty Name
      "$($_.Name)=[$($files -join ',')]"
    }) -join "; "
} else {
  "MISSING"
}
$sourceCount = if (Test-Path -LiteralPath $registryPath) {
  (Select-String -Path $registryPath -Pattern '^\s*-\s+source_code:' | Measure-Object).Count
} else {
  0
}
$preflight = @"
Host preflight before Hermes:
- repo_root: $resolvedRepo
- container_repo_mount: /repo
- registry_exists: $(Test-Path -LiteralPath $registryPath)
- source_code_count_from_host: $sourceCount
- source_adapters_dir_exists: $(Test-Path -LiteralPath $sourcesDir)
- source_adapters_dir_container_path: /repo/src/official_sources/sources
- source_adapters_seen: $adapterDirs
- adapter_py_files_from_host: $adapterFileMatrix
- registry_tests_exist: $(Test-Path -LiteralPath $testsPath)
- registry_report_exists: $(Test-Path -LiteralPath $reportPath)
- sources_policy_exists: $(Test-Path -LiteralPath $policyPath)
"@

$query = @"
Audita /repo/config/sources.yaml contra el codigo y docs del repo.

El siguiente preflight fue calculado por el host antes de lanzar Hermes. Tratalo como evidencia
de ruta para evitar falsos UNKNOWN por buscar en /opt o /opt/data:

$preflight

Rutas canonicas dentro del contenedor:
- Registro: /repo/config/sources.yaml
- Adaptadores reales: /repo/src/official_sources/sources
- Tests del registro: /repo/tests/test_source_registry.py
- Informe del registro: /repo/docs/reports/source-registry-2026-05-24.md
- Politica de fuentes: /repo/docs/SOURCES_POLICY.md

No busques adaptadores en /repo/adaptadores ni en /opt/hermes.
No declares que un adaptador es stub si el preflight enumera client.py, parser.py,
ingestion.py, artifacts.py u otros archivos .py reales para esa fuente.

Comprueba:
- source codes duplicados o ambiguos.
- operational_status vs adaptadores reales en /repo/src/official_sources/sources.
- monitor_support vs access_methods.
- evidence_adapter vs downloader/test/doc existente.
- candidate_creation_allowed y evidence_grade_allowed.
- coherencia con /repo/tests/test_source_registry.py y /repo/docs/reports/source-registry-2026-05-24.md.

Salida markdown:
# Source registry audit $stamp
## Decision
PASS | WARNING | BLOCKER | UNKNOWN
## Hallazgos
## Fuentes que requieren investigacion
## No promover todavia
## Tareas pequenas para Codex/OpenCode
## Validaciones sugeridas

No modifiques archivos. No propongas evidence-grade por simple presencia de URL.
"@

$result = Invoke-HermesProfile -Profile "source-registry-auditor" -Query $query -MaxTurns $MaxTurns
$status = if ($result.ExitCode -eq 0) { "OK" } else { "ERROR" }
$outPath = Write-HermesReport -RelativePath "reports/source-registry-audit/source-registry-$stamp.md" -Body $result.Text -Meta @{
  profile = "source-registry-auditor"
  status = $status
  session_id = $result.SessionId
}
Write-Host "DONE source registry audit: $outPath"
if ($result.ExitCode -ne 0) { exit $result.ExitCode }
