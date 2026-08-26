---
name: graphing-guide
description: A house style and analysis procedure for producing figures that reveal what data is actually saying — pre-flight interrogation of the dataset, sharp titles, explanatory captions, locked palettes, disciplined outlier handling, and paired .png/.csv output. Use this skill whenever the user asks for a graph, chart, plot, figure, visualization, or "show me the data" — and also whenever a task will produce a figure as a byproduct, such as analyzing a CSV, comparing model results, reporting accuracy, or examining distributions, even if the user never says the word "graph." If matplotlib is about to be imported, this skill applies.
---

# Graphing Guide

## The role

You are a revealer of secrets. Data arrives confusing and jumbled; your job is to
return a figure that uncovers the message hiding inside it. Think puzzle-decoder,
not chart-renderer.

The difference matters in practice. A chart-renderer receives "plot accuracy by
condition" and plots accuracy by condition. A revealer notices that two conditions
are indistinguishable, that the variance tells a better story than the means, and
that one participant is dragging the whole effect — and builds the figure that shows
*that*. The request is the starting point, not the specification.

So: never go straight to code.

## Pre-flight

Before writing any plotting code, answer these six questions against the actual data.
Load it, look at it, compute what you need to answer honestly.

1. **What am I looking at?** Shape, units, granularity, what one row means.
2. **Who is this for?** Self-review, a collaborator, a supervisor, a paper, a
   presentation. This governs density and how much prior context to assume.
3. **What is most interesting here?** The finding, not the variables. Say it as a
   sentence a person could disagree with.
4. **Are there outliers?** Check before deciding. Report counts and magnitudes.
5. **Is something missing?** Unequal n, silent dropped rows, zeros standing in for
   nulls, a condition with no data, a truncated time range.
6. **What is the best way to showcase the biggest secret?** Chart form, and why that
   form over the obvious one. See `references/chart-selection.md`.

Compile the answers into a tight bullet summary — one or two lines each, no padding —
and send it back with AskUserQuestion so the user can confirm the read or redirect it.
Once you are on the same page, you have the green light to execute.

**Cadence.** Check in **once per series**, then proceed. The pre-flight runs at the
start of a new figure series or a new dataset; subsequent figures in the same series
are built without stopping to ask again. Re-open the conversation only when something
material changes:

- the data shape changes (new conditions, new grouping variable, different n)
- an exclusion decision arises that was not covered in the original green light
- the finding you now see contradicts the story the series was built to tell
- the series outgrows its palette (crossing the 3-series boundary, or new items
  appearing that need colors assigned)

That last one is worth saying plainly: if you discover mid-series that the original
framing was wrong, stop and say so. Silently building six more figures on a
misreading is worse than one extra question.

## House style

These are defaults, not suggestions. Deviating is fine when the data demands it —
say so in the caption when you do.

**Titles.** Sharp, ≤10 words, stating what the figure shows. Use a colon to separate
scope from claim; never an em-dash. Lead with the project's ID convention if it has
one.

- Good: `Accuracy by condition: masking cost is nonlinear`
- Bad: `Accuracy by condition — a look at how masking affects performance`
- Bad: `Figure 3`

**Captions.** Below the figure, size 9, light grey (`#8A8A8A`), italicized. This is
where the depth goes: how the numbers were computed, what hypothesis is in play, a
light reading of the result. Two to four sentences. If outliers were excluded, the
caption must say so — count, rule, and effect on the conclusion.

**Axes.** Balance precision against readability: enough ticks to read a value off the
figure, few enough that the axis is not noise. In subplot grids, axis labels appear
only on the bottom row and left column; repeating them on every panel is clutter.

**Background.** White. (Cream was retired for results charts on 2026-06-11; white is
now the default everywhere for consistency.)

**Saving.** Always `bbox_inches='tight'`.

**Output pairing.** Every figure produces both a `.png` and a `.csv` with the same
basename. The CSV holds the exact data plotted — post-filtering, post-aggregation —
so any figure can be audited or rebuilt without re-running the analysis. A figure
without its CSV is unfinished.

## Palettes

Two palettes, selected by series count:

- **1–3 series → Eye palette.** Amber `#D4A574`, green `#A8C86F`, deep-pupil
  `#1A1A2E`. Deep-pupil is also the text/ink color throughout.
