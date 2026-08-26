# Clones (or updates) the lior-claude-skills repo and links every skill
# folder into ~/.claude/skills so Claude Code picks them up automatically.
# Uses Junctions rather than Symlinks so this does NOT require admin rights
# or Developer Mode. Safe to re-run any time - on login, after a reboot,
# on a freshly imaged lab PC, whenever.

# ---- Edit these two lines for your setup ----
$RepoUrl   = "https://github.com/liorkishipro-ai/lior-claude-skills.git"
$CloneDir  = Join-Path $HOME "lior-claude-skills"
# ------------------------------------------------

$SkillsDir = Join-Path $HOME ".claude\skills"

function Log($msg) { Write-Host "[install-skills] $msg" }
function Err($msg) { Write-Host "[install-skills] ERROR: $msg" -ForegroundColor Red }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Err "git is not installed. Install it first."
    exit 1
}

if (Test-Path (Join-Path $CloneDir ".git")) {
    Log "Updating existing clone at $CloneDir"
    git -C $CloneDir pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Err "git pull failed - likely local changes or a diverged branch in $CloneDir. Resolve manually, then re-run this script."
        exit 1
    }
} else {
    Log "Cloning $RepoUrl into $CloneDir"
    git clone $RepoUrl $CloneDir
}

New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

# ---- Third-party skill packages, installed via the `skills` CLI ----
# https://github.com/vercel-labs/skills — one entry per line.
# "owner/repo" installs every skill in that repo.
# "owner/repo::skill-name" installs just one skill from a multi-skill repo.
$ThirdPartySkills = @(
    "julianoczkowski/designer-skills"
)
# ----------------------------------------------------------------------

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Err "npx not found - skipping third-party skills. Install Node.js to enable this."
} else {
    foreach ($entry in $ThirdPartySkills) {
        if ($entry -match "::") {
            $parts = $entry -split "::", 2
            $repo = $parts[0]
            $skillName = $parts[1]
            Log "Installing '$skillName' from $repo (npx skills)"
            npx -y skills add $repo --skill $skillName -a claude-code -g -y
            if ($LASTEXITCODE -ne 0) { Err "Failed to install $skillName from $repo - continuing" }
        } else {
            Log "Installing all skills from $entry (npx skills)"
            npx -y skills add $entry --all -a claude-code -g -y
            if ($LASTEXITCODE -ne 0) { Err "Failed to install skills from $entry - continuing" }
        }
    }
}

$expected = @()

Get-ChildItem -Path $CloneDir -Directory | ForEach-Object {
    $skillName = $_.Name
    if ($skillName.StartsWith(".") -or $skillName -in @("dist", "node_modules")) { return }

    $skillMd = Join-Path $_.FullName "SKILL.md"
    if (-not (Test-Path $skillMd)) {
        Log "Skipping $skillName (no SKILL.md found)"
        return
    }

    $script:expected += $skillName
    $target = Join-Path $SkillsDir $skillName

    if (Test-Path $target) {
        $item = Get-Item $target -Force
        if ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink") {
            if ($item.Target -contains $_.FullName) {
                Log "OK: $skillName already linked"
            } else {
                Log "Relinking $skillName (was pointing elsewhere)"
                Remove-Item $target -Force -Recurse
                New-Item -ItemType Junction -Path $target -Target $_.FullName | Out-Null
            }
        } else {
            Err "$target exists and is NOT a junction - leaving it alone (likely a name collision with a third-party skill, or something installed manually). Rename one of them if you want $skillName managed by this script."
        }
    } else {
        Log "Linking $skillName"
        New-Item -ItemType Junction -Path $target -Target $_.FullName | Out-Null
    }
}

# Prune links this script created for skills that were since removed/renamed
Get-ChildItem -Path $SkillsDir -Force | Where-Object {
    $_.LinkType -eq "Junction" -or $_.LinkType -eq "SymbolicLink"
} | ForEach-Object {
    if ($_.Target -like "$CloneDir*" -and $expected -notcontains $_.Name) {
        Log "Removing stale link: $($_.Name) (no longer in repo)"
        Remove-Item $_.FullName -Force -Recurse
    }
}

Log "Done. Active skills in ${SkillsDir}:"
Get-ChildItem -Path $SkillsDir -Name