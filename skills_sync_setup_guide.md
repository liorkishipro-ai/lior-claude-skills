# Skills & documents sync — setup guide

How Claude Code skills reach every machine you work from, via Git alone, while Google Drive stays
strictly for reference documents.

**Standing at a brand-new machine? Go to the Quickstart and stop reading.** Everything after it is
background and troubleshooting.

## Facts this guide assumes

| | Value |
|---|---|
| Repo | `https://github.com/liorkishipro-ai/lior-claude-skills.git` |
| GitHub account | `liorkishipro-ai`, HTTPS (not SSH) |
| Clone location | `~/lior-claude-skills` |
| Personal skills | repo root — one folder per skill |
| Vendored third-party skills | `vendor/` — see `vendor/vendored_skills_provenance.md` |
| Skills load from | `~/.claude/skills` — **every entry is a symlink into the clone** |
| Authoritative scripts | `install-skills.sh` (mac/linux), `install-skills.ps1` (windows), in the repo root |
| Prerequisites | `git`, plus `gh` for painless auth. **Nothing else** — no Node.js, no npx |

The install scripts are **not reproduced in this document**. They live in the repo and are the
single source of truth; a pasted copy here would drift and mislead you. Read them with
`cat ~/lior-claude-skills/install-skills.sh`.

---

## The core rule

Two tracks, never mixed:

- **Git (GitHub)** — anything Claude Code needs to load: every skill, the karaoke script, any code.
  Versioned, branchable, merge-safe.
- **Google Drive** — anything a human reads directly: papers, decks, notes. Never nested inside the
  git repo folder, and Drive never syncs `.claude/skills`.

There is no third track. Third-party skills used to be installed by the `skills` CLI, which meant
a second mechanism, a Node.js dependency on every machine, and content living in `~/.agents/skills`
outside any repo. They are now vendored into this repo — see Phase 5 for what that costs and why it
is worth it.

---

## Quickstart — a brand-new machine

**Mac / Linux:**