- **4+ series → 22-color spectrum.** A single monotonic sweep, pink → red → orange →
  yellow → green → cyan → blue → indigo → violet across the best 15 items, fading
  through brown and gray to black across the worst 7.

Full hex tables, the ordering rationale, and — importantly — the mechanic for
**freezing** a color map so a given item keeps its color across every figure in the
project: `references/palettes.md`. Read it before assigning colors to a 4+ series
figure. Assigning spectrum colors by live rank order is a trap; the file explains why.

## Outliers

Handle with caution and a bias toward exclusion. Default rule: drop above the 99th
percentile. Two obligations follow:

1. **Disclose in the caption.** How many points, what rule, and whether the
   conclusion survives their removal. If you did not check whether it survives, check.
2. **Keep them in the CSV** with a flag column rather than deleting them, so the
   exclusion is reversible by whoever reads the output.

Exclusion is not automatic. An outlier that *is* the finding — a participant who
behaves nothing like the others, a condition that breaks the pattern — gets kept and
pointed at. The 99th percentile rule guards against measurement artifacts and long
tails swamping an axis, not against surprising data.

## Series consistency

When producing a set of figures meant to be compared, comparability is the whole
point, and it is easy to destroy accidentally:

- **One shared color language across every figure**, not per-plot. A given item is the
  same color in figure 1 and figure 9.
- **Locked axis limits** across the set. Compute the global min/max once and apply it
  everywhere. Autoscaled panels look tidy and lie about magnitude.
- **Uniform title grammar and caption structure**, so a reader learns the format once.
- **Same figure dimensions and font sizes**, so nothing appears more important for
  being bigger.

## Results and accuracy charts

Additional rules for figures reporting model or participant performance:

- White background.
- **No chance reference line or bar.** State chance in the caption instead; a
  reference line invites eyeballing significance off the figure.
- Error bars drawn as **dashed** whiskers, showing mean ± standard deviation. Say
  which dispersion measure it is in the caption — SD, SEM, and CI are not
  interchangeable and readers will assume the wrong one.

## scripts/figstyle.py

A helper module that enforces the mechanical parts of this style so they cannot drift:
rcParams, palette selection by series count, frozen color maps, percentile clipping
that returns a ready-made disclosure string, dashed whiskers, caption placement, locked
axis limits, paired png/csv saving, and Hebrew RTL text preparation.

```python
import sys; sys.path.insert(0, "<skill-dir>/scripts")
import figstyle as fs

fs.apply_style()
fig, ax = plt.subplots(figsize=(7, 4.5))

df, note = fs.clip_outliers(df, "rt_ms")        # flags, does not delete; note is caption-ready
plotted = summarize(fs.keep(df))

ax.bar(labels, plotted["mean"], color=fs.palette_for(len(labels)))
fs.dashed_whiskers(ax, range(len(labels)), plotted["mean"], plotted["sd"])
fs.title(ax, "P03 S02 Sonnet: masking cost is nonlinear")
fs.caption(fig, f"Mean RT per condition, n=24. Chance = 4.5%. {note} Whiskers are ±1 SD.")
fs.save_figure(fig, "p03_s02_rt_by_condition", data=plotted)   # writes .png + .csv
```

For any multi-figure set, replace `palette_for()` with `freeze_color_map()` once at
project start and `colors_for()` in every figure thereafter.

Read the module before using it; the docstrings state what each function assumes.
Prefer it over hand-rolling the style, but do not fight it — if a figure needs
something the module does not do, write the matplotlib directly and keep the style
rules by hand.

## Reference files

| File | Read when |
|---|---|
| `references/palettes.md` | Assigning colors, especially 4+ series or any multi-figure set |
| `references/chart-selection.md` | Answering pre-flight Q6; choosing a form that reveals rather than merely displays |
| `references/research-hebrew.md` | Working on the Hebrew-word / model-evaluation research project — RTL text rules, `P# S# Model` title convention, per-word figure conventions |

## Project layers

The rules above are general. Individual projects add conventions on top — ID formats,
domain-specific display requirements, standing decisions about what goes on an axis.
The Hebrew-word research project's layer lives in `references/research-hebrew.md`.
When a project's convention conflicts with the house style, the project wins; note the
deviation in the caption so it reads as a decision rather than an inconsistency.
