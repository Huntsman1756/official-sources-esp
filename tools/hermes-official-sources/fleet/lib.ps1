param(
  [string]$HermesRoot = "$env:USERPROFILE\.hermes-official-sources-auditor",
  [string]$RepoRoot = "",
  [string]$HermesImage = "nousresearch/hermes-agent:latest"
)

$ErrorActionPreference = "Stop"

function ConvertTo-DockerPath {
  param([Parameter(Mandatory = $true)][string]$Path)
  return ((Resolve-Path -LiteralPath $Path).Path -replace '\\', '/')
}

function Get-RepoRoot {
  if ($script:RepoRoot -and $script:RepoRoot.Trim()) {
    return (Resolve-Path -LiteralPath $script:RepoRoot).Path
  }
  $root = (git rev-parse --show-toplevel).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $root) {
    throw "Run inside official-sources or pass -RepoRoot."
  }
  return (Resolve-Path -LiteralPath $root).Path
}

function Invoke-HermesProfile {
  param(
    [Parameter(Mandatory = $true)][string]$Profile,
    [Parameter(Mandatory = $true)][string]$Query,
    [int]$MaxTurns = 12
  )

  $resolvedRoot = (Resolve-Path -LiteralPath $script:HermesRoot).Path
  $profileDir = Join-Path (Join-Path $resolvedRoot "profiles") $Profile
  if (-not (Test-Path -LiteralPath (Join-Path $profileDir "config.yaml"))) {
    throw "Missing profile config. Run tools/hermes-official-sources/bootstrap-profile.ps1 first. Profile: $Profile"
  }

  $repo = Get-RepoRoot
  $dockerProfile = ConvertTo-DockerPath $profileDir
  $reportsDir = Join-Path $resolvedRoot "reports"
  New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
  $dockerReports = ConvertTo-DockerPath $reportsDir
  $dockerRepo = ConvertTo-DockerPath $repo

  $argsList = @(
    "run", "--rm",
    "-v", "${dockerProfile}:/opt/data",
    "-v", "${dockerReports}:/hermes-reports:ro",
    "-v", "${dockerRepo}:/repo:ro",
    $script:HermesImage,
    "chat", "-Q", "--max-turns", [string]$MaxTurns, "-q", $Query
  )

  $previousEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $output = & docker @argsList 2>&1
  $exitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousEap
  $text = (($output | Out-String).Trim())

  return [pscustomobject]@{
    ExitCode = $exitCode
    Text = $text
    SessionId = if ($text -match 'session_id:\s*([0-9A-Za-z_-]+)') { $Matches[1] } else { "" }
  }
}

function Write-HermesReport {
  param(
    [Parameter(Mandatory = $true)][string]$RelativePath,
    [Parameter(Mandatory = $true)][string]$Body,
    [hashtable]$Meta = @{}
  )
  $root = (Resolve-Path -LiteralPath $script:HermesRoot).Path
  $path = Join-Path $root $RelativePath
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  $metaLines = @("<!--", "generated_at: $(Get-Date -Format o)")
  foreach ($key in ($Meta.Keys | Sort-Object)) {
    $metaLines += "${key}: $($Meta[$key])"
  }
  $metaLines += "-->"
  [System.IO.File]::WriteAllText($path, (($metaLines -join "`n") + "`n`n" + $Body + "`n"), [System.Text.UTF8Encoding]::new($false))
  return $path
}

function Get-LatestHermesReports {
  param(
    [string[]]$Subdirs,
    [int]$Limit = 12
  )
  $root = (Resolve-Path -LiteralPath $script:HermesRoot).Path
  $files = @()
  foreach ($subdir in $Subdirs) {
    $dir = Join-Path (Join-Path $root "reports") $subdir
    if (Test-Path -LiteralPath $dir) {
      $files += Get-ChildItem -LiteralPath $dir -Filter "*.md" -File -ErrorAction SilentlyContinue
    }
  }
  return $files | Sort-Object LastWriteTime -Descending | Select-Object -First $Limit
}
