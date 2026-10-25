---
name: data-collection-reliability
description: The lab's validation protocol for running a recording session (PsychoPy + LSL/LabRecorder/XDF + EMG, camera, mic), from a code change to an accepted data file - checks after a change, autopilot rehearsal, session-day pre-flight, hardware gates, operator rules during the session, the post-session verdict and XDF check, and crash/freeze triage from the evidence files. Use whenever someone is about to run, rehearse, validate or debug a session, asks "is this safe to run", "what do I check before the participant", "why did the session fail", "is this session usable", or mentions LabRecorder, an .xdf, validate_session.py, autopilot, a stress test, .faults, the sentinel, a hang dump, a freeze or a crash. Has reference files per experiment (Emotions, voiceless_they). Not for writing experiment code (psychopy-experiments) or processing accepted data (pipeline-validation).
---

# Data-collection reliability

**The lab's rule: validation, validation, validation.** A session either finishes
with data we can show is good or, if it fails, leaves enough evidence to say why.
Every step below serves one of those two outcomes.

Explain what each check proves and why it exists, not only the command. People
running sessions skip steps they don't understand, and the steps that seem most
skippable are the ones that catch silent failures.

## Where this skill sits

| Skill | Used by, when | Answers |
|---|---|---|
| `psychopy-experiments` | whoever writes the experiment code | how to build it so it cannot fail silently (fault capture, autopilot, stream watch, verdict) |
| **`data-collection-reliability`** | whoever runs, rehearses or debugs a session | is it safe to record today, and is this session good? |
| `pipeline-validation` | whoever processes the accepted data | did each processing stage keep the signal? |

This skill ends where a session is **accepted** (stage 6). Everything after that
belongs to `pipeline-validation`.

## How to use this skill

1. **Identify the experiment** and read its reference file in `references/`
   (`emotions.md`, `voiceless_they.md`). It holds the real commands, file names
   and incident history. If the experiment has none, use the generic stages
   below and offer to write one (see *Adding an experiment*).
2. **Identify the stage** (table below), and walk only that stage's checklist, in
   order.
3. **A failing check is a stop sign.** Fix it, or write down why it is safe to go
   on. Validation that can be waved through is not validation.
4. **Check the repo before quoting a command.** Tools and flags change. The
   experiment's README and protocol doc win over this skill and over its
   reference file.
5. **Dated facts are snapshots.** Before saying something is still broken or
   still open, check the experiment's changelog and `git log`.

## The rules behind every check

1. **Nothing is "working" until a check says so.** A run that did not crash is
   not a run that worked. The evidence is a file with a pass/fail line, not a
   console that looked fine.
2. **Missing evidence is a failure.** A missing file, a stream with 0 samples, a
   log with no clean-exit line all mean *fail*. A check that could not run is
   `SKIP` with its reason, never `PASS`.
3. **Every check has been seen red.** A check that has never failed on purpose
   is unverified (how to do that: `psychopy-experiments` §8.7).
4. **Validate before, during and after.** Pre-flight and the stress test, then
   fault capture and the stream watch, then the verdict. Each one catches what
   the others cannot.
5. **A person reviews every verdict** before the next participant. The verdict
   is evidence, not a decision the code makes alone. Nothing goes into analysis
   unreviewed.

## The seven stages

| Stage | What | Catches |
|---|---|---|
| 1. After any code, config, stimulus or library change | self-tests, stimulus check, dry run, test suite | broken code, missing or unplayable stimuli, marker-plan errors, test settings left on |
| 2. Before the first real session after a change | autopilot rehearsal | crashes and freezes that only show in a full-length run |
| 3. Session day, before the participant | machine fitness, audio, EMG contact | a degraded PC, silent audio, noisy electrodes |
| 4. Session start | setup window, pre-flight checks, hardware gates | wrong participant or config, a stream not running, a stream not recorded |
| 5. During the session | evidence files, stream watch, operator rules | data loss, a freeze with no record of why |
| 6. Right after | verdict, file checklist, XDF check | a session that looks complete but is not |
| 7. When something fails | triage table, freeze rule, recovery tools | lost evidence, lost video |

### Stage 1: after any change

Run the experiment's code-level checks (its reference file lists them). None needs
a participant. The usual set:

- **Self-tests** for every module that defines config, markers or vocabulary.
- **The test suite** (`pytest`), where the project has one.
- **A stimulus check** that opens every file and compares it with its manifest.
  A movie with no duration otherwise ends on frame 1 without an error.
- **A dry run** that prints the session plan on paper: phases, block order,
  marker count, duration.

Then:

- **Look at the config toggles before committing.** A test setting (a phase
  switched off, a short trial count) must not reach a real session. The
  start-up summary may flag it; don't rely on that alone.
- **Commit, then pull on every rig.** All machines run the same commit
  (`git log -1 --oneline`), and the session file records it.