```bash
gh auth login                                    # GitHub.com, HTTPS, via browser
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

Cloning first looks redundant — the script clones too — but it is how the script gets onto a
machine that does not have it yet, and re-running it over an existing clone is harmless. No files
to copy between machines, no config lines to edit.

**Expected output** — one line per skill, then the list:

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

**Every entry should be a symlink whose target is inside the clone.** That is the whole invariant:

```
graphing-guide  -> /Users/you/lior-claude-skills/graphing-guide          # personal
neurokit2       -> /Users/you/lior-claude-skills/vendor/neurokit2        # vendored
```

Anything in `~/.claude/skills` that is *not* such a symlink was put there by something else, and
the installer will refuse to touch it. See Troubleshooting.

> `install-skills.ps1` has not yet been executed on a real Windows machine. The first lab PC is its
> first true test — expect to debug it, and fix it **in the repo** rather than locally.

---

## Phase 1 — Create the repo (once, already done)

1. On GitHub, create the repo.
2. One folder per skill, each with its own `SKILL.md` directly inside:
   ```
   lior-claude-skills/
     git-commit-workflow/SKILL.md
     graphing-guide/SKILL.md
     pipeline-validation/SKILL.md
     psychopy-experiments/SKILL.md
     vendor/
       <16 third-party skills>/SKILL.md
       licenses/
       vendored_skills_provenance.md
     install-skills.sh
     install-skills.ps1
     skills_sync_setup_guide.md
   ```
3. **Commit and push before running the installer anywhere.** Not optional:

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

4. Verify the push landed:
   ```bash
   git ls-remote --heads origin     # must print a sha and refs/heads/main
   git status -sb                   # must NOT say [gone]
   ```

**The direction of truth:** the repo holds the real skill folders; `~/.claude/skills` holds only
links pointing at them. If you ever find a real folder in `~/.claude/skills`, the setup is
backwards for that skill.

---

## Phase 2 — Where the skills actually live

Editing `~/.claude/skills/graphing-guide/SKILL.md` does **not** write into `~/.claude/skills`. The
symlink redirects the write to `~/lior-claude-skills/graphing-guide/SKILL.md`, inside the git repo.
That is why you can commit an edit you made "in" the skills folder.

`pwd -P` collapses symlinks and shows you which directory you are actually standing in. Use it
whenever you are unsure.

Consequences:

- Edit either path; they are the same file.
- Every edit is already inside a git repo the moment you save it — including vendored skills, which
  is the point of vendoring them.
- Deleting a link in `~/.claude/skills` never deletes the skill, only the signpost. Re-run the
  installer to restore it.

---

## Phase 3 — Roll out to another machine

- [ ] `git` installed
- [ ] `gh auth login` completed, or HTTPS credentials otherwise cached — the single most common
      stall on a fresh machine
- [ ] Run the Quickstart, confirm the skills list
- [ ] Confirm every entry in `~/.claude/skills` is a symlink into the clone
- [ ] If the machine gets reimaged or reset periodically, wire the script into a login hook
      (cron `@reboot`, or Windows Task Scheduler at logon) so it self-heals instead of quietly
      falling behind. The script is idempotent — re-running it changes nothing when nothing changed.

No Node.js, no network beyond GitHub. That is deliberate: lab PCs with restricted egress can still
get every skill.

---

## Phase 4 — Day-to-day workflow (the cheat sheet)

On whichever machine you are at:

1. **Pull latest** — `git -C ~/lior-claude-skills pull`, or just re-run the install script; it does
   this for you.
2. **Work normally.** Edit a skill's `SKILL.md` in the clone or through the symlink — same file.
3. **Save your work** — `git add`, `git commit`, `git push`. Use the **git-commit-workflow** skill;
   it walks you through branch-or-not, prefix, and message. `git push` alone does nothing if you
   have not committed.
4. **Next machine** — `pull`, and the change is already live. No reinstall needed; Claude Code reads
   the linked folder each session.

This now applies to vendored third-party skills too. Previously they could not be edited at all.

---

## Phase 5 — Vendored third-party skills

`vendor/` holds 16 skills copied from two upstream repositories at pinned commits:
`julianoczkowski/designer-skills` (Apache-2.0) and `K-Dense-AI/scientific-agent-skills` (MIT).
`vendor/vendored_skills_provenance.md` is the authoritative record: upstream URLs, commit SHAs,
licences, which skills were taken, which were deliberately left behind, and the re-sync procedure.

**Why vendored instead of installed by a tool.** Reproducibility is the bar: same code plus same
trials must give the same numbers. A tool that updates skills on its own schedule can change how
`statistical-analysis` picks a test between two runs of the same analysis. The scientific library
ships roughly 100 commits a month, so this was not hypothetical. Pinning to a commit means `git log`
answers which version of a skill was active when a number was produced. Vendoring also removes the
Node.js dependency and puts every skill under one mechanism.

**What it costs.** Upstream bug fixes and new API coverage no longer arrive by themselves. This is
accepted deliberately. The skill most exposed is `neurokit2`, which pins NeuroKit2 0.2.13 APIs — if
that library ships a breaking change, upstream will update their skill and this repo will not know.
Re-sync it deliberately, per the provenance file, rather than on a schedule.

**Adding or updating a vendored skill:** follow the procedure in
`vendor/vendored_skills_provenance.md`. It requires updating the commit SHA in that file in the same
commit as the content. A provenance file with a stale SHA is worse than none, because it claims a
precision it no longer has.

**A note on the tool that used to do this.** `npx skills add` installed two different ways
depending on the flag — `--all` put content in `~/.agents/skills` and symlinked it in, while
`--skill` copied a real folder straight into `~/.claude/skills`. That second shape is what blocked
the vendored versions from linking until the copies were removed. It is also worth knowing that
`npx` returns non-zero when agents it does not manage here (`Eve`, `PromptScript`) reject a global
install, so its exit code never meant what it appeared to mean. None of this applies any more; it
is recorded because the leftovers may still exist on a machine that was set up earlier.

**Trust:** these skills run with full agent permissions. Vendoring means they were reviewed once at
a known commit and cannot change without a commit here. It also means nobody upstream is patching
them for you. The 1.3 MB in `vendor/` is code this repo is now responsible for.

---

## Phase 6 — Where Google Drive fits

- Papers, decks, meeting notes, non-code deliverables → Drive, mounted normally via Drive for
  Desktop.
- **Never let Drive sync the git repo folder. Never let Drive sync `.claude/skills`.** Keep them as
  sibling folders on disk, not nested. This single rule prevents the corruption risk this whole
  setup was designed around.
- This guide is the exception that proves the rule: a human-readable document that lives in the
  *repo*, because you need it on a machine with no Drive access configured yet.

---

## Quick reference

| | Source of truth | Lives on a machine as | Update mechanism |
|---|---|---|---|
| Personal skills / code | this repo, root folders | symlink in `~/.claude/skills` | `git pull` |
| Vendored third-party skills | this repo, `vendor/` | symlink in `~/.claude/skills` | `git pull`; upstream re-sync is manual |
| claude.ai skills | this repo | zip upload | manual, per update |
| Documents | Google Drive | synced folder (sibling, not nested) | automatic Drive sync |

One source of truth, one update command. That is the entire point of the current design.

---

## Troubleshooting

**`no such ref was fetched` / `origin/main [gone]`**

```
Your configuration specifies to merge with the ref 'refs/heads/main'
from the remote, but no such ref was fetched.
```

The GitHub repo is empty, or `main` was never pushed. Git was told to merge `origin/main` and that
ref does not exist:

```bash
git ls-remote --heads origin     # no output = the remote is genuinely empty
git log --oneline -1             # "does not have any commits yet" = nothing local either
git add -A && git commit -m "Initial commit" && git push -u origin main
```

This is Phase 1 step 3 having been skipped. Nothing is broken or lost.

**`<name> exists and is NOT a symlink — leaving it alone`**

Something other than this repo owns that name in `~/.claude/skills` — most likely a leftover copy
from the old `npx skills` setup, or a folder created by hand. The installer deliberately refuses to
delete real folders. Confirm the repo has the same skill, then remove the folder and re-run:

```bash
ls -la ~/.claude/skills/<name>              # real folder, no arrow
diff -rq ~/lior-claude-skills/vendor/<name> ~/.claude/skills/<name>   # confirm equivalent first
rm -rf ~/.claude/skills/<name> && ./install-skills.sh
```

**An unexpected `Relinking <name> (was pointing elsewhere)`** — that name pointed outside the clone
and the installer took it back. Expected once when migrating a machine off the old setup; on any
other run it means something else is competing for the name.

**`git pull --ff-only` fails some other way** — local changes or a diverged branch on that machine.
Resolve manually (`git status`, then `git stash` or commit) before re-running the installer.

**A skill is not showing up** — confirm `SKILL.md` sits directly inside its folder. Folders without
one are skipped, with a log line. Empty folders cannot be committed to git at all, so a skill that
exists only as an empty directory will never reach another machine.

**Authentication prompts or 403 on push** — HTTPS credentials are not cached. `gh auth login`,
choosing GitHub.com → HTTPS → browser, is the shortest path.

**`git sparse-checkout` is not a git command** — relevant only when re-syncing a vendored skill from
a large upstream repo. Apple's bundled git is old (2.24.3 on this Mac; sparse-checkout needs 2.25+).
Either `brew install git`, or just do a full `--depth 1` clone into a scratch directory and copy the
one folder you need.
