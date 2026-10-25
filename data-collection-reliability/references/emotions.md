# Emotions experiment

Facial EMG during emotion phases (photos, video, commanded, Ekman, audio, smell),
solo or together (dyad). Two rigs: machine A and machine B.

## Where things are

| | |
|---|---|
| Repo | `Emotions-Experiment` |
| Working folder | `experimental_scripts/` (all commands below run from here) |
| Conda env | `emotions` |
| Operator protocol | `md_plans/Emotions_Experiment_Protocol.md` (step-by-step for running a participant; this skill is the layer around it) |
| Design + acceptance gates | `md_plans/emotions_experiment.md`, section 12 (gates G1 to G13) |
| Changelog | `md_plans/CHANGELOG.md` |
| Data | `Data/D<dyad>/P<pid>/`; pilot runs in `Data/Pilot/`; autopilot in `Data/D99/P99` |

## Stage 1 commands

| Command | Proves |
|---|---|
| `python emotions_experiment.py --selftest` | every config key and instruction text exists; outlets open before the first marker; onsets use `callOnFlip`; crash marker sent before `recording_stop` |
| `python session_plan.py --selftest` | marker vocabulary is unique, paired, parseable |
| `python setup_dialog.py --selftest` | console overrides (phases, blocks, pilot, windowed) resolve correctly |
| `python dyad_keyboards.py --selftest` | two-keyboard attribution (together sessions) |
| `python run_emg_recorder_gui.py --selftest` | EMG launcher logic |
| `python tools/psychopy_autopilot.py --selftest` | the autopilot harness |
| `python run_emotions_lsl.py --check-stimuli` (~1 min) | every stimulus exists, opens, matches its manifest |
| `python run_emotions_lsl.py --dry-run --dyad D99 --p1 P99 --kind solo` | session plan on paper: phases, block order, smell rack, marker count |
| `python tools/movie_decoder_warmup_probe.py` (minutes) | every movie decodes through the warm-up path. **Required after a PsychoPy upgrade, new clips, or a new machine** |
| `python tools/test_fault_capture.py --suite --out D:/scratch/fc` (~10 min) | crash/freeze evidence records what happened. **Required after any change to fault capture or the sentinel** |

Toggles to check in `emotions_config.py` before any real session: `RUN_COMMANDED`,
`RUN_EKMAN` and the other `RUN_*` phase switches. The start-up summary marks a
switched-off phase `!! OFF IN CONFIG`.

## Stage 2: autopilot

`python tools/run_autopilot_session.py` runs a full solo session into `Data/D99/P99`.

| Command | Use |
|---|---|
| `python tools/run_autopilot_session.py` | full solo, real pacing, camera on |
| `... --hardware` | EMG recorder, LabRecorder, camera live; the two gates **clicked by a person** |
| `... --fast --quick` | 2 trials per block, no camera: harness only |
| `--photo-only`, `--no-audio-block`, `--windowed` | narrower reproductions |
| `--only-phase`, `--camera-resolution` | short rig runs (on branch `feature/autopilot-hardware-mode` as of 2026-10-25) |

Pass: console ends `Session complete` (not `SESSION DID NOT FINISH CLEANLY`);
`.json`, `responses.csv`, `_live.jsonl` exist and `_live.jsonl` ends with
`session_end`; `.faults` ends `=== clean exit ===` with no stack dumps before
`=== teardown started ===`; `.sentinel.log` ends with a clean `VERDICT`; no
`.hang*.dmp`; `python tools/validate_session.py Data/D99/P99` passes.

Expected noise: with no speaker plugged in, the audio block prints errors.

## Stage 3 specifics

- Audio: `python tools/audio_preflight.py` plays a real stimulus through the
  session's device (`--list` outputs, `--sweep` try each, `--loop` while setting
  volume). The audio block shows nothing on screen while sound plays, so a muted
  device looks exactly like a normal trial.
- EMG: tablet signal check, step 9 of the operator protocol. Packet loss in
  `run_emg_recorder_gui.py` under 5 %.
