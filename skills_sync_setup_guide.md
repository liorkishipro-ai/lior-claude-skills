# Skills & documents sync — setup guide

How skills and code get onto every machine you work from, via Git, while Google Drive stays
strictly for reference documents.

**If you are standing at a brand-new machine, go to the Quickstart and stop reading.** Everything
after it is background and troubleshooting.

## Facts this guide assumes

| | Value |
|---|---|
| Repo | `https://github.com/liorkishipro-ai/lior-claude-skills.git` |
| GitHub account | `liorkishipro-ai`, HTTPS (not SSH) |
| Clone location | `~/lior-claude-skills` |
| Skills load from | `~/.claude/skills` (symlinks/junctions into the clone) |
| Authoritative scripts | `install-skills.sh` (mac/linux), `install-skills.ps1` (windows) — in the repo root |
| Prerequisites | `git`; `gh` for painless auth; Node.js/`npx` only if you want third-party skills |

The install scripts are **not reproduced in this document**. They live in the repo and are the
single source of truth — a pasted copy here would drift out of date and mislead you. Read them
with `cat ~/lior-claude-skills/install-skills.sh`.

---

## The core rule

Two tracks, never mixed:

- **Git (GitHub)** — anything Claude Code needs to load: skills, the karaoke script, any code.
  Versioned, branchable, merge-safe.
- **Google Drive** — anything a human reads directly: papers, decks, notes. Never nested inside
  the git repo folder, and Drive never syncs `.claude/skills`.

A third source sits alongside these: third-party skill packages (like
`julianoczkowski/designer-skills`), installed via the community `skills` CLI rather than vendored
into your own repo. See Phase 5.

---

## Quickstart — a brand-new machine

**Mac / Linux:**

```bash
gh auth login                                    # HTTPS, GitHub.com, your browser
git clone https://github.com/liorkishipro-ai/lior-claude-skills.git ~/lior-claude-skills
cd ~/lior-claude-skills
./install-skills.sh
```

**Windows (PowerShell):**

```powershell
gh auth login
git clone https://github.com/liorkishipro-ai/lior-claude-skills.git $HOME\lior-claude-skills
cd $HOME\lior-claude-skills
powershell -ExecutionPolicy Bypass -File install-skills.ps1
```

Cloning first looks redundant — the script clones too — but it is how you get the script onto a
machine that does not have it yet, and re-running it over an existing clone is harmless (it just
pulls). No copying files between machines, no editing config lines.

**Expected output**, one `OK`/`Linking` line per skill:

```
[install-skills] Updating existing clone at /Users/you/lior-claude-skills
Already up to date.
[install-skills] Linking git-commit-workflow
[install-skills] Linking graphing-guide
...
[install-skills] Done. Active skills in /Users/you/.claude/skills:
```

Confirm:

```bash
ls -la ~/.claude/skills
```

Personal skills appear as **symlinks** (mac/linux) or **junctions** (windows) pointing back into
the clone. Third-party skills appear as **plain folders**, managed separately by the `skills` CLI.

> `install-skills.ps1` has not yet been executed on a real Windows machine. The first lab PC is
> its first true test — expect to debug it, and fix it in the repo rather than locally.

---

## Phase 1 — Create the repo (once, already done)

1. On GitHub, create the repo.
2. Structure it one folder per skill, each with its own `SKILL.md`:
   ```
   lior-claude-skills/
     git-commit-workflow/SKILL.md
     graphing-guide/SKILL.md
     pipeline-validation/SKILL.md
     psychopy-experiments/SKILL.md
     install-skills.sh
     install-skills.ps1
     skills_sync_setup_guide.md
   ```
3. **Commit and push before running the installer anywhere.** This step is not optional and not
   cosmetic:

   ```bash
   cd ~/lior-claude-skills
   git add -A
   git commit -m "Add personal skills"
   git push -u origin main
   ```

   The installer's first action is `git pull`. Against an empty GitHub repo there is no `main`
   branch to fetch, so it aborts with *"Your configuration specifies to merge with the ref
   'refs/heads/main' from the remote, but no such ref was fetched."* That is not a broken
   installer — it is an empty warehouse. See Troubleshooting.

4. Verify the push actually landed:
   ```bash
   git ls-remote --heads origin     # must print a sha and refs/heads/main
   git status -sb                   # must NOT say [gone]
   ```

**The direction of truth:** the repo holds the real skill folders; `~/.claude/skills` holds only
links pointing at them. If you ever find real folders in `~/.claude/skills`, the setup is
backwards — move them into the repo and re-run the installer.

---

## Phase 2 — Where the skills actually live

Editing a skill through `~/.claude/skills/graphing-guide/SKILL.md` does **not** write into
`~/.claude/skills`. The symlink redirects the write to `~/lior-claude-skills/graphing-guide/SKILL.md`
— inside the git repo. That is why you can commit an edit you made "in" the skills folder.

Consequences:

- Edit either path; they are the same file.
- Every edit is already inside a git repo the moment you save it.
- Deleting a link in `~/.claude/skills` never deletes the skill — only the signpost. Re-run the
  installer to restore it.

---

## Phase 3 — Roll out to another machine

