# Vendored skills — provenance and re-sync record

Every skill folder in `vendor/` was copied from an upstream repository at a **pinned commit**.
None of them were written here. This file is the record of where each came from, under what
licence, and how to bring it up to date.

Vendored on **2026-08-26**.

## Why these are vendored rather than installed by a tool

They were previously installed with `npx skills add`, which meant three different mechanisms
(git for personal skills, `~/.agents/skills` symlinks for whole-repo installs, direct copies for
single-skill installs) and no control over when a skill's behaviour changed underneath a running
analysis. Reproducibility is the bar for this work: the same code and the same trials must give
the same numbers, and a skill that silently rewrites how a statistical test is chosen breaks that.
Vendoring pins every skill to a commit that only changes when someone commits here.

The cost is accepted deliberately: upstream bug fixes and new API coverage no longer arrive on
their own. See **Re-syncing** below.

## Sources

### `julianoczkowski/designer-skills`

| | |
|---|---|
| Upstream | https://github.com/julianoczkowski/designer-skills |
| Commit | `c259656c76d9758d7ead46b0d2f125cbe84f8665` (branch `main`) |
| Commit date | 2026-07-06 |
| Licence | Apache-2.0 — `licenses/designer-skills_LICENSE_Apache-2.0.txt` |
| Upstream velocity | ~15 commits over 3.5 months. Slow; staleness costs little. |

Skills taken (8, from the repo root): `brief-to-tasks`, `design-brief`, `design-flow`,
`design-review`, `design-tokens`, `frontend-design`, `grill-me`, `information-architecture`.

### `K-Dense-AI/scientific-agent-skills`

| | |
|---|---|
| Upstream | https://github.com/K-Dense-AI/scientific-agent-skills |
| Commit | `36d8f13a1e754618794bf42f417884940077b4ae` (branch `main`) |
| Commit date | 2026-08-24 |
| Package version | 2.64.0 |
| Licence | MIT — `licenses/scientific-agent-skills_LICENSE_MIT.md` |
| Upstream velocity | ~100 commits per month. **Fast** — this one genuinely goes stale. |

Skills taken (8 of 163, from `skills/`): `neurokit2`, `statistical-analysis`, `statistical-power`,
`statsmodels`, `scikit-learn`, `scientific-writing`, `citation-management`, `umap-learn`.

`K-Dense-AI/claude-scientific-skills` is a redirect to this repo; the canonical name is used here.

**Deliberately not taken:** `matplotlib`, `seaborn`, `scientific-visualization`. They trigger on
plotting and would compete with `graphing-guide`, which owns the house figure style and the Hebrew
RTL rules. A generic plotting skill winning that race is a quiet way to produce a wrong Hebrew
label. Do not add them without revisiting that decision.

The other 155 skills were left upstream on purpose: every skill's description loads into every
session's context, and `astropy`, `cirq`, `diffdock` and the like are irrelevant to this work.

## Modifications

**None.** All 16 folders are byte-for-byte copies of the upstream files at the commits above.
This satisfies the Apache-2.0 requirement to state changes: there are none. If you ever do edit a
vendored skill, record it here — which file, what changed, and why — and note that the change will
be lost on the next re-sync unless you re-apply it.

## Re-syncing a vendored skill

There is no automatic update path, by design. To refresh one:

```bash
# 1. Clone upstream shallowly into a scratch directory
git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git /tmp/sci

# 2. Diff before overwriting — this is the whole point of pinning the SHA
diff -r /tmp/sci/skills/neurokit2 ~/lior-claude-skills/vendor/neurokit2

# 3. If the diff is acceptable, replace the folder and re-run the installer
rm -rf ~/lior-claude-skills/vendor/neurokit2
cp -R /tmp/sci/skills/neurokit2 ~/lior-claude-skills/vendor/neurokit2
cd ~/lior-claude-skills && ./install-skills.sh

# 4. Update the commit SHA and date in this file, then commit both together
```

Step 4 is not optional. A provenance file with a stale SHA is worse than none, because it claims a
precision it no longer has.

## Adding a new vendored skill

1. Copy the folder into `vendor/<skill-name>/`. It must contain a `SKILL.md` directly inside.
2. Add it to the source's skill list above.
3. If it comes from a new upstream, add a source section and put its licence in `licenses/`.
4. Run `./install-skills.sh` and confirm the new skill links.
5. Commit the skill, this file, and the licence together.

## Note on trust

These skills run with full agent permissions. Vendoring means you reviewed them once at a known
commit and nothing changes without a commit here — which is the security benefit. It also means
nobody upstream is patching them for you. The 1.3 MB in this folder is code you are now
responsible for.
