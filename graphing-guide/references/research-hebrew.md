# Project layer: Hebrew-word / model evaluation research

Conventions specific to this project, layered on top of the house style in SKILL.md.
Where they conflict, these win — and the deviation goes in the caption.

## Hebrew text is mandatory on every figure (standing rule, 2026-06-01)

Every visualization that references words **displays the actual Hebrew word**. A
`word_id` is not sufficient — not even with a side key or legend. The test is
at-a-glance comprehension: a reader should understand the figure without
cross-referencing a table. Cross-referencing is a tax that gets paid by never being
paid, and then the figure goes into a slide deck and means nothing.

This applies to axis tick labels, direct labels, annotations, and legend entries.

### Rendering

Matplotlib does not apply bidirectional text reordering, so Hebrew must be reversed
before it is drawn:

```python
import figstyle as fs
ax.set_yticklabels([fs.heb(w) for w in words])
```

`fs.heb()` handles three things that naive `word[::-1]` gets wrong:

1. **Nikud and cantillation marks.** Combining marks attach to the character that
   precedes them in logical order; reversing the string moves them onto the wrong base
   letter and renders as garbage. `fs.heb()` strips combining marks by default
   (`strip_nikud=True`). Pass `strip_nikud=False` only after visually confirming the
   output — if vowels are semantically necessary to the figure, verify the render.
2. **Embedded Latin text and digits.** In `"P3 שלום"`, reversing everything yields
   `"םולש 3P"` — the Hebrew is now correct but `P3` has become `3P`. `fs.heb()`
   re-reverses contiguous runs of Latin characters and digits so both read correctly.
3. **Trailing punctuation**, which lands on the wrong side under naive reversal.

Always eyeball at least one rendered figure per session. Silent glyph fallback boxes
(`□□□`) mean the chosen font lacks Hebrew coverage — DejaVu Sans has it and is the
default; a custom `font.family` may not.

## Title convention

`P# S# Model: <what the figure shows>` — the project ID prefix, then the claim, ≤10
words total for the descriptive part.

- Good: `P03 S02 Sonnet: recall collapses on low-frequency words`
- Good: `P07 S01 Opus: nikud absence costs 12 points`
- Bad: `P07 S01 Opus — Accuracy` (em-dash, and states no finding)
- Bad: `Accuracy for participant 7` (no ID convention, no finding)

When a figure aggregates across participants or sessions, use `ALL` in the slot rather
than omitting it: `P-ALL S02 Sonnet: ...`.

## Per-word color identity

Words are the items in the 22-color spectrum. The canonical ranking is by overall
accuracy across the full dataset, best to worst: the top 15 words take the spectral
sweep (pink → violet), the bottom 7 take the brown/gray/black tail.

**Freeze the map at project start and load it in every figure.** A word's color is
part of its identity across the whole project, not a per-figure decision. See the
freezing section in `palettes.md` — this is the single most consequential rule here,
because a color that shifts between figures produces confident wrong readings.

Words added to the corpus later append to the end of the map and keep their appended
color, even if their accuracy would place them higher. Note the addition in the caption
of the figure where the word first appears.

## Results and accuracy charts (standing rule, 2026-06-11)

- **White background.** (This superseded cream; the house default is now white
  everywhere, so no deviation is needed.)
- **No chance reference line or bar.** State the chance level in the caption. A drawn
  reference line invites eyeballing significance directly off the figure, which is the
  thing it looks most authoritative while doing worst.
- **Error bars as dashed whiskers**, showing mean ± 1 SD. Name the measure in the
  caption every time — SD, SEM, and CI get conflated by readers, and the dashes only
  signal "dispersion," not which one.

## Caption content for this project

Beyond the house requirements, project captions state:

- n words and n trials contributing to the figure
- chance level, since it is not drawn
- whether nikud was present in the stimuli, stripped for display only, or absent
- model and decoding settings if they vary across the figure set
- exclusions: count, rule, and whether the conclusion survives them

Example:

> *Mean per-word recall, 22 words × 40 trials, Sonnet at temperature 0. Chance = 4.5%.
> Stimuli included nikud; display strips combining marks for legibility only. Two trials
> above the 99th percentile of response latency excluded (flagged in the accompanying
> CSV); the ordering is unchanged with them included. Whiskers are ±1 SD.*