- [ ] `git` installed
- [ ] `gh auth login` completed, or HTTPS credentials otherwise cached — this is the single most
      common stall on a fresh machine
- [ ] Node.js / `npx` installed, only if you want third-party skills (Phase 5). The script skips
      that step gracefully if `npx` is missing
- [ ] Run the Quickstart, confirm the skills list
- [ ] If the machine gets reimaged or reset periodically, wire the script into a login hook
      (cron `@reboot`, or Windows Task Scheduler at logon) so it self-heals instead of quietly
      falling behind

---

## Phase 4 — Day-to-day workflow (the cheat sheet)

On whichever machine you are at:

1. **Pull latest** — `git -C ~/lior-claude-skills pull`, or just re-run the install script; it
   does this for you.
2. **Work normally.** Edit a skill's `SKILL.md` in the clone or through the symlink — same file.
3. **Save your work** — `git add`, `git commit`, `git push`. Use the **git-commit-workflow** skill;
   it walks you through branch-or-not, prefix, and message. `push` alone does nothing if you have
   not committed.
4. **Next machine** — `pull`, and the change is already live. No reinstall needed; Claude Code
   reads the linked folder on each session.

---

## Phase 5 — Third-party skill packages (npx skills)

For skill collections you did not write and do not intend to maintain — like
`julianoczkowski/designer-skills` — use the purpose-built `skills` CLI
(https://github.com/vercel-labs/skills) rather than forking the repo into your own. It is
maintained by the original author, supports many coding agents, and gives you a real update path.

**Why not vendor it into `lior-claude-skills`?** You could, but then you own re-syncing every
future update by hand. Consuming it through the CLI keeps that burden with the people already
doing it.

```bash
npx skills add julianoczkowski/designer-skills                              # interactive
npx skills add julianoczkowski/designer-skills --all -a claude-code -g -y    # what the script runs
npx skills add julianoczkowski/designer-skills --skill design-review -a claude-code -g -y
npx skills update                                                            # keep current
```

To add or remove a source, edit the `THIRD_PARTY_SKILLS` array near the top of
`install-skills.sh` (and `$ThirdPartySkills` in the `.ps1`) — `"owner/repo"` for everything in
that repo, `"owner/repo::skill-name"` for one skill. Commenting a line out disables it without
losing the recipe.

**Name collisions:** third-party skills and your own land in the same flat `~/.claude/skills/`
folder, and the script installs third-party **first**. If an upstream package ships a skill named
`graphing-guide`, it becomes a plain folder, and the script then refuses to overwrite it — so
*your* `graphing-guide` silently stops being the active one. After adding a new third-party
source, always confirm your own skills are still symlinks:

```bash
ls -la ~/.claude/skills | grep '\->'
```

---

## Phase 6 — Where Google Drive fits

- Papers, decks, meeting notes, non-code deliverables → Drive, mounted normally via Drive for
  Desktop.
- **Never let Drive sync the git repo folder. Never let Drive sync `.claude/skills`.** Keep them
  as sibling folders on disk, not nested. This single rule prevents the corruption risk this whole
  setup was designed around.
- This guide is the exception that proves the rule: it is a human-readable document, but it lives
  in the *repo*, because you need it on a machine that has no Drive access configured yet.

---

## Quick reference

| | Source of truth | Lives on a machine as | Update mechanism |
|---|---|---|---|
| Personal skills / code | GitHub repo (`lior-claude-skills`) | Symlink/junction in `~/.claude/skills` | `git pull` |
| Third-party skills | Upstream GitHub repo (e.g. `designer-skills`) | Plain folder in `~/.claude/skills` | `npx skills update` |
| claude.ai skills | Same personal GitHub repo | Zip upload | Manual, per update |
| Documents | Google Drive | Synced folder (sibling, not nested) | Automatic Drive sync |

---

## Troubleshooting

**`no such ref was fetched` / `origin/main [gone]`**

```
Your configuration specifies to merge with the ref 'refs/heads/main'
from the remote, but no such ref was fetched.
```

The GitHub repo is empty, or `main` was never pushed. Git was told to merge `origin/main` and
that ref does not exist. Confirm and fix:

```bash
git ls-remote --heads origin     # no output = the remote is genuinely empty
git log --oneline -1             # "does not have any commits yet" = nothing local either
git add -A && git commit -m "Initial commit" && git push -u origin main
```

This is Phase 1 step 3 having been skipped. Nothing is broken or lost.

**`git pull --ff-only` fails some other way** — local changes or a diverged branch on that
machine. Resolve manually (`git status`, then `git stash` or commit) before re-running the
installer.

**"exists and is NOT a symlink"** — a name collision with a third-party skill, or a folder created
outside this system. Rename one of them. See the collision note in Phase 5.

**A personal skill is not showing up** — confirm `SKILL.md` sits directly inside its folder.
Folders without one are skipped (with a log line). Empty folders cannot be committed to git at
all, so a skill that exists only as an empty directory will never reach another machine.

**`npx skills add` fails** — usually no network access on that machine, or Node.js is not
installed. The script logs it and keeps going rather than aborting the whole install.

**Authentication prompts or 403 on push** — HTTPS credentials are not cached. `gh auth login`,
choosing GitHub.com → HTTPS → browser, is the shortest path.
