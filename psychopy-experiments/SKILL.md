---
name: psychopy-experiments
description: Use when writing, debugging, or reviewing PsychoPy experiment code -- rendering quality (ImageStim/TextStim), layout in height units, RTL/Hebrew text -- and when building the operator-facing setup/launcher GUI -- PyQt6 or tkinter dialogs living in a PsychoPy process, config overrides driven from a window, and how to keep any of it testable with no display. Non-obvious gotchas learned building real experiments. Load before writing or editing stimulus-presentation code, or any operator setup dialog, in PsychoPy.
---

# PsychoPy Experiments

A growing collection of non-obvious gotchas and defaults worth overriding when
building PsychoPy experiments, learned on real projects rather than found in
the docs. Each entry: what to do, why the default bites, how to tell if it
applies. Add a new entry whenever one turns up -- don't let the lesson live
only in one project's git history.

## Rendering

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

## Layout in "height" units

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

## The operator's setup screen: Qt inside a PsychoPy process

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

## The operator's setup screen: architecture that stays testable

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