- **Log the change** in the experiment's changelog.

### Stage 2: autopilot rehearsal

The autopilot runs the **real** session with nobody at the keyboard, into a
throwaway participant folder, and ends with the verdict. Run it after any
experiment change, after any PsychoPy/driver/Windows update (on each machine),
and when chasing a crash.

| Mode | Use |
|---|---|
| default | the task survives end to end at real pace |
| `--quick` / `--fast` / `--windowed` | harness checks only. These change timing and load, so they **cannot** clear a crash or a timing question |
| `--hardware` | the full rig: recorder, LabRecorder, camera, mic. **A person answers the hardware gate**; the autopilot never vouches for hardware it can't see |
| `--stress-only` / `--baseline` | is this machine fit today / save its baseline (where the experiment has them) |

**A crash reproduction must match the session it reproduces:** full counts, real
pacing, camera on, fullscreen.

**Pass criteria (all must hold):** the verdict passes (exit code 0); the run ended
`completed`; the fault log ends with its clean-exit line; the sentinel's VERDICT is
clean; no hang dumps; with `--hardware`, the XDF has every stream with samples and
no gaps. Delete the throwaway folder afterwards.

### Stage 3: session day, before the participant

**Machine**

- Pause Windows Update and Microsoft Store updates for session hours. A Store
  update was the only background activity logged during a machine-wide stall
  (Emotions, 2026-10-19).
- Close everything the session does not need: browsers, Teams, OneDrive sync,
  other Python processes.
- LAN cable, not Wi-Fi, for LSL.
- Same commit on every rig.
- Where the experiment has a stress test, run it with the recording programs
  already running (as in a session):

| Result | Action |
|---|---|
| `FIT` | run |
| `DEGRADED` | restart the computer, then run the stress test again |
| `UNFIT` | no participant on this machine today |
| `NO BASELINE` / not comparable | the numbers are not judged. Take a baseline (freshly restarted, recording programs running) before trusting them |

**Audio:** play a real stimulus through the exact output device the session will
use, and for a mic, confirm it **hears sound**, not just that it opens. A muted
output or mic produces no error and looks exactly like a normal trial.

**EMG:** a quiet resting baseline on every channel, and every electrode responds
to a face scrunch. Packet loss stays under 5 %. Don't start with a channel you're
unsure of. The in-session calibration is the functional check; review it after.

### Stage 4: session start

1. **Setup window.** Check participant, session, condition, and the list of what
   will run. Use **pilot mode** for anything that is not real data, so it can never
   be mistaken for real data.
2. **Pre-flight checks** (where the experiment has them) must be green. Starting
   despite a failed check is a decision to write down, and the session file
   records it.
3. **Recorder gate.** Proceed only when the EMG recorder is streaming.
4. **LabRecorder gate.** Press Update, tick **every** stream the session lists,
   check the file lands in the participant's own folder, press Start, then
   confirm. **LSL does not backfill**: a stream not ticked now is missing for
   good.

### Stage 5: during the session

The protection is automatic; the operator's job is not to destroy it.

**What the session writes** (exact names in the reference file):

| Evidence | Tells you |
|---|---|
| console log | everything printed, including tracebacks |
| flushed event log / progress file | the last thing the session did; survives any crash |
| fault log (`.faults`) | Python stacks of a native crash, dead threads, freeze-watchdog dumps; ends with a clean-exit line only if the run finished |
| sentinel log | a separate process: when the window was "Not Responding", the exit code, a final VERDICT |
| `.perf.csv` | per-second CPU, disk, memory: shows machine-wide stalls |
| `.hangN.dmp` | native dumps of every thread while hung |
| `.winevents.txt` | Windows events for the session window |
| per-frame video index (CSV) | frame count survives even if the mp4 does not |
| LSL marker stream (in the XDF) | every marker, recorded by another process, so it survives the experiment dying |

**Stream watch** (where built): no samples for 2 s is a FLAG (the session goes
on); no samples for 10 s is a safe stop. It counts samples arriving, never signal
level, so a silent participant never trips it.

**Operator rules**

- Glance at the console now and then; write down the time of any WARN or ERROR.
- **If the screen freezes or goes white, close nothing for 2 minutes.** The PC
  is writing hang dumps. Photograph the screen and any dialog, then close it and
  write down *how* (dialog button, the X, Task Manager, Ctrl+C) and roughly when.
  The exit code depends on how, and it's the only way to tell a freeze from a
  crash afterwards.
- **Do not stop LabRecorder until the experiment window is gone.**
- Note what the EMG app and the recorder terminal show at that moment. Neither
  leaves a file.
- To quit on purpose: **hold Ctrl+C in the task window for 3 s** (a single key
  does nothing). Ctrl+C in the console is the instant emergency stop.

### Stage 6: after the session

1. Press **Stop** in LabRecorder (the XDF is incomplete until you do), then stop
   the EMG recorder.
