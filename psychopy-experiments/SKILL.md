---
name: psychopy-experiments
description: Use when writing, debugging or reviewing PsychoPy experiment code - rendering (ImageStim/TextStim), layout in height units, RTL/Hebrew text - and when building the operator setup GUI (PyQt6/tkinter inside a PsychoPy process, config overrides from a window, testable with no display). Also for building LSL streams that must not lie (no outlet without a source, a stream that stops mid-session), safe stops (hold-Ctrl+C-3-s quit, stream-loss stop), crash/freeze capture (faulthandler, an out-of-process sentinel, hang dumps), and an AUTOPILOT in every experiment - an unattended run that stress-tests the machine, drives the real session, measures it against the machine's baseline, and ends in a pass/fail verdict. Non-obvious gotchas from real experiments. Load before editing stimulus code, a setup dialog, recording/LSL code, quit handling, fault capture or an autopilot. For BUILDING these; to run, rehearse, validate or triage a session, use data-collection-reliability.
---

# PsychoPy Experiments

A growing collection of non-obvious gotchas and defaults worth overriding when
building PsychoPy experiments, learned on real projects rather than found in
the docs. Each entry: what to do, why the default bites, how to tell if it
applies. Add a new entry whenever one turns up -- don't let the lesson live
only in one project's git history.

## Contents

