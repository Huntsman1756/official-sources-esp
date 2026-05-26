param(
    [Parameter(Mandatory = $true)]
    [string]$Task,

    [string]$Model = $env:OPENCODE_MODEL,

    [string]$Agent = "build",

    [string]$TestCommand = "",

    [switch]$InPlace,

    [switch]$AllowDirty,

    [string]$WorktreePath = "",

    [string]$BranchName = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Program,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program exited with code $LASTEXITCODE"
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required but was not found on PATH."
}

if (-not (Get-Command opencode -ErrorAction SilentlyContinue)) {
    throw "opencode is required but was not found on PATH."
}

$RepoRoot = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
    throw "This script must be run inside a git repository."
}

$RepoRoot = (Resolve-Path $RepoRoot).Path
$OriginalLocation = (Get-Location).Path
Set-Location $RepoRoot

try {
    $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $AiDir = Join-Path $RepoRoot ".ai"
    $PromptDir = Join-Path $AiDir "prompts"
    $LogDir = Join-Path $AiDir "logs"
    $PatchDir = Join-Path $AiDir "patches"

    New-Item -ItemType Directory -Force -Path $PromptDir, $LogDir, $PatchDir | Out-Null

    $PromptFile = Join-Path $PromptDir "opencode-$Stamp.md"
    $LogFile = Join-Path $LogDir "opencode-$Stamp.log"
    $PatchFile = Join-Path $PatchDir "opencode-$Stamp.patch"

    $StatusBefore = git status --porcelain

    if ($InPlace) {
        if ($StatusBefore -and -not $AllowDirty) {
            Write-Host "Working tree is not clean. Re-run with -AllowDirty or omit -InPlace to use an isolated worktree."
            git status --short
            exit 2
        }

        $TargetRoot = $RepoRoot
        $TargetDescription = "current worktree"
    }
    else {
        $RepoName = Split-Path -Leaf $RepoRoot
        if (-not $WorktreePath.Trim()) {
            $WorktreePath = Join-Path (Split-Path -Parent $RepoRoot) "$RepoName-opencode-$Stamp"
        }
        if (-not $BranchName.Trim()) {
            $BranchName = "codex/opencode-$Stamp"
        }

        $TargetRoot = $WorktreePath
        $TargetDescription = "isolated worktree $TargetRoot on branch $BranchName"

        Invoke-Checked git @("worktree", "add", "-b", $BranchName, $TargetRoot, "HEAD")
    }

    $Prompt = @"
You are OpenCode acting as the implementation worker for this repository.

Codex is the orchestrator and reviewer. Codex will inspect your diff, run validation, and decide whether to accept, amend, or reject the work.

Task:
$Task

Repository rules:
- Read AGENTS.md, PROJECT_STATE.md, TASK_QUEUE.md, and the relevant docs before editing.
- Preserve the official-sources boundary: upstream official-source ingestion and evidence platform only.
- Do not add downstream product writes, alert-to-candidate conversion, notifications, subscriptions, ranking, publication, or product workflow ownership.
- Do not perform VPS, database, deployment, push, or release operations.
- Do not commit.
- Do not edit secrets, .env files, credentials, tokens, or unrelated config.
- Modify only files required for the task.
- Prefer small, reviewable changes.
- Run relevant tests if safe and available.

At the end, summarize:
1. files changed
2. tests run
3. risks or uncertainties
"@

    $Prompt | Set-Content -Encoding UTF8 $PromptFile

    $ArgsList = @(
        "run",
        "--dir", $TargetRoot,
        "--agent", $Agent,
        "--format", "json",
        "--file", $PromptFile
    )

    if ($Model -and $Model.Trim() -ne "") {
        $ArgsList += @("--model", $Model)
    }

    $ArgsList += @("Follow the attached delegation prompt. Do not commit, push, deploy, or edit secrets.")

    Write-Host "Running OpenCode delegation..."
    Write-Host "Repo root: $RepoRoot"
    Write-Host "Target: $TargetDescription"
    Write-Host "Prompt: $PromptFile"
    Write-Host "Log: $LogFile"

    & opencode @ArgsList *>&1 | Tee-Object -FilePath $LogFile
    $OpenCodeExit = $LASTEXITCODE

    Write-Host ""
    Write-Host "Git status after OpenCode:"
    git -C $TargetRoot status --short

    # Include newly created files in the generated patch without staging their contents.
    git -C $TargetRoot add -N -- . 2>$null

    git -C $TargetRoot diff --binary > $PatchFile

    Write-Host ""
    Write-Host "Patch saved to: $PatchFile"

    if ($TestCommand -and $TestCommand.Trim() -ne "") {
        Write-Host ""
        Write-Host "Running tests in target worktree: $TestCommand"
        Push-Location $TargetRoot
        try {
            pwsh -NoProfile -Command $TestCommand
        }
        finally {
            Pop-Location
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Test command exited with code $LASTEXITCODE"
        }
    }

    if ($OpenCodeExit -ne 0) {
        throw "opencode exited with code $OpenCodeExit. Inspect $LogFile and $PatchFile."
    }

    Write-Host ""
    Write-Host "OpenCode delegation finished. Review the target worktree or patch before accepting any change."
    if (-not $InPlace) {
        Write-Host "Target worktree: $TargetRoot"
        Write-Host "Target branch: $BranchName"
    }
}
finally {
    Set-Location $OriginalLocation
}