- Machine B: the camera and the Bluetooth radio share one USB root hub. Use a
  port on another controller if possible (Device Manager > View > Devices by
  connection).

## Stage 4

`python run_emotions_lsl.py`: setup console (use **Pilot mode** for non-data
runs, writes to `Data/Pilot/`), then the EMG recorder gate, then the LabRecorder
gate, which lists every stream and prints the session folder.

## Session folder

Name base `<pid>_<dyad>_<kind>_<timestamp>` (except the console log).

| File | Required | Content |
|---|---|---|
| `session_console.md` | yes | everything printed |
| `<base>_live.jsonl` | yes | one flushed line per event; ends `session_end` |
| `<base>.json`, `responses.csv` | yes | session outputs, written **before** hardware is released |
| `<base>.faults` | yes | ends `=== clean exit ===` |
| `<base>.sentinel.log` | yes | ends `VERDICT` |
| `<base>.perf.csv`, `.winevents.txt` | yes | machine load, Windows events |
| `<base>.hang1.dmp`, `.hang2.dmp` | only if hung | dumps at 25 s and 85 s of "Not Responding" |
| `<base>.mp4`, `_video_frames.csv` | if camera on | one CSV row per frame |
| `.xdf` | yes | from LabRecorder |

## Stage 6 specifics

`python tools/validate_session.py Data/D<dyad>/P<pid>` checks marker structure
and gate G7 (every rating in `responses.csv` matches its marker). Only the
structural gates and G7 are automated. Streams present, EMG continuity, channel
quality, timing offset, video frame count and audio delivered are manual (open
the XDF in `mnelab-streams`). In the calibration block, smile, eyebrows and eyes
each raise a different set of channels.

## Recovery tools

Video with no index ("moov atom not found"):
`python tools/recover_truncated_mp4.py BROKEN.mp4 --reference GOOD.mp4 --fps 30`.
Writes `<name>_recovered.mp4` next to it, never touches the original, and prints the
rebuilt frame count against `_video_frames.csv` (they should match).

Write-ups go in `md_plans/` (e.g. `video_block_freeze_2026-10-19.md`).

## Incident history (to 2026-10-25)

| Date | What happened | Status |
|---|---|---|
| 2026-08-11 | Commanded clips crashed on 3rd frame (decoder not ready) | fixed: `prepare_movie` warm-up |
| 2026-08-17 | Clean session looked like a crash (shutdown hung on black screen) | fixed: hard exit (`os._exit`) |
| 2026-08-17 | Two solo sessions died near photo trial 16; no `.json`, mp4 without index | **cause unknown**; outputs now saved before teardown; mp4 recovery tool |
| 2026-08-23 | Native access violation entering video block (volume write on soundless clips) | fixed: movie volume guard |
| 2026-10-19 | Machine A: video-block freeze (white screen), EMG went on. Machine B: machine-wide stall killed EMG, experiment survived | **cause unknown**; led to the stage 5 evidence system |

## Known gaps (checked 2026-10-25 on LAB006_NEW; re-verify)

- Two crash causes unknown (photo block, August; video block, October). Both were
  long solo sessions, so the commanded phase and session length stay confounded
  suspects until a failure is caught with full evidence.
- Most acceptance gates are manual.
- On LAB006_NEW, `main` (622cecb) still has `RUN_COMMANDED = False` and no flip
  freeze watchdog (`run_emotions_lsl.py` notes it "lacks A's flip watchdog"). The
  2026-10-25 changes (freeze watchdog, teardown disarm, shared file timestamp,
  flattened data folder, `RUN_COMMANDED` / `RUN_EKMAN` back on) exist only on
  machine A. Commit them there and pull here before the next real session.
- No stream watch yet (built in voiceless_they, `session_guards.py`). The quit
  is the lab standard: hold Ctrl+C for 3 s (`emotions_experiment.py`,
  `_install_quit_watcher`).
- Fault-capture follow-ups: the watchdog re-arms on the frame loop once a second
  (possible small stutter); minor cleanup of capture functions.
