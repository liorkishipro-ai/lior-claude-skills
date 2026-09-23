---
name: git-commit-workflow
description: Use this any time the user is about to commit, save, or push a code change, is naming a branch, says things like "let's commit this," "I made a change to the script," "should I branch this," or is wrapping up work on a project tracked in Git. Also trigger proactively when the user describes modifying a file (e.g. "I added X to the script," "I changed Y to Z") but hasn't committed yet, or when they fall back into renaming/suffixing files (e.g. "script_v2.py," "script_LSL.py") instead of using branches — catch this pattern and redirect to proper Git hygiene. Walks the user through clarifying what changed, choosing the right branch prefix (or recognizing it isn't a branch at all), writing a precise commit message, executing the commands, and surfacing the project's commit/branch/tag timeline so Git stays a trustworthy home base rather than a chore.
---

# Git Commit Workflow

A forcing function for disciplined commits. The goal is precision, not speed: every commit should be traceable, every branch should have an obvious purpose, and the project history should read like a clear log, not a guessing game.

Run through these steps **in order**, every time. Don't skip to "just write the commit message" — the earlier steps are what make the commit message and branch name correct.

## Step 0 — Orient (read-only, do this yourself, don't ask)

Before asking the user anything, find out where things actually stand. If a bash/terminal tool is available and a repo is present, run:

```bash
git status
git branch --show-current
git log --oneline -5
```

This tells you: what's uncommitted, what branch you're on, and what just happened. If no terminal tool is available, ask the user to paste the output of those three commands. Never skip this — advice given without knowing current state is a guess.

## Step 1 — Clarify the change

Ask the user directly (short, plain-language, one at a time is fine):

1. **What actually changed?** One sentence, concrete. Not "improvements" — "added LSL streaming output to the karaoke script."
2. **Why?** Bug fix, new capability, cleanup, or an experiment you might discard.
3. **Is this "and" a two-part answer?** If the "what changed" answer contains "and" joining two unrelated things (e.g. "added LSL support and fixed the Hebrew rendering"), stop — that's two commits, possibly two branches. Split it before proceeding.

## Step 2 — The branch-or-parameter test

This is the step people skip, and it's the one that actually prevents the old `_LSL` / `_HE` suffix habit from creeping back in disguised as branches.

Ask: **"After this is done, will there ever be a legitimate reason to run the OLD and NEW versions side by side, on purpose, going forward?"**

- **No** → this is temporary work-in-progress. It belongs on a branch that will merge into `main` and then get deleted. Continue to Step 3.
- **Yes** → this is not a branch at all. It's a permanent runtime option (a `--lang=he` flag, a config value, an environment variable). Branches are for divergence that resolves — merges or gets discarded. A permanent fork in behavior that lives forever is a parameter, not a branch. If you keep it as a branch, you'll be manually re-merging every future bug fix into both forever. **Redirect the user here** rather than proceeding to branch naming: help them turn it into a flag/config option in the same file, under the same filename, instead of building a branch for it.

Only proceed past this step for genuine temporary work.

**Exception: Adding a completely new, isolated skill directory.** These are purely additive (can't break existing code) and can go straight to main. No branch needed — just create the skill directory, add it, commit, and push. They don't need Step 3 onwards.

## Step 3 — Choose the prefix

| Prefix | Use for | Ends in |
|---|---|---|
| `feature/` | New capability, intended to merge | merge → delete branch |
| `fix/` | Bug fix, intended to merge | merge → delete branch |
| `experiment/` | Trying an idea that might not survive | merge, or discard entirely |
| `refactor/` | Restructuring code, no behavior change | merge → delete branch |
| `chore/` | Dependencies, config, tooling, non-functional maintenance | merge → delete branch |
| `docs/` | Documentation only | merge → delete branch |

Pick one based on the Step 1 answers. If the user is unsure between two, ask which one describes the *intent*, not the *content* — a change that touches code but is purely to make tests pass is `chore/`, not `feature/`.

## Step 4 — Name the branch

`<prefix>/<short-kebab-case-description>` — describes the change, not the file it lives in.

- Good: `feature/add-lsl-streaming`, `experiment/try-realtime-pitch-shift`
- Bad: `feature/karaoke_main_LSL`, `update`, `fix-stuff`

The filename underneath never changes. The branch name carries the "what" and "why" so the file doesn't have to.

## Step 5 — Write the commit message

- **Imperative, present tense**: "Add LSL streaming to karaoke script" — not "Added" or "Adds."
- First line ≤ 50 characters. If more context is needed, blank line, then a short body explaining *why*, not just *what* (the diff already shows what).
- One logical change per commit. If Step 1 surfaced an "and," that's already been split — keep it split here too.

## Step 6 — Execute

Fill in the specifics from Steps 2–5. If a terminal tool is available and the user confirms, run these yourself, one at a time, checking output between steps rather than blindly chaining them:

```bash
git checkout main
git pull
git checkout -b <prefix>/<short-description>

# ... user makes changes ...

git status                      # confirm only intended files show as changed
git add <specific files>        # avoid blind `git add .` — name the files
git status                      # confirm only intended files are staged
git commit -m "<imperative message>"
git push -u origin <prefix>/<short-description>
```

When the branch is verified working and ready to fold back in:

```bash
git checkout main
git pull
git merge <prefix>/<short-description>
git push
git branch -d <prefix>/<short-description>
git push origin --delete <prefix>/<short-description>
```

If no terminal tool is available, output this exact block for the user to run themselves, with the specifics already filled in — don't make them do the substitution.

## Step 7 — Timeline check

This is what makes Git feel like a "home base" instead of a black box: always be able to see the shape of the project at a glance. After executing (or at the start of any session where the user asks "where are we"), surface:

```bash
git log --oneline --graph --all -15
git branch -a
git tag --sort=-creatordate
```

Then ask one question: **"Does this point deserve a tag?"** — e.g. "first working demo," "version used in Study 1," "pre-refactor snapshot." If yes:

```bash
git tag -a <milestone-name> -m "<what this snapshot represents>"
git push origin <milestone-name>
```

Tags are the correct tool for "I need to be able to come back to exactly this" — never a duplicated file with a suffix. A tagged commit can be checked out by name anytime (`git checkout study1-v1`) without the live files ever carrying that history in their names.

## Guardrail: catching the old habit

If the user starts naming a file `_v2`, `_LSL`, `_HE`, `_backup`, `_final`, or similar — stop and name what's happening: that information belongs in a commit message, a branch name, or a tag, not in the filename. Ask which of the three it actually is (Step 2's test settles this) and redirect there instead of letting the rename happen.
