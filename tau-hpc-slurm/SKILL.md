---
name: tau-hpc-slurm
description: Use this whenever Lior is doing anything with the TAU HPC / SLURM cluster — connecting via SSH, writing or debugging an sbatch script, checking squeue or check_my_partitions, deciding between CPU/GPU partitions, working with /scratch100 or /localscratch, or troubleshooting a hung/failed SSH login to slurmlogin.tau.ac.il or powerslurm-login*.tau.ac.il. Also trigger proactively if Lior describes wanting to run EEG preprocessing, ICA, or any batch analysis "on the cluster" or "on HPC," even if he doesn't say SLURM directly — he's still building fluency with this system and benefits from concepts being explained in plain language, not just scripts being handed to him.
---

# TAU HPC / SLURM Workflow

Lior is a new Master's student doing EEG/MNE-Python research, still building fluency with SLURM and cluster computing — he explicitly wants to understand *why*, not just get a working script. When helping with anything here, briefly explain new pieces in plain language the first few times they come up. Ease off the explaining once a term has clearly landed (watch for him using it fluently himself unprompted).

## Lior's actual setup — don't make him rediscover these

- **Username:** `liorki`
- **Login hosts:** `slurmlogin.tau.ac.il` (load-balanced across three nodes) — if that hangs, fall back to the direct nodes `powerslurm-login.tau.ac.il` / `powerslurm-login2.tau.ac.il`
- **VPN:** already installed and working on his MacBook — no need to walk through GlobalProtect setup again
- **Account:** `public-chenbar_v2` — his supervisor's (chenbar) lab allocation, not the generic public one
- **Partitions available to him:**

| Partition | Account | QOS | Use for |
|---|---|---|---|
| `power-general-shared-pool` | `public-chenbar_v2` | `public` | **Default for all CPU jobs** — EEG preprocessing, ICA. 236 nodes, ~27,600 CPUs. Always start here. |
| `power-general-public-pool` | `public-chenbar_v2` | `public` | Confirmed via `scontrol`: identical time limits and priority tier to shared-pool, just a tiny 8-node subset of largely the same nodes. No known reason to prefer it — don't suggest it unless HPC support says otherwise for a specific case. |
| `gpu-general-pool` | `public-chenbar_v2` | `public` | GPU-bound work only (deep-learning EEG decoding, not classical MNE/ICA). Use this even though `shared-pool`'s node list also includes some GPU nodes — don't route GPU requests through `shared-pool`. |

When writing any `#SBATCH` script for him, fill in `--account=public-chenbar_v2` and the right partition yourself — don't leave them as placeholders for him to fill in.

## Plain-language glossary

Use these phrasings instead of jargon until he's clearly using the real terms himself:

- **Node** — one physical machine in the cluster.
- **Partition / queue** — a named pool of nodes with its own rules. Same thing, two names.
- **Account** — which lab's allocation a job bills against. His is his supervisor's.
- **QOS** — priority/limits tier. His has always been `public` so far.
- **`sbatch`** — "submit this script, run it whenever a node is free, don't wait around for it."
- **`srun`** — run something *right now*, interactively, blocking until it finishes.
- **Job array** — one script, run many times in parallel, once per item (e.g. once per participant).
- **Scratch** — fast temporary storage, *not backed up*, for files only needed during a job.

## Connecting

```bash
ssh liorki@slurmlogin.tau.ac.il
```

If it hangs after the password (a garbled colored banner, then nothing) — this has happened before and is usually a shell-startup hiccup, not a real problem:

1. If this is a first-ever login, wait 1–2 minutes (home directory can be slow to provision).
2. Open a *second* terminal tab and try the direct node hostnames instead of the balanced one:
   ```bash
   ssh -v liorki@powerslurm-login.tau.ac.il
   ssh -v liorki@powerslurm-login2.tau.ac.il
   ```
3. If one direct node hangs at the same spot (`pledge: fork` in the verbose output) but the other connects fine, that's a specific-node issue — just tell him plainly, he doesn't need to chase it further.
4. If both hang identically, that's the point to suggest emailing `hpc@tauex.tau.ac.il` with the `-v` log attached — not before.

## Storage — what goes where

- `/home/liorki` — backed up, default landing directory. Scripts, configs, small outputs.
- `/scratch100`, `/scratch200`, `/scratch300` — shared, fast, **not backed up**. Working files needed only during a job.
- `/localscratch` — node-local, fastest, **must be self-cleaned**. Any script using it needs:
  ```bash
  export CACHEDIR=/localscratch/${USER}_${SLURM_JOB_ID}
  mkdir -p $CACHEDIR
  cleanup() { rm -rf -- "$CACHEDIR" || true; }
  trap cleanup EXIT INT TERM HUP
  ```
  Always include this trap if `/localscratch` shows up in a script — don't let it slip, the space is shared with other people's jobs.

Rule of thumb: raw/processed EEG data that needs to persist → home, or ask his supervisor about dedicated lab storage. Anything transient during a single run → scratch.

## Writing a job script

Default CPU template — already has his real account/partition baked in:

```bash
#!/bin/bash
#SBATCH --job-name=<descriptive_name>
#SBATCH --account=public-chenbar_v2
#SBATCH --partition=power-general-shared-pool
#SBATCH --qos=public
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --output=<name>_%j.out
#SBATCH --error=<name>_%j.err
#SBATCH --mail-user=liorki@mail.tau.ac.il
#SBATCH --mail-type=END,FAIL

module purge
module load <conda-module>
conda activate eeg

python <script>.py --input /scratch100/liorki/raw/<file>
```

Only ask him for the things that genuinely vary: which script, which input file, roughly how long it'll take, how much memory. Don't make him restate username/account/partition — those are fixed, above.

**Many participants at once** → job array instead of separate submissions:
```bash
#SBATCH --array=1-<N>
#SBATCH --output=<name>_%A_%a.out
```
Inside the script, reference the participant with `sub-$(printf "%02d" $SLURM_ARRAY_TASK_ID)`.

**GPU job** (deep-learning work only, not classical MNE/ICA) — swap the partition and add:
```bash
#SBATCH --partition=gpu-general-pool
#SBATCH --gres=gpu:1
```

**Dependent pipeline stages** (preprocess → ICA → epoch):
```bash
jid1=$(sbatch --parsable preprocess.sh)
sbatch --depend=afterok:$jid1 run_ica.sh
```

**Max runtime:** 7 days (`--time=7-00:00:00`) is the hard ceiling for any `sbatch` job.

## Monitoring

```bash
squeue -u liorki          # what's running / pending
cat <name>_<jobid>.out    # output once a job finishes
scancel <jobid>           # cancel a job
```

## Guardrails

- **Never suggest running actual compute on the login node** — always route through `sbatch`/`srun`. The login node is shared, and heavy processes there get killed.
- **Never leave `/localscratch` usage without the cleanup trap.**
- Default to `power-general-shared-pool` for CPU work unconditionally — it's confirmed to have no downside versus `power-general-public-pool` and a far bigger node pool.
- If `check_my_partitions` or a job submission ever comes back empty/denied, treat that as an access problem, not a script problem — point him to `hpc@tauex.tau.ac.il` rather than debugging the script further.
