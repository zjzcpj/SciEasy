# SciEasy Overnight Build Script
# Each phase runs in a fresh Claude Code session (clean context).
# Agent creates one branch per phase, branching off the previous phase.
# You review and merge PRs in order when you wake up.
#
# Usage: .\scripts\overnight-build.ps1
# To start from a specific phase: .\scripts\overnight-build.ps1 -StartFrom 5

param(
    [int]$StartFrom = 3
)

$ErrorActionPreference = 'Stop'
$repo = "C:\Users\jiazh\Desktop\workspace\SciEasy"
Set-Location $repo

# Each phase gets a focused prompt. CLAUDE.md and ROADMAP.md provide the full spec.
$phases = @{
    3 = @"
Read CLAUDE.md and docs/roadmap/ROADMAP.md. Implement Phase 3 (Core data layer).

Do all of 3.1 through 3.6 in a single branch. Steps:
1. git checkout main && git pull origin main
2. git checkout -b phase-3/core-data-layer
3. Implement 3.1 (DataObject + types), commit
4. Implement 3.2 (storage backends), commit
5. Implement 3.3 (ViewProxy), commit
6. Implement 3.4 (lineage), commit
7. Implement 3.5 (broadcast utility), commit
8. Implement 3.6 (tests — make sure they pass), commit
9. Update CHANGELOG.md, commit
10. git push origin phase-3/core-data-layer
11. gh pr create --title "feat: Phase 3 — core data layer" --body "Closes #XX. Implements DataObject types, storage backends, ViewProxy, lineage, and broadcast utility."

Do NOT merge the PR. Just create it and stop.
"@

    4 = @"
Read CLAUDE.md and docs/roadmap/ROADMAP.md. Implement Phase 4 (Block system).

IMPORTANT: Phase 3 branch should exist. Branch off it, not main:
1. git fetch origin
2. git checkout origin/phase-3/core-data-layer
3. git checkout -b phase-4/block-system
4. Implement 4.1 through 4.8, committing after each sub-section
5. Run tests after each sub-section
6. Update CHANGELOG.md, commit
7. git push origin phase-4/block-system
8. gh pr create --title "feat: Phase 4 — block system" --body "Implements port system, block lifecycle, CodeBlock, AppBlock, registry, and format adapters." --base phase-3/core-data-layer

Do NOT merge. Just create PR and stop.
"@

    5 = @"
Read CLAUDE.md and docs/roadmap/ROADMAP.md. Implement Phase 5 (Execution engine).

Branch off Phase 4:
1. git fetch origin
2. git checkout origin/phase-4/block-system
3. git checkout -b phase-5/execution-engine
4. Implement 5.1 through 5.7, committing after each
5. Tests must pass
6. Update CHANGELOG.md
7. git push origin phase-5/execution-engine
8. gh pr create --title "feat: Phase 5 — execution engine" --body "Implements DAG scheduler, batch execution, checkpointing, event bus." --base phase-4/block-system

Do NOT merge. Just create PR and stop.
"@

    6 = @"
Read CLAUDE.md and docs/roadmap/ROADMAP.md. Implement Phase 6 (Workflow definition + CLI).

Branch off Phase 5:
1. git fetch origin
2. git checkout origin/phase-5/execution-engine
3. git checkout -b phase-6/workflow-cli
4. Implement 6.1 through 6.3
5. Tests must pass
6. Update CHANGELOG.md
7. git push origin phase-6/workflow-cli
8. gh pr create --title "feat: Phase 6 — workflow definition and CLI" --base phase-5/execution-engine

Do NOT merge. Just create PR and stop.
"@

    7 = @"
Read CLAUDE.md and docs/roadmap/ROADMAP.md. Implement Phase 7 (API layer).

Branch off Phase 6:
1. git fetch origin
2. git checkout origin/phase-6/workflow-cli
3. git checkout -b phase-7/api-layer
4. Implement 7.1 through 7.3
5. Tests must pass
6. Update CHANGELOG.md
7. git push origin phase-7/api-layer
8. gh pr create --title "feat: Phase 7 — API layer" --base phase-6/workflow-cli

Do NOT merge. Just create PR and stop.
"@
}

Write-Host "============================================"
Write-Host "  SciEasy Overnight Build"
Write-Host "  Starting from Phase $StartFrom"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================"
Write-Host ""

foreach ($phaseNum in ($StartFrom..7)) {
    $prompt = $phases[$phaseNum]
    if (-not $prompt) {
        Write-Host "[SKIP] No prompt defined for Phase $phaseNum"
        continue
    }

    Write-Host "[$phaseNum/8] Starting Phase $phaseNum at $(Get-Date -Format 'HH:mm:ss')..."

    # Write prompt to temp file to avoid stdin/pipe issues
    $tmpFile = [System.IO.Path]::GetTempFileName()
    Set-Content -Path $tmpFile -Value $prompt -Encoding UTF8

    # Run Claude Code: -p = print mode (no interactive UI), read prompt from file
    Get-Content $tmpFile -Raw | claude -p --dangerously-skip-permissions

    $exitCode = $LASTEXITCODE
    Remove-Item $tmpFile -ErrorAction SilentlyContinue
    if ($exitCode -ne 0) {
        Write-Host "[FAIL] Phase $phaseNum exited with code $exitCode. Stopping."
        Write-Host "  Review the output above, fix issues, then restart:"
        Write-Host "  .\scripts\overnight-build.ps1 -StartFrom $phaseNum"
        exit $exitCode
    }

    Write-Host "[DONE] Phase $phaseNum completed at $(Get-Date -Format 'HH:mm:ss')"
    Write-Host ""
}

Write-Host "============================================"
Write-Host "  All phases complete!"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "  Next: review and merge PRs in order:"
Write-Host "    Phase 3 -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 7"
Write-Host "  Phase 8 (frontend) skipped — requires manual supervision."
Write-Host "============================================"
