# voiceless_they

Participants read pronoun + verb prompts ("They walk") aloud at a slow and a fast
rate while facial sEMG, mic and camera are recorded. 3 blocks × (slow, fast),
about 16 min of trials and rests plus instructions, calibration and practice.

## Where things are

| | |
|---|---|
| Repo / folder | `Repetition_Voiceless_Pilot/voiceless_they/` (all commands run from here) |
| Conda env | `voiceless` (Python 3.10) |
| Docs | `README.md` (protocol, outputs, markers, verdict, autopilot); `windows_lab_pc_first_run_checklist_recording.md` (lab-PC setup) |
| Config | `config/experiment_config.json` (all parameters) |
| Data | `data/sub-<ID>/`; pilot runs in `data/pilot/sub-<ID>/`; autopilot in `data/pilot/sub-AUTOPILOT/` |
| Machine baselines | `machine_baselines/<HOST>.json` |

## Stage 1 commands

| Command | Proves |
|---|---|
| `python -m pytest tests -q` | the whole suite: pseudorandomizer, markers in strict mode, mocked live run, guards, verdict, machine health, autopilot driver (1055 passed on the lab PC, 2026-10-22) |
| `python psychopy_autopilot.py --selftest` | the autopilot harness |
| `python voiceless_they_experiment_run.py --participant P01 --dry-run` | no window/audio/LSL; writes logs and prints durations |
| `python lsl_json_marker_intervals.py data/sub-P01/<prefix>_events.csv` | markers → one row per event; exits 1 on any lifecycle problem |
| `python voiceless_they_experiment_run.py --participant T --windowed --no-lsl --skip-calibration` | quick visual check: text size, tracker positions, progress-bar direction |

`psychopy_autopilot.py` is vendored from Emotions; keep both copies identical.

## Stage 2: autopilot

| Command | Use |
|---|---|
| `python run_autopilot_session.py` | stress test + full session, software only |
| `... --quick` / `--fast` / `--windowed` | harness checks (timing not judged) |
| `... --hardware` | LSL, mic, camera, fullscreen. Start the EMG recorder and LabRecorder **before** it; it pauses once its streams exist, a person ticks them in LabRecorder and presses Enter |
| `... --stress-only` | is this machine fit today? |
| `... --baseline` | save this machine's baseline: freshly restarted, recorder and LabRecorder running |
| `--run-anyway` | run despite a failed stress test (rehearsal only) |

Its exit code is the verdict's. Stop it by holding Ctrl+C in the task window for
3 s, or Ctrl+C in the console. Delete `data/pilot/sub-AUTOPILOT/` afterwards.

## Stage 3 and 4

- `python machine_health.py --fingerprint` (what this machine is) and the
  stress test above.
- `python voiceless_they_experiment_run.py` opens the setup window
  (`setup_console.py`). Pre-flight checks start immediately (~20 s;
  `python preflight_checks.py` runs them in the console):
  - `XtrodesEMG` and `XtrodesIMU` on the network, exactly once each;
  - the mic opens **and hears sound** (a muted HyperX records silence with no error);
  - the camera delivers the configured resolution at speed, picture neither black
    nor blown out.
- **Begin** is pressed twice: the first shows the summary (what runs, the streams
  to tick, the output folder), the second starts. Begin is refused while a needed
  check is running or failed, unless *Start despite failed checks* is on, which
  is saved in `_session_info.json` under `setup_window`.
- Streams to tick in LabRecorder: `ExperimentAnnotations`, `Audio_Mic`,
  `Video_Frames`, `XtrodesEMG`, `XtrodesIMU`. `Audio_Mic` exists only if the mic
  opened; `Video_Frames` is withdrawn if the camera never recorded. **A stream
  missing from that list is a device problem, not a LabRecorder problem.**
- Experimenter keys during the volume screen: **R** sets the dB reference,
  **ENTER** continues. Fix the mic gain once and never change it between
  participants (the meter is dBFS, not dB SPL).

## Session folder (`data/sub-<ID>/`, files start with `<prefix>`)

| File | Required | Content |
|---|---|---|
| `_trial_order.csv` | yes | written **before** the session starts |
| `_events.csv` | yes | one row per marker call; `marker_error` empty |
| `_trials.csv` | yes | per-trial measured durations and dB |
| `_segments.csv` | karaoke only | pronoun / verb highlight rows |
| `_session_info.json` | yes | config snapshot, seed, refresh rate, dropped frames, mic device, `marker_failures` |
| `_progress.json` | yes | `status`: `completed`, `aborted`, `aborted_marker_failure`, `stopped_early`, `stopped_stream_lost` |
| `_video.mp4`, `_video_frames.csv`, `_video_meta.json` | unless `--no-video` | `Video_Frames` sample N = mp4 frame N |
| `.faults` | yes | ends `=== clean exit ===` |
| `.console.log` | yes | stdout + stderr |
| `.sentinel.log` | yes | last line `VERDICT ...` (CLEAN, ABORTED, CRASH, KILLED/CLOSED, CONSOLE CLOSED, ENDED-WITH-ERROR), ~1 min after exit |
| `.perf.csv`, `.winevents.txt` | yes | machine load, Windows events |
| `.hangN.dmp` | only if hung | |
| `.validation.json` | yes | the verdict, merged over its three stages |
| `.xdf` | yes | from LabRecorder, **in this same folder** |

## Stage 6: the verdict

`validate_session.py` reads files only, so a crashed session still gets one.

| Stage | When | Adds |
|---|---|---|
| `session_end` | printed on the console as the session closes | fault capture, completion, files, streams (published **and** backed by an open device), gaps, trial count, frames, CPU/GPU/RAM |
| `final` | the sentinel, ~1 min after exit | exit code, sentinel VERDICT |
| `xdf` | `python validate_session.py data/sub-<ID>/<prefix>_events.csv --xdf data/sub-<ID>/<name>.xdf` | every stream with samples, gaps, video frames = mp4 frames, CSV markers = XDF markers, 0 lifecycle problems, XDF inside the participant folder |

Also: `python lsl_json_marker_intervals.py <file>.xdf` → 0 lifecycle problems.
Frame and machine numbers are judged against `machine_baselines/<HOST>.json`;
without one they are SKIP, not PASS.

## Incident history

| Date | What happened | Status |
|---|---|---|
| 2026-10-22 | HyperX mic unplugged, `Audio_Mic` still listed in LabRecorder, would have recorded 0 samples; the first verdict passed it | fixed: outlet only after the mic opens; verdict checks the device too |
| 2026-10-22 | Operator quit at 30 s: exit 0, `.faults` only `=== clean exit ===` | not a crash; read progress status + `abort` event together |
| 2026-10-25 | First real stress test: hand-made load with no quit check; baseline without recorders vs test with them called a fresh machine DEGRADED; stress camera published a `Video_Frames` stream | fixed: stress drives the real presenter; `recording_stack` / `stress_version` must match or NO BASELINE; stress test publishes no LSL |

## Known gaps (2026-10-25; re-verify)

- `machine_baselines/LAB006_NEW.json` exists (2026-10-25) but is not committed.
- The Voiceless Asus laptop has no fingerprint or baseline.
- Not built: marker-to-flip latency check, memory-growth (leak) check, recording
  which GPU drives the experiment window (LAB006_NEW has two adapters each
  reporting a 1920×1080 display).
- EMG + IMU path: on the lab-PC checklist as not yet tested on any machine;
  check that file's progress log for the current state.