0. [Validation, validation, validation](#0-validation-validation-validation) -- the rule every section answers to
1. [Rendering](#1-rendering)
   - [Always pass `interpolate=True` to `ImageStim`](#always-pass-interpolatetrue-to-imagestim)
2. [Layout in "height" units](#2-layout-in-height-units)
   - [`TextStim` needs an explicit `wrapWidth`](#textstim-needs-an-explicit-wrapwidth-or-it-will-eventually-clip)
   - [RTL text that barely wraps puts the first word last](#rtl-text-that-barely-needs-to-auto-wrap-can-put-the-first-word-on-the-last-line)
3. [The operator's setup screen: Qt inside a PsychoPy process](#3-the-operators-setup-screen-qt-inside-a-psychopy-process)
4. [The operator's setup screen: architecture that stays testable](#4-the-operators-setup-screen-architecture-that-stays-testable)
5. [Recording streams that don't lie](#5-recording-streams-that-dont-lie)
   - [Never advertise an LSL outlet before its source is open](#never-advertise-an-lsl-outlet-before-its-source-is-open)
   - [Watch every stream while the session runs](#watch-every-stream-while-the-session-runs)
6. [Stopping a session safely](#6-stopping-a-session-safely)
   - [Quit = hold Ctrl+C for 3 seconds](#quit--hold-ctrlc-for-3-seconds)
   - [Every stop saves everything](#every-stop-saves-everything)
7. [When a session dies: capture the evidence before you need it](#7-when-a-session-dies-capture-the-evidence-before-you-need-it)
8. [Autopilot: every experiment can run itself](#8-autopilot-every-experiment-can-run-itself)
   - [8.1 What it is, and why not SendInput](#81-what-it-is-and-why-not-sendinput)
   - [8.2 Two files: a generic driver, a thin per-experiment runner](#82-two-files-a-generic-driver-a-thin-per-experiment-runner)
   - [8.3 Modes](#83-modes)
   - [8.4 Stress test first: is this machine fit today?](#84-stress-test-first-is-this-machine-fit-today)
   - [8.5 Machine health during the run](#85-machine-health-during-the-run)
   - [8.6 The validation verdict](#86-the-validation-verdict)
   - [8.7 Prove every check can fail](#87-prove-every-check-can-fail)
   - [8.8 Gotchas](#88-gotchas)
   - [8.9 Checklist: adding autopilot to a new experiment](#89-checklist-adding-autopilot-to-a-new-experiment)
9. [Lab machines](#9-lab-machines)
10. [Reference implementations](#10-reference-implementations)

## 0. Validation, validation, validation

The standing rule of this lab, defined in full in **data-collection-reliability**
(which also owns how a session is run, checked and triaged). For whoever writes the
code, it comes down to:

1. **Every check must be shown to fail.** Reintroduce the bug, unplug the device, kill
   the process -- and watch the check go red. A check that has never been red is
   unverified. (On the Emotions console a green test passed over three broken slots;
   on the fault-capture pass two of eight "obvious" crash recipes tested something
   else.)
2. **Missing evidence is a failure, not a pass.** A missing file, a stream with 0
   samples, a log with no clean-exit line all mean *fail*. A check that cannot run
   reports `SKIP` with the reason, never `PASS`. (Not the same as a *quiet signal*: a
   silent participant still produces audio samples. Judge whether samples arrive,
   never how loud they are -- section 5.)
3. **Exit codes carry the verdict.** Any automated run returns non-zero when any
   check fails, so a script, CI or a human skimming can't mistake red for green.
4. **Report the gap honestly.** If something was not tested, say so in the verdict
   (`SKIP: no EMG hardware`), don't omit the row.
5. **Build for all three points**: before the session (pre-flight, the stress test),
   during it (fault capture, the stream watch, the watchdog), after it (the verdict,
   section 8.6). The verdict is evidence for a person to review, never a decision the
   code makes alone.

## 1. Rendering

### Always pass `interpolate=True` to `ImageStim`

PsychoPy's `ImageStim` defaults to `interpolate=False` -- nearest-neighbor
sampling whenever the image is scaled to its on-screen size. That reads as
blocky, aliased edges, most visible on diagonal lines and on text baked into
an image, even though the same PNG looks sharp in any normal image viewer
(which does smooth resampling by default). The fix is one keyword on every
`ImageStim` call:

```python
visual.ImageStim(win, image=path, units="height", size=size, pos=pos,
                 interpolate=True)
```

**When it applies**: any `ImageStim`, always -- there's no real case where the
blocky default looks better. Check every call site in a codebase at once
(`grep -rn "ImageStim("`), since it's easy to add a new image-drawing call
later and forget the flag.

**What it won't fix**: if the source image is much lower-resolution than the
area it's stretched to fill, no filtering recovers detail that isn't in the
file -- that needs a higher-resolution source export, not a code change. Also
worth ruling out separately: a small preview/dev window (e.g. 1440x900)
displays everything at fewer pixels than a real fullscreen session at native
monitor resolution, which can look "soft" for a reason that has nothing to do
with `interpolate`.

## 2. Layout in "height" units

With `units="height"`, the window's vertical extent is always exactly
`[-0.5, 0.5]`; the horizontal extent is `[-0.5*aspect, 0.5*aspect]`, where
`aspect = win.size[0] / win.size[1]`. Two things follow from that:

- **A dev/preview window and a real fullscreen session usually have different
  aspect ratios** (e.g. a 1440x900 dev window is 1.6, a 1920x1080 fullscreen
  session is 1.778), so a position or size hand-tuned in one may sit slightly
  differently in the other. For most layout work this is a small enough
  difference to ignore and hand-tune with static numbers; only compute a
  size/position from `win.size` at runtime when getting it wrong would
  actually clip something (see the next entry).
- **`ImageStim(size=...)` accepts `None` in either slot**, not just the one
  you've used before: `(None, height)` fixes height and derives width from
  the image's own aspect ratio; `(width, None)` does the reverse. Use
  whichever dimension is actually the constraint -- e.g. fit a narrow column
  by fixing width, not height, even if every other image in the file happens
  to fix height.

### `TextStim` needs an explicit `wrapWidth`, or it will eventually clip

`TextStim`'s default `wrapWidth` is not reliably "the whole window" -- and
even when a wrapWidth IS set, a value that was fine for one string can still
run text past the screen edge once the content changes (a longer phrase, a
different language, an anchor point that isn't centered). Two known failure
modes, both real bugs hit on the same project:

- A **centered** status text with no `wrapWidth` at all: fine for early
  short strings, then Hebrew arrived with longer lines and it wrapped in the
  wrong place. Fix: compute `wrapWidth = (win.size[0] / win.size[1]) * 0.95`
  once, at window-creation time, and give every such TextStim that value.
- A **side-anchored** text (`pos=(x, 0)` with `alignText="left"` or
  `"right"`, not centered) with no `wrapWidth`: the available room isn't the
  whole screen, it's whatever is left between the anchor and the nearer
  edge. A phrase that fits in English can still run off the edge in a
  language whose translation is longer. Fix: `wrapWidth = half_width -
  abs(anchor_x) - margin`, computed the same way, anchored on the correct
  side.

**How to tell it applies**: any `TextStim` whose content can change length
(translations, participant-driven values, anything not a fixed short label)
and whose position isn't safely centered with a huge margin on all sides.

### RTL text that barely needs to auto-wrap can put the first word on the LAST line

Found live via a participant-facing screenshot, in Hebrew (`languageStyle="Arabic"`,
the RTL/bidi reshaping path). A paragraph measured only slightly wider than
`wrapWidth` -- 1.604 vs. 1.520, about 5% over -- and PsychoPy auto-wrapped it
into two lines. The overflow word should have led the second line (RTL still
reads top-to-bottom, first line first). Instead it landed alone on a THIRD
line, after the rest of the sentence: the paragraph's first logical word
displayed dead last. Not a clipping bug, not a grammar bug -- a bidi
line-assignment bug in the wrap itself, and it can be genuinely hard to
notice by eye at a glance, especially skimming a language you don't read
fluently.

**Fix**: don't let PsychoPy auto-wrap RTL text at all, close to the limit or
not. Measure every line (split on your own explicit `\n`s) with a throwaway
`TextStim` and `.boundingBox`, and hand-insert a `\n` at a natural clause
boundary (comma, colon, sentence end) for any line whose unwrapped width
exceeds `wrapWidth` -- verifying both resulting pieces also fit, recursing
into a 3-way or 4-way split if one piece is still too long:

```python
t = visual.TextStim(win, "", height=height, wrapWidth=10.0, languageStyle=lang_style)
def width(s):
    t.text = s; t.draw(); win.flip()
    return t.boundingBox[0] / win.size[1]
```

**How to tell it applies**: any RTL text file, checked by scanning every
line's measured width against its real `wrapWidth` -- not by eyeballing which
lines "look long", since a 5%-over line is exactly as likely to trigger this
as a 50%-over one, and a native-fluency skim can miss the symptom (a single
stranded word) even when looking right at it. Re-run the scan after ANY edit
to the text (a shorter/longer translation, a config value, a placeholder
substitution can each push a line from safely-under to just-over).

## 3. The operator's setup screen: Qt inside a PsychoPy process

Every experiment eventually grows a launcher window — who is in the room, which
condition, which blocks run. `psychopy.gui.DlgFromDict` gets you six auto-generated
fields; the moment you want switches, live-derived consequences, or a layout, you
are writing Qt by hand *inside a process that also runs PsychoPy*. These are the
traps in that specific situation, learned building the Emotions setup console.

### Never construct your own `QApplication` — borrow PsychoPy's

`psychopy/gui/qtgui.py` caches `qtapp = QApplication.instance()` **at module import
time**, and `ensureQtApp()` only builds one `if qtapp is None`. Constructing a second
`QApplication` does **not** raise: it silently becomes `QApplication.instance()` and
orphans the first. `Dlg.__init__` then reads `qtapp.screens()` off an object that
doesn't own your widgets.

The bug is order-dependent, which is why it hides: if you build your app before
`psychopy.gui` is imported, the cache picks yours up and everything works. Import
`psychopy.gui` first and you get two apps, no error, and a failure two dialogs later.

```python
def _ensure_qt_app():
    from psychopy.gui import qtgui
    qtgui.ensureQtApp()      # order-independent, sets the 'Fusion' style psychopy
    return qtgui.qtapp       # expects, and keeps the only strong ref in sys.modules
```

Three rules follow, all for the same reason — **PsychoPy will reuse this app for its
own dialogs later in the session** (a "recorder running?" gate, a LabRecorder prompt):

- **`QDialog.exec()`, never `app.exec()`.** A nested modal loop ends on
  accept/reject and leaves the application object alone. Stopping `app.exec()` needs
  `app.quit()`, which leaves the shared app in a quit state. This is exactly what
  psychopy's own `Dlg.exec_()` does.
- **Never `app.quit()`, `del app`, or rebind the cached global.** If the app is
  collected, the later dialog hits `qtapp.screens()` on a dead C++ object.
- **`dlg.setStyleSheet()`, never `app.setStyleSheet()`.** PsychoPy's gates are bare
  `QLabel`/`QLineEdit` with no styling of their own, so an app-wide dark sheet bleeds
  in and renders them dark-on-dark — unreadable, on the screen that asks whether the
  recorder is running.

**How to tell it applies**: any Qt window in a process that also imports
`psychopy.gui`. Assert it rather than eyeballing — see the offscreen smoke entry.

### Every Qt slot needs `*_`, and only a signal-driven test can prove it

Qt passes arguments to slots: `clicked` sends a `checked` **bool**, `textChanged`
sends the new **str**. So `def _on_begin(self)` raises
`TypeError: takes 1 positional argument but 2 were given` the instant a real button
is pressed.

The vicious part is that a test which *calls* the handler cannot see this:

```python
dlg._on_begin()        # passes -- one argument, `self`
dlg.begin_btn.click()  # raises -- Qt adds the bool, as it does in the real window
```

On the Emotions console this shipped three broken slots behind a green test that
called them directly; they were found by running the launcher by hand. The same
defect hides in signal-to-signal wiring: `button.clicked.connect(self.changed.emit)`
feeds a bool into a zero-argument `pyqtSignal()`, so wrap it —
`clicked.connect(lambda _=False: self.changed.emit())`.

**The rule**: give every slot `*_`, and make the test drive widgets the way a human
does — `.click()`, `.setText()`, synthesised `QMouseEvent` — never by calling the
handler.

**Gotcha inside the test itself**: `setText()` with an *unchanged* value emits
nothing, so seeding a state that way silently skips the refresh and leaves stale
values on screen. Render explicitly, drive signals separately.

### An unhandled exception in a slot kills the whole process

Not a caught error, not a traceback you can recover from: PyQt6 tears the process
down from *inside* `QDialog.exec()`. Nothing after `exec()` runs — no return value,
no cleanup, no "cancelled" message. To the operator it looks like the launcher dying
at random while they type.

So wrap every slot, and record failures so a test can assert none fired:

```python
def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:                       # noqa: BLE001
            _SLOT_FAILURES.append(traceback.format_exc())
            traceback.print_exc()
    return wrapper
```

Corollary: **never `sys.exit()` inside a slot.** `SystemExit` from a slot kills the
process from within `exec()`, so the caller never prints anything. Set a result
attribute, call `reject()`, and put the exit *after* `exec()` returns.

**Live-preview handlers are the highest-risk slot**, because they run on every
keystroke against half-typed input. Anything doing `int(text)` on the way to a
derived value (an id parity, a formatted path) raises on `""`, `"D"`, `"abc"` — guard
it and fall back to a dim placeholder.

### Resolve font families in Python, not in a QSS `font-family` list

A QSS `font-family: "IBM Plex Mono", Menlo, monospace` looks like CSS and behaves
worse: each *missing* family costs a ~230 ms `qt.qpa.fonts: Populating font family
aliases` pass printed to stderr — on the operator's live console — and a missing mono
family can resolve to a **proportional** system font, silently breaking any aligned
column you were relying on.

```python
def _family(*candidates):
    have = set(QtGui.QFontDatabase.families())   # needs a QApplication first
    return next((c for c in candidates if c in have), candidates[-1])
```

Interpolate the winner into the stylesheet. **How to tell it applies**: check the
font is actually installed rather than assuming — a designed mock-up will happily
name a font nobody on the lab PC has.

## 4. The operator's setup screen: architecture that stays testable

The GUI traps above cost debugging time. These cost *data*, so they matter more.

### Split the rules out of the window, or their edge cases never get tested

A dialog you can only test by clicking through it is a dialog whose edge cases never
get tested. Put every decision — what a switch means, where a "pilot" run writes,
whether a screen state is legal — in a plain module beside the validation function,
and leave the GUI file holding layout, colour, and wiring only.

The payoff is a `--selftest` that runs the rules in a fraction of a second on any
machine with no display, and a GUI file that needs no unit tests *because it contains
no decisions*. The test: if you are writing an `if` about the experiment inside the
window class, it belongs one file over.

### Store the operator's INTENT, not the post-rule effective value

**The one on this list that causes a scientific error rather than a crash.**

If a design rule can force a setting off (a counterbalancing rule that skips a phase
for even-numbered participants, say), the window must store what the operator
*asked for* and let the existing rule function apply the forcing downstream.

Why it matters: validation code often distinguishes *"off by design"* from *"off
because someone left a test setting behind"* — and it distinguishes them by reading
the same toggle dict. Write the already-forced-off value into that dict and the
setting silently migrates from the first category to the second, so the "STOP, you
forgot to turn this back on" alarm fires on a phase the **design** deliberately cut.
It then fires on every even participant, always wrongly, and the operator learns to
ignore the one warning meant to stop a session.

The stored value is not *"will this run"* — the rule function already owns that. It
is *"was this on purpose."* In the widget, keep intent and drawn-state separate, so
correcting a mistyped id restores the switch the operator originally set.

### Override config *before* you resolve, and make the override idempotent

If the GUI writes runtime overrides into a config module, ordering is load-bearing:
mutate first, *then* call the function that derives the session from that config.
Reverse them and the derived values describe the pre-override state.

Two details worth copying:

- **Write every key**, not just the changed ones. Downstream code that does
  `CONFIG.BLOCKS[name]` raises `KeyError` mid-session on a partial dict — a crash 40
  minutes in, not a warning at launch. Validate key-completeness up front.
- **Derive paths from an import-time snapshot**, never from the current value.
  `DATA_ROOT = DATA_ROOT / "Pilot"` applied twice yields `Pilot/Pilot`. Snapshot the
  original at import, derive from that, and raise if the live value is neither the
  base nor the expected override — so a second writer fails loudly instead of nesting.

### A validity check that reads a module constant goes stale the moment a GUI can override

Config modules often self-check at import (`if RUN_BLOCKS and not enabled_blocks()`).
Those checks read the **constants**, and they run **once, at import** — so they are
structurally blind to anything a window changes at runtime. The guard doesn't fail
loudly; it just quietly stops guarding.

When you make a setting GUI-settable, grep for every existing check that reads it and
re-home them into the GUI's own validation. Don't re-run the whole config validator
instead: it re-checks unrelated invariants the operator can't fix from that screen.

### Smoke-test the entire window with no display

`QT_QPA_PLATFORM=offscreen` builds the real widget tree, fires real signals, and
needs no monitor — so this belongs in the same breath as a unit test, not in the
"needs the lab PC" pile:

```bash
QT_QPA_PLATFORM=offscreen python setup_console.py --smoke
```

Have `--smoke` drive the window across a spread of states (blank, half-typed input,
each condition, each toggle combination that changes what runs), exercise every
widget through its **signal**, and exit non-zero if any slot recorded a failure. Add
assertions for the `QApplication`-identity and stylesheet-scope rules from the
section above; on the Emotions console this reduced "needs a real display" from three
checks to exactly one — **window stacking order**, i.e. whether the PsychoPy window
opens *in front* of the launcher. That genuinely cannot be tested headlessly; nothing
else on the list needed a monitor.

**Prove the test can fail.** Reintroduce the bug deliberately and confirm it goes
red. A smoke test that calls handlers instead of clicking buttons passes while the
window is broken — verified, on this exact console.

## 5. Recording streams that don't lie

### Never advertise an LSL outlet before its source is open

Found on voiceless_they, 2026-10-22: the HyperX mic was unplugged, the dB meter
logged `could not open microphone`, and `Audio_Mic` was **still listed in
LabRecorder**. The code created the audio outlet first ("so LabRecorder lists it")
and opened the mic second. The outlet lives on regardless of whether anything ever
pushes into it, so the operator ticks a healthy-looking stream that records **0
samples** -- found only when the XDF is opened, after the participant has gone.

**Fix**: open the source, then create the outlet, and only if the source opened. A
failed device must mean *no stream*, plus a loud console line, plus the failure in
`session_info.json`:

```python
mic_open = db.start()
if mic_open and audio_lsl_wanted:
    db.audio_outlet = make_audio_outlet(...)
elif audio_lsl_wanted:
    print("[MIC] WARNING: microphone did not open - NO Audio_Mic LSL stream")
```

A missing stream is caught at a glance in LabRecorder; an empty one is not. The same
rule applies to every device-backed outlet (camera frames, eye tracker, a
response box): **the outlet's existence must mean the device is delivering.**

The camera had the same bug, in a harder form: its outlet must exist before LabRecorder
starts, but the camera opens in the background (~12 s) and can fail after that. Fix:
when `arm()` finds the camera never opened, **withdraw** the outlet (drop the last
reference to the `StreamOutlet`) and print it. A stream that disappears is still far
easier to notice than one that stays empty.

**The validator must not trust the outlet flag either.** The first version of the
verdict checked `audio_lsl_active` and passed the very session that had the dead mic.
Check the outlet **and** the device behind it (`mic_device` set, `mic_error` empty).

**How to validate it**: the post-session check "every expected stream exists AND
has > 0 samples" (section 8.6). Prove it red by running once with the device
unplugged.

### Watch every stream while the session runs

The reverse case: a device that opens and then dies mid-session (mic cable pulled at
minute 20, the DAU dropping off Wi-Fi) leaves an outlet that simply stops receiving.
Nothing crashes, so nothing else notices. Every experiment runs a **stream watch**
for the whole session:

| gap (no samples arriving) | action |
|---|---|
| > 2 s | **flag**: console line, `stream_gap_detected` / `stream_gap` events in the log (stream, length), a row in the verdict. The session **continues** -- a flag never quits. |
| > 10 s | **safe stop**: end the session the same way a quit does (section 6), status `stopped_stream_lost`, naming the stream. Ten seconds of a dead stream means the rest of the session would be unusable anyway. |

Both limits live in the config, per stream.

**Watch sample arrival, never signal level.** A silent participant is not a dead
mic: the mic still delivers a block of (near-zero) samples every ~23 ms. The watch
counts *samples arrived*, so silence never flags and never stops a session. The only
thing that trips it is the device or the stream actually going away.

What to watch, and how:

- **Our own outlets** (mic, video frames): a counter that grows on arrival (audio
  blocks processed, frames written); the watch compares counts between checks.
- **External streams** (`XtrodesEMG`, `XtrodesIMU` from the recorder): open a `pylsl`
  inlet per stream in a background thread that only counts the samples `pull_chunk`
  returns.
- **Never on the frame path.** Inlet threads only *count*; the main loop calls
  `watch.check()` between flips (the same place it checks the quit gesture), which
  logs and, past the stop limit, raises `StreamLost` on the main thread. A thread must
  never close the window or the files itself.
- **Count where every sample passes.** Put the increment in the one function every
  block goes through, not in the device callback: the first version counted in the
  callback, and the test harness, which feeds blocks without it, was promptly "lost"
  after 10 s.
- Arm each stream as *just seen* when it is registered (after the camera arms), so a
  stream dead from the start is also lost after `stop_s`. Streams that are not there at
  all (EMG off the network, LSL off) are listed as **not watched**, with the reason, and
  the verdict decides whether that is a FAIL.
- Log the events as instant markers (`stream_gap_detected` at the flag, `stream_gap`
  with `gap_duration_s` when samples resume, `stream_lost` at the stop), and add the
  names to the project's marker vocabulary.

**How to validate it**: pause the EMG recorder for 5 s → one flag, the session goes
on. Pause it for 11 s → safe stop, all files intact, status `stopped_stream_lost`.
Sit silent for a whole block → nothing.

## 6. Stopping a session safely

### Quit = hold Ctrl+C for 3 seconds

Single-key quits (Escape) end sessions by accident: a brush of the keyboard, a
participant reaching for a tissue. And under autopilot, Escape cannot work at all,
because the autopilot owns the keyboard API (section 8.8). So in **every**
experiment, autopilot or not, the quit gesture is: **hold Ctrl+C in the PsychoPy
window for 3 seconds.** A single key does nothing.

Read it from **pyglet's key state**, not from PsychoPy's keyboard API. That one
choice makes it immune to the autopilot (which patches only the PsychoPy APIs) and
gives "is it still held" directly:

```python
from pyglet.window import key
held = key.KeyStateHandler()
win.winHandle.push_handlers(held)          # once, after the window opens

def quit_held(state, now, hold_s=3.0):     # call once per frame, between flips
    down = (held[key.LCTRL] or held[key.RCTRL]) and held[key.C]
    if not down:
        state["since"] = None
        return False
    state["since"] = state["since"] or now
    return now - state["since"] >= hold_s
```

- Print a console countdown while it is held (`quit: hold 2 s more`), so the operator
  knows it is working. Show nothing to the participant.
- Inside the PsychoPy window, Ctrl+C is just two keys -- not a signal. **Ctrl+C in
  the console** is still the emergency stop: instant, no hold, exits via
  `KeyboardInterrupt` (or `0xC000013A` if uncaught; exit codes in data-collection-reliability, stage 7).
- Every polling loop must call it, including waits that poll no keys (fixations, a
  fixed-duration rest). Otherwise the quit dead-zones exactly where an operator most
  wants to stop.
- **Verify on each rig** that pyglet's key state updates while PsychoPy's keyboard
  backend (psychtoolbox) is in use: `win.flip()` dispatches the window's events, but
  check it.
- **Fallback:** if the window has no pyglet `winHandle` (another backend, a mocked
  window in tests), fall back to the old single quit key **with a warning at start**,
  rather than leaving the session with no way to quit.
- Count the countdown down with `ceil` (3, 2, 1). Rounding prints "3 s more" twice --
  caught by the test, not by eye.

**How to validate it**: hold for 2.9 s → nothing. Hold 3 s → quit. Tap Escape →
nothing. Hold during a fixation → quit. Hold during an autopilot run → quit.

### Every stop saves everything

A quit, a stream-loss safe stop and a normal end take the **same** exit path: mark
the open events cancelled, write progress (`status` = `aborted` / `stopped_stream_lost`
/ `completed`, last event, block, trial), flush and close every log, stop the camera
(so the mp4 is finalised), close LSL outlets, write the fault-capture clean-exit line
last. One path means one thing to test. The verdict then runs on whatever was saved.

## 7. When a session dies: capture the evidence *before* you need it

A long session that dies at minute 49 is investigated from whatever was written to
disk. If nothing was, you get a day of guessing, and Windows will usually not help:
on one lab PC a real access violation left **no** Event 1000, no WER report and no
dump. The Emotions experiment learned this on 2026-10-19, when two rigs failed in
the same block for two different reasons and neither left evidence. Arm all of the
below for every real session; none of it touches the frame path.

### Two layers, because each one is blind where the other sees

| layer | runs | catches | blind to |
|---|---|---|---|
| **in-process**: `<base>.faults` | inside the experiment | native-crash Python stack (`faulthandler`, `all_threads=True`); dead background threads (`threading.excepthook`); errors in `__del__`/GC (`sys.unraisablehook`); a clean-exit line written last | how the process ended; C stacks; anything after it is killed; machine-wide stalls |
| **out-of-process**: a sentinel | a separate, detached python | exit code; "Not Responding" (`IsHungAppWindow`, polled 1 s); native minidumps of every thread while hung; per-second CPU/disk/memory (`typeperf`); the Windows event log for the session; a one-line verdict | Python-level stacks |

Start the sentinel with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` (try
`| CREATE_BREAKAWAY_FROM_JOB` first, fall back if the job refuses) and stdio on
`DEVNULL`. Then it survives Ctrl+C, a closed console, or the experiment being
killed. Open a handle to the experiment at startup and `WaitForSingleObject` on
it, so the exit is never missed. Tee stdout/stderr into the session folder as well:
the console is otherwise the only record of what the operator saw.

### Reading the evidence lives elsewhere

The sentinel's VERDICT maps exit codes to endings. The calibrated exit-code table, the
Event 1001/1002 signatures, how to read a hang dump with `cdb`, and the traps in
reading `.faults` (it logs exceptions that were then handled; an operator abort is
not a crash) are in **data-collection-reliability**, stage 7, so the person triaging
a failed session finds them in one place. Build the sentinel against that table.

### Gotchas that cost a test cycle each

- **`ctypes.string_at(0)` is not a crash test**: ctypes catches the fault and raises
  `OSError` (exit 1). **`faulthandler._sigsegv()` is not one either** on Windows: it
  only calls `raise(SIGSEGV)` (exit 3). A real `0xC0000005` needs a fault outside
  ctypes' guard, e.g. `kernel32.CreateThread(None, 0, c_void_p(0), None, 0, None)`.
- **A child of a shell that ignores Ctrl+C inherits the ignore flag** and never sees
  `CTRL_C_EVENT`. A test that sends one must call
  `kernel32.SetConsoleCtrlHandler(None, False)` in the child first.
- **`IsHungAppWindow` needs ~5 s without message pumping** before it reports hung.
  `win.flip()` pumps, so a healthy PsychoPy loop never trips it. Arm the dump at
  ≥ 25 s hung. Writing a 0.5 MB `MiniDumpNormal | WithThreadInfo |
  WithUnloadedModules | WithHandleData` dump paused the target 0.6–1.5 s.
- **`typeperf \Process(python*)\...` expands the wildcard once, at start.**
  Processes started later are not logged. Start it after the processes you care
  about. A killed `typeperf` keeps every line it wrote.
- **Python block-buffers stdout when it is not a terminal** (pipes, IDE panels, a
  tee). `stream.reconfigure(line_buffering=True)` on both streams, first thing, or
  the console lags the session by minutes.
- **An operator abort must be distinguishable from a crash in the files.**
  voiceless_they, 2026-10-22: a quit gave exit `0` and a clean `.faults`; only the
  progress `end_reason=aborted` and the `abort` event said it was a quit. Write both.

### Prove it before trusting it

Run every ending on purpose before a pilot and check the files say what happened:
clean, freeze + kill, real segfault, abort, background-thread exception, freeze
closed via "Close the program", Ctrl+C, console closed. On the first pass, two of
the eight "obvious" recipes silently tested something else: the segfault (twice)
and Ctrl+C.


## 8. Autopilot: every experiment can run itself

**Recommended for every experiment built with this skill -- and in this lab we always
build it.** A human clicking through a 50-minute session to see whether it survives
trial 16 is slow, unrepeatable and tests the human as much as the code. The
autopilot first checks the machine is fit (8.4), then drives the *real* session --
same code path, same stimuli, same recording, same fault capture -- with nobody at
the keyboard, measures the machine while it does, and ends in a pass/fail verdict.

### 8.1 What it is, and why not SendInput

`psychopy_autopilot.py` patches PsychoPy's key APIs (`event.getKeys`,
`event.waitKeys`, `hardware.keyboard.Keyboard.getKeys/waitKeys`) so a script that
polls for keys gets synthetic presses. The key is inferred from the `keyList` the
script itself asks for: a continue key on instruction screens, a random in-range
digit then a confirm on rating screens. Nothing about any experiment is hard-coded.

Why not OS-level injection (SendInput, pyautogui): it lands only in the window that
has focus, which a fullscreen PsychoPy window fights over, and it cannot be
attributed to one physical keyboard. Patching at the PsychoPy boundary is
focus-independent, works windowed or fullscreen, and exercises the script's real
polling path rather than a mock of it.

What you get for free, because every poll flows through one place:

- `autopilot_<ts>_<tag>.jsonl` -- one JSON line per armed key and press, flushed per
  write: the last lines name the screen a dead run died on.
- a **watchdog** that dumps every thread's stack into the session's `.faults` when
  the script stops polling for `hang_timeout` seconds: a freeze caught in the act.

### 8.2 Two files: a generic driver, a thin per-experiment runner

| file | owns | never contains |
|---|---|---|
| `psychopy_autopilot.py` (generic, vendored unchanged into each project) | key patching, key policy, trace, watchdog, `--selftest` | anything about one experiment |
| `run_autopilot_session.py` (per experiment) | skipping the setup GUI, the throwaway output folder, mode flags, the hardware gate, calling the experiment's real `main()` | key logic, stimulus logic |

The runner's rules:

1. **Skip the setup window**, never click it: pass the experiment the same argv the
   window would have produced (`--participant … --session …`). Nothing can click a
   dialog when nobody is there.
2. **Throwaway identity**: participant `AUTOPILOT` (or `99`), pilot folder, and
   `notes="automated unattended run -- NOT REAL DATA"` in `session_info.json`. An
   autopilot run must be impossible to mistake for data.
3. **Stress test first** (8.4). A machine that fails it is not used for the run.
4. **Call the real `main()`**, in-process, so the real fault capture arms itself
   exactly as in a live session.
5. **A human answers the hardware gate, before `engage()`.** The autopilot must never
   vouch for hardware it can't see (recorder streaming, LabRecorder recording).
6. **End with the verdict** (8.6) and return its exit code.

### 8.3 Modes

| flag | what runs | use |
|---|---|---|
| *(none)* | stress test, then full session, real pacing, no LSL/camera/mic | does the task itself survive end to end? |
| `--quick` | skip calibration + practice | harness check |
| `--fast` | presses after 50–150 ms instead of human pace | smoke test; **not** valid for timing or crash-repro |
| `--windowed` | a window instead of fullscreen | while you keep working; **not** valid for frame timing |
| `--hardware` | LSL, mic, camera, fullscreen, human gate first | full rehearsal on the real rig |
| `--stress-only` | the stress test (8.4) and nothing else | is this machine fit today? |
| `--baseline` | the stress test, saved as this machine's new baseline | first run on a machine, or after a hardware/driver change |
| `--seed N` | reproducible key choices and delays | rerun the exact same run |

**A crash-repro run must match the session it reproduces**: full counts, real
pacing, camera on, fullscreen. `--fast`/`--quick`/`--windowed` change exactly the
timing and load a crash may depend on.

### 8.4 Stress test first: is this machine fit today?

The first thing every autopilot run does, before any session screen: about 60 s of
synthetic load that looks like the session -- the heaviest screen drawn every frame,
fullscreen, with the camera and LSL outlets running as the config has them. It
measures the same metrics as 8.5 and compares them with **this machine's
baseline**.

**Thresholds come from the machine, not from a guess.** Specs alone can't say how
many frames a rig will drop; only a measurement can. So:

1. On each lab machine, run `--baseline` once, freshly restarted, nothing else open.
   It writes `machine_baselines/<HOSTNAME>.json`: the fingerprint (section 9) plus
   the stress-test numbers.
2. Every later stress test is judged **against that file**.
3. Re-baseline after a hardware change, a GPU-driver update, or a Windows feature
   update -- the fingerprint check below makes that visible.

Verdict of the stress test:

| result | meaning | action |
|---|---|---|
| `FIT` | within the baseline's margins | run |
| `DEGRADED` | clearly worse than its own baseline (provisional: dropped frames > 2× baseline, or CPU/GPU p95 > baseline + 20 points, or free RAM < half of baseline) | **restart the computer**, then run the stress test again |
| `UNFIT` | an absolute floor broken: free RAM < 1 GB, or > 1 % dropped frames | do not run a participant on it |
| `NO BASELINE` | no `<HOSTNAME>.json` yet | run `--baseline` first; the numbers are reported but not judged |

Also report, without judging: **uptime** (a long uptime is the usual suspect when a
machine is `DEGRADED`), the power plan (anything other than *High performance* is a
classic dropped-frame cause), and a **fingerprint mismatch** (different GPU driver,
refresh rate or display than the baseline was measured on → re-baseline).

The margins above are provisional. Tighten or loosen them once two or three
baselines and real sessions exist per machine.

Learned on the first real run (voiceless_they, 2026-10-25), each one a wrong verdict:

- **The stress load must be the experiment's own code.** The first version drew a
  hand-made screen (wrong pronoun, invented layout) in its own loop. It neither looked
  like the session nor loaded the machine like it, and its loop had **no quit check**,
  so holding Ctrl+C did nothing. Drive the real presenter on real trials
  (`presenter.run_condition(...)`); the quit gesture, layout and load then come free.
- **Compare like with like, or don't compare.** The baseline was taken with nothing
  running; the stress test before a `--hardware` run had the EMG recorder and
  LabRecorder running. CPU doubled, frames dropped, and a machine restarted 1 h earlier
  was called DEGRADED with "restart the computer". Record which recording programs ran
  (`recording_stack`) and a `stress_version`; when either differs from the baseline the
  verdict is `NO BASELINE` ("not comparable -- re-baseline"), never DEGRADED. Take the
  baseline **under session conditions**: freshly restarted, recorder and LabRecorder
  running. And never advise a restart to a machine that was just restarted.
- **A stress test publishes no LSL streams.** Its camera opened a `Video_Frames`
  outlet that appeared in LabRecorder while the session's own streams did not exist yet.
- **Gate LabRecorder only once the session's streams exist.** A gate shown before
  `main()` asks the operator to tick streams nobody has created (no `Audio_Mic`, no
  markers). Give `main()` a `before_task(streams)` hook, called after every outlet is
  open and before the task window covers the console, and list the streams to tick.

### 8.5 Machine health during the run

The sentinel already logs CPU, disk and memory per second. The autopilot run adds the
two things a stimulus-presentation PC most often runs out of -- GPU and frame budget
-- and judges all of it against the baseline, the same as 8.4.

| metric | source | verified on lab PC? |
|---|---|---|
| CPU % total and per python process | `typeperf \Processor(_Total)\% Processor Time`, `\Process(python*)\% Processor Time` | yes (sentinel) |
| available memory, python working set | `\Memory\Available MBytes`, `\Process(python*)\Working Set` | yes (sentinel) |
| disk queue / write rate | `\PhysicalDisk(_Total)\Avg. Disk Queue Length`, `Disk Write Bytes/sec` | yes (sentinel) |
| GPU 3D engine utilisation | `\GPU Engine(*engtype_3D)\Utilization Percentage` | counter exists on LAB006_NEW (2026-10-22); values not yet checked |
| GPU memory | `\GPU Adapter Memory(*)\Dedicated Usage`, `\Shared Usage` | counter exists; values not yet checked |
| frame intervals | PsychoPy `win.recordFrameIntervals = True` → `win.frameIntervals`, `win.nDroppedFrames` | in session_info (`frame_stats`) |
| marker-to-flip latency | marker LSL time vs flip time in `_events.csv` | to build |
| memory growth | python working set, first vs last 5 min | to build (leak check) |

### 8.6 The validation verdict

**Every session ends with a verdict: every autopilot run and every real participant
session.** It is computed from files only, so a crashed experiment still gets one. It
runs in three stages, each merged into `<prefix>.validation.json`:

| stage | run by | adds |
|---|---|---|
| `session_end` | the experiment's `main()`, after everything is written (and after the clean-exit line), printed on the operator console | everything below except the exit code (`SKIP: known only after exit`) |
| `final` | the sentinel, after it writes its VERDICT (~60 s after exit) | exit code, sentinel VERDICT |
| `xdf` | `validate_session.py <session> --xdf <file>`, when Lior hands Claude the XDF | the stage-2 checks below |

So a dead mic is caught on the console before the next participant, not at analysis.

```
PASS  stress test          FIT vs baseline LAB006_NEW (2026-10-22)
PASS  clean exit           .faults ends with "=== clean exit ===", exit code 0
PASS  completed            progress.json status = completed
FAIL  stream Audio_Mic     expected, not published (mic did not open)
PASS  stream Video_Frames  41 812 samples = 41 812 mp4 frames
FLAG  stream gaps          XtrodesEMG: 1 gap of 3.4 s at 00:21:07 (session continued)
SKIP  XDF checks           no .xdf yet -- give it to Claude for stage 2
FAIL  frames               1.9 % dropped (limit from baseline 0.4 %), worst 71 ms
PASS  machine              CPU p95 41 %, GPU p95 22 %, min free RAM 9.1 GB
VERDICT: FAIL (2 failed, 1 flagged, 1 skipped)          exit code 1
```

`FLAG` is information for the reviewer, not a failure (a 3 s stream gap the session
survived). `FAIL` sets the exit code.

The checks, in order:

1. **Machine**: stress-test result (autopilot) or fingerprint (real session).
2. **Process**: exit code 0, `.faults` ends with the clean-exit line, sentinel
   VERDICT clean, no hang dumps.
3. **Completion**: `progress.json` status. An autopilot run must be `completed`
   (nobody quits it on purpose); a real session reports `aborted` /
   `stopped_stream_lost` as-is for the reviewer.
4. **Files**: every expected output exists and is non-empty (events, trials,
   session_info, video, frame index).
5. **Streams**: every expected stream was published and pushed > 0 samples (section
   5); every `stream_gap` event listed.
6. **Trial count**: trials logged = trials in the trial-order file.
7. **Timing**: frame and latency numbers against the baseline.
8. **Machine during the run**: CPU/GPU/memory against the baseline.

**Numbers nobody judged are `SKIP`, never `PASS`.** With no baseline, the frame and
machine rows show their numbers and say "not judged: no baseline" -- only the
absolute floors (UNFIT) still apply. The first version printed `PASS` next to a
number it had compared with nothing.

**Stage 2: the XDF, validated by Claude.** LabRecorder writes the `.xdf`; Lior hands
it to Claude after the session for: every expected stream present with > 0 samples
and no gaps beyond the flags; mp4 frame count = `Video_Frames` samples; markers in
`_events.csv` = markers in the XDF; `lsl_json_marker_intervals.py` → 0 lifecycle
problems. **The XDF must land in the participant's own folder** (the same
`sub-<id>/` as every other file of that session): the setup window shows that path
for the operator to paste into LabRecorder, and stage 2 flags an XDF found anywhere
else.

### 8.7 Prove every check can fail

Before trusting the verdict, make each check go red on purpose, once per experiment
(and again after any change to the validator):

| check | how to make it fail |
|---|---|
| stress test | run it with a second fullscreen video or a CPU burner alongside → `DEGRADED` |
| clean exit | kill the run from Task Manager mid-session |
| completion | hold Ctrl+C for 3 s during an autopilot run |
| stream published | unplug the mic before the start |
| stream gap flag | pause the EMG recorder for 5 s |
| stream-loss safe stop | pause the EMG recorder for 11 s |
| silence is not a gap | sit silent through a whole block → **no** flag |
| frame/mp4 alignment | truncate a copy of the mp4 and validate against it |
| markers | delete marker rows from a copy of `_events.csv` |
| XDF location | save a test XDF outside the participant folder |

Record the date each was last seen red in the experiment's checklist. A check with
no date is unverified.

### 8.8 Gotchas

- **The autopilot owns PsychoPy's keyboard API.** The patched `Keyboard.getKeys`
  returns only synthetic keys and never reads the real keyboard, and the policy never
  sends the quit key. That is why the quit gesture (section 6) reads pyglet's key
  state instead: it works under autopilot because nothing patches it.
- **One `.faults` per run.** `engage()` does **not** re-point `faulthandler` when the
  experiment's fault capture already enabled it (`faulthandler.is_enabled()`). When
  the experiment's `FaultCapture.arm()` runs *after* `engage()` (voiceless_they: the
  prefix only exists inside `main()`), it hands its file to the active autopilot
  (`psychopy_autopilot._active.use_faults_file(fh, path)`), so the watchdog's hang
  dumps land in the session's `.faults` too. Two details that bit: re-point
  `faulthandler` to the adopted file *before* closing the autopilot's own (or a crash
  writes to a closed file), and catch write errors in the watchdog (the adopted file
  may already be closed at teardown). Both copies (Emotions, voiceless_they) carry
  this since 2026-10-22; keep them identical.
- **A flip is a sign of life, not only a key poll.** The watchdog first counted only
  key polls. Once the quit gesture moved to pyglet's key state, trials read no keys at
  all, and one clean 22-minute session (exit 0, sentinel CLEAN) got 7 "hang" dumps,
  one per condition block. `engage()` now patches `visual.Window.flip` to call
  `alive()`, and a deliberate wait for a human (the console hardware gate) runs inside
  `with pilot.paused("hardware gate"):`. A real freeze -- no flip, no poll -- is still
  dumped; a test proves both.
- **Escape-only polls send nothing.** A quit check like
  `kb.getKeys(keyList=["escape"])` is filtered out by the policy -- correct, but it
  means a screen that waits on *only* the quit key hangs, and the watchdog will dump
  it after `hang_timeout`. That's the watchdog working, not a bug.
- **Experimenter-only keys get pressed too.** The policy presses whatever the screen
  asks for, including an experimenter-advance key (`return`). Fine for testing; never
  ship a design where pressing it at the wrong time corrupts a session.
- **Ratings are a heuristic.** "Digits plus a confirm key = rating screen". A
  different keying scheme needs a `Policy` subclass, not edits to the driver.
- **`--fast` and `--windowed` invalidate timing checks.** The verdict marks
  frame/latency checks `SKIP (fast/windowed run)` rather than judging them.
- **`os._exit(code)` at the end of the runner**, after flushing: PsychoPy/pyglet
  teardown can hang or crash after the session is safely written, and that must not
  change the verdict's exit code.

### 8.9 Checklist: adding autopilot to a new experiment

1. Vendor `psychopy_autopilot.py` unchanged; run `python psychopy_autopilot.py --selftest`.
2. Make sure the experiment's `main(argv)` accepts every setup-window choice as a
   flag (section 4: the window only produces argv).
3. Implement the hold-Ctrl+C quit (section 6) and the stream watch (section 5).
4. Write `run_autopilot_session.py` (8.2 rules); copy the voiceless_they one.
5. `--baseline` on each machine the experiment will run on (section 9).
6. Run `--quick --fast --windowed` once: the harness works.
7. Run the default mode once: the task survives end to end.
8. Run `--hardware` on the rig: the full verdict passes; Claude validates the XDF.
9. Do 8.7: every check seen red once. Date it in the checklist.
10. Add the autopilot command to the README.

## 9. Lab machines

Each machine an experiment runs on gets a baseline (8.4). The fingerprint is what
the baseline was measured on; a mismatch means re-baseline.

| | LAB006_NEW (lab PC "006") | Voiceless Asus laptop |
|---|---|---|
| model | Gigabyte Z790 UD AX desktop | *to fingerprint* |
| CPU | Intel i7-13700, 16 cores / 24 threads | |
| RAM | 64 GB | |
| GPU | NVIDIA RTX 4080 (driver 32.0.16.1088) **and** Intel UHD 770 (31.0.101.4577), each reporting a 1920×1080 @ 60 Hz display | |
| disks | Samsung 980 PRO 1 TB NVMe, Samsung 980 500 GB NVMe, Crucial BX500 2 TB SATA | |
| OS | Windows 11 Enterprise, build 26300 | |
| power plan | High performance | |
| uptime when fingerprinted | 199.6 h (8.3 days), 2026-10-22 | |
| baseline | `machine_baselines/LAB006_NEW.json` in voiceless_they (2026-10-25) | *not yet run* |

On LAB006_NEW, check which GPU drives the participant display: two adapters each
report an active 1920×1080 display. A PsychoPy window on the integrated UHD 770 is a
dropped-frame risk the RTX 4080 would not have [not yet verified which one it is].
The fingerprint should record the adapter behind the experiment window, not just the
list of adapters.

## 10. Reference implementations

| what | Emotions | voiceless_they |
|---|---|---|
| generic autopilot driver | `experimental_scripts/tools/psychopy_autopilot.py` | `psychopy_autopilot.py` (vendored copy) |
| per-experiment runner | `experimental_scripts/tools/run_autopilot_session.py` | `run_autopilot_session.py` |
| in-process fault capture | `run_emotions_lsl.start_fault_capture()` | `fault_capture.py` (`FaultCapture`) |
| out-of-process sentinel | `experimental_scripts/tools/session_sentinel.py` | `session_sentinel.py` |
| fault-capture tests | `tools/test_fault_capture.py` | `tests/test_fault_capture.py` |
| setup console + pre-flight | Emotions setup console | `setup_console.py`, `setup_dialog.py`, `preflight_checks.py` |
| outlet only after source opens | — | `voiceless_they_experiment_run.py` (mic), `video_recording.VideoRecording.arm` (camera withdrawal) |
| hold-Ctrl+C quit, stream watch | quit only: `emotions_experiment._install_quit_watcher` | `session_guards.py` (`QuitGesture`, `StreamWatch`); wired in `LivePresenter._guard()` |
| fingerprint, stress test, baselines | — | `machine_health.py`, `machine_baselines/<HOST>.json` |
| validation verdict | — | `validate_session.py` (stages `session_end`, `final`, `xdf`) |
| tests (incl. deliberate mutations) | — | `tests/test_session_guards.py`, `test_guards_live.py`, `test_validate_session.py`, `test_machine_health.py`, `test_autopilot.py` |
| not built yet | — | marker-to-flip latency check; memory-growth (leak) check; recording the adapter behind the experiment window |
