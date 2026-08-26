# Palettes

## Contents

- [Selection rule](#selection-rule)
- [Eye palette (1–3 series)](#eye-palette-13-series)
- [22-color spectrum (4+ series)](#22-color-spectrum-4-series)
- [Freezing the color map](#freezing-the-color-map) ← read this before a multi-figure set
- [Accessibility and honesty notes](#accessibility-and-honesty-notes)

## Selection rule

| Series / distinct items | Palette |
|---|---|
| 1 | Amber alone |
| 2 | Amber + green |
| 3 | Amber + green + deep-pupil |
| 4+ | 22-color spectrum, in rank order |

Series count means *distinct things needing distinct colors*, not number of data
points. A 200-bar histogram is one series.

## Eye palette (1–3 series)

| Role | Hex | Use |
|---|---|---|
| Amber | `#D4A574` | First / primary series |
| Green | `#A8C86F` | Second series, or the comparison condition |
| Deep-pupil | `#1A1A2E` | Third series; also all text, ticks, and spines |

Deep-pupil doubling as ink is deliberate — a three-series figure reads as two colored
series against a dark reference, which is usually the right emphasis. If the third
series should not carry that weight, use a desaturated slate `#6E7E8A` instead and
note the substitution.

For sequential emphasis within one series (a single highlighted bar among grey ones),
use amber for the highlight and `#D8D8D8` for the muted rest. Do not reach for the
spectrum to solve emphasis.

## 22-color spectrum (4+ series)

One monotonic sweep. Positions 1–15 run pink → violet; positions 16–22 fade through
brown and gray to black. Position 22 is deep-pupil, closing the loop with the ink
color.

| # | Hex | Name |
|---|---|---|
| 1 | `#E6479A` | pink |
| 2 | `#E23B6B` | rose |
| 3 | `#DE3B45` | red |
| 4 | `#E3552B` | vermilion |
| 5 | `#E87A1E` | orange |
| 6 | `#F09A22` | tangerine |
| 7 | `#EDB824` | amber |
| 8 | `#DFD02B` | yellow |
| 9 | `#B9D239` | lime |
| 10 | `#85C63F` | green |
| 11 | `#46B878` | emerald |
| 12 | `#23B2A6` | teal |
| 13 | `#2497C6` | cyan |
| 14 | `#3A6CC4` | blue |
| 15 | `#7B4FBE` | violet |
| 16 | `#8C6D4F` | brown |
| 17 | `#7A6455` | taupe |
| 18 | `#6E6A66` | warm gray |
| 19 | `#5C5C5C` | gray |
| 20 | `#444444` | dark gray |
| 21 | `#2E2E2E` | charcoal |
| 22 | `#1A1A2E` | deep-pupil |

**Why the sweep is ordered this way.** Position encodes rank, so color carries
information rather than just distinguishing. The spectral run gives the top 15 items
distinct, legible hues; the desaturated tail groups the bottom 7 as visually
recessive, which is the honest reading — they are the items that did not perform. A
reader learns the direction once and then reads every subsequent figure faster.

**If you need more than 22 colors**, you have a chart-form problem, not a palette
problem. Go back to `chart-selection.md`: consider small multiples, or plotting the
top-N individually with the remainder aggregated as a single grey band.

**If you need fewer**, use the first N of the spectral run for a 4–15 series figure.
Do not compress the full sweep into fewer slots — that breaks cross-figure identity
(see below).

## Freezing the color map

This is the part that is easy to get wrong, and getting it wrong silently destroys
every comparison in the project.

The spectrum is ordered *by rank*. If you assign colors by live rank at plot time,
then any figure where the ranking shifts reassigns colors — the same word is pink in
figure 1 and orange in figure 4, and the reader draws a conclusion from a coincidence.
"One shared color language" is a claim about **identity**, not about position.

So: assign once, then freeze.

1. Decide the canonical ranking a single time, at project start, on the full dataset —
   whatever "best to worst" means for the project (overall accuracy, mean score).
2. Write the item → hex mapping to a file, e.g. `colors.json`, committed alongside the
   analysis.
3. Every figure thereafter **loads** that file. No figure recomputes it.
4. New items appearing later append to the end of the map; they do not renumber
   existing entries, even if their true rank is high. Note the append in the caption of
   the figure where they first appear.

`figstyle.freeze_color_map()` and `figstyle.load_color_map()` implement exactly this.
Use them rather than reimplementing, because the failure mode is invisible — nothing
errors, the figures just quietly lie.

Sorting a figure's *bars* by rank is fine and often good. Sorting the *colors* is the
bug.

## Accessibility and honesty notes

- The spectral sweep is not colorblind-safe across all 22 positions. When a figure
  must survive deuteranopia, pair color with a second channel: position, direct
  labeling, or line style. Direct labeling beats a legend anyway.
- Never encode a continuous quantity with the 22-color spectrum. It is a categorical
  palette carrying ordinal information; used as a continuous colormap, its uneven
  perceptual steps invent structure that is not in the data. For continuous fields use
  a perceptually uniform map (`viridis`, `magma`) and say which in the caption.
- Do not use red/green as the only distinction between two series that a reader is
  meant to compare — in the Eye palette, amber vs green is deliberately a
  lightness contrast as well as a hue contrast.