2. **Read the verdict** the session printed (`validate_session.py`). `FAIL` sets
   the exit code; `FLAG` is information for the reviewer; `SKIP` always says why.
3. **Check the folder**: every expected file is there and not empty (list in the
   reference file).
4. **Validate the XDF**: every stream present with samples and no gaps beyond the
   flags; markers in the CSV = markers in the XDF, 0 lifecycle problems; video
   frames = frame-stream samples; the XDF sits in the participant's own folder.
   Then look at it (e.g. in `mnelab-streams`): markers aligned with EMG,
   calibration movements raise the expected channels. Handing the verdict and the
   XDF to Claude for this pass is the normal route.
5. **Back up** the session folder.
6. **One-line session note**: anything unusual, any warnings, who ran it.

A session that passes 2 to 4 is **accepted**, and from here `pipeline-validation`
takes over. A session that does not pass goes to stage 7 before anyone deletes,
moves or reruns anything.

### Stage 7: when something goes wrong

**Do not lose the evidence.** Don't delete, move or rerun into the session folder
until the files are copied or read. A rerun gets a new timestamp, but note which
run is which.

| Question | Look at |
|---|---|
| What was the last thing it did? | tail of the event log / progress file; the XDF marker stream |
| Python error? | console log traceback; session file `end_reason` / status |
| Native crash (process vanished)? | `.faults` stack + sentinel exit code (table below) + `.winevents.txt` |
| Freeze? | `.faults` watchdog dumps; sentinel "Not Responding" times; `.hangN.dmp` |
| Whole machine stalled? | `.perf.csv` around the failure; EMG gaps in the XDF |
| Alive but frozen, or dead? | video frame index: frames written after the last marker = alive and frozen |
| Operator quit or crash? | read them **together**: exit code, last `.faults` line, progress status, the `abort` event. No single file tells you |
| Finished cleanly? | `.faults` ends with the clean-exit line and the sentinel VERDICT is clean |

**Exit codes** (calibrated on a lab PC, Windows 11, Python 3.10):

| Code | Meaning |
|---|---|
| `0` | normal exit. **Also Ctrl+C when the launcher catches it**: read the end reason |
| `1` | Task Manager / `taskkill /F`, **or** an uncaught Python exception (was the window hung first?) |
| `3` | `abort()` or `raise(SIGSEGV)` |
| `0xC0000005` | real access violation (native crash) |
| `0xC000013A` | console window closed, or a Ctrl+C Python did not catch |
| `0xCFFFFFFF` | hung window closed via X → "Close the program". Also logs Application Event 1002 |

A dead freeze **without** an Event 1002 was most likely ended in Task Manager.

**Reading traps**

- **`.faults` logs exceptions that were then handled.** It can say `Windows fatal
  exception: access violation` in a process that exited normally. Never call it a
  crash on `.faults` alone; pair it with the exit code.
- **Reading a hang dump:** WinDbg (`winget install Microsoft.WinDbg`) ships `cdb`:

  ```powershell
  & "C:\Program Files\WindowsApps\Microsoft.WinDbg_<ver>_x64__8wekyb3d8bbwe\amd64\cdb.exe" `
    -z <base>.hang1.dmp -c "~*kc 20; q"
  ```

  Read the main thread bottom-up from `_PyEval_EvalFrameDefault` into the C call
  it is stuck in. Compare `hang1` with `hang2`: identical stacks mean a true
  deadlock; different stacks mean a stall that is still moving.

**Write it up** in the experiment's plans/notes folder: what happened, an evidence
table, hypotheses kept **and rejected**, and what would settle it next time. Keep
the rejected ones so nobody re-derives them.

## Adding an experiment

Write `references/<experiment>.md` with these sections, filled from the repo,
not from memory:

1. **Where things are**: repo, working folder, conda env, protocol doc, changelog.
2. **Stage commands**: the stage 1 checks, the autopilot commands, the
   pre-flight and verdict commands.
3. **Session folder**: every file a session writes, and which are required.
4. **Experiment-specific gates and rules** beyond the generic stages.
5. **Incident history** (dated) and **known gaps** (dated).

If the experiment lacks a piece of the protection (no autopilot, no sentinel, no
verdict), list it under known gaps and build it with `psychopy-experiments`. The
minimum for a trustworthy experiment:

1. Self-tests that need no participant, for every module defining config or markers.
2. A stimulus checker against a manifest.
3. A rehearsal that cannot be mistaken for real data.
4. Hard gates before recording, with "tick every stream" if the recorder cannot
   backfill.
5. Evidence that survives a crash: flushed event log, fault capture, an
   independent watcher process, a per-frame video index, markers recorded in
   another process.
6. Outputs saved **before** hardware is released, since release is where hangs happen.
7. An automated verdict after every session, plus a written list of the checks
   that are still manual.
8. A triage table mapping each question to the file that answers it.
