"""figstyle — mechanical enforcement of the graphing-guide house style.

Covers the parts that drift when done by hand: rcParams, palette selection by series
count, frozen cross-figure color maps, percentile clipping with a caption-ready
disclosure string, caption placement, paired .png/.csv output, and Hebrew RTL text.

Judgment stays with you. This module will not choose a chart form, notice that the
variance is the finding, or write an honest caption.

Usage:
    import sys; sys.path.insert(0, "<skill-dir>/scripts")
    import figstyle as fs
    fs.apply_style()
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- palettes

INK = "#1A1A2E"          # deep-pupil: text, ticks, spines, and 3rd Eye series
AMBER = "#D4A574"
GREEN = "#A8C86F"
SLATE = "#6E7E8A"        # optional substitute 3rd series when INK is too heavy
MUTED = "#D8D8D8"        # background bars when highlighting one
CAPTION_GREY = "#8A8A8A"

EYE = [AMBER, GREEN, INK]

#: Spectrum-ordered. 1-15 sweep pink->violet (best items); 16-22 fade
#: brown->gray->black (worst items). Position 22 is INK, closing the loop.
SPECTRUM_22 = [
    "#E6479A", "#E23B6B", "#DE3B45", "#E3552B", "#E87A1E",  # pink -> orange
    "#F09A22", "#EDB824", "#DFD02B", "#B9D239", "#85C63F",  # tangerine -> green
    "#46B878", "#23B2A6", "#2497C6", "#3A6CC4", "#7B4FBE",  # emerald -> violet
    "#8C6D4F", "#7A6455", "#6E6A66", "#5C5C5C", "#444444",  # brown -> dark gray
    "#2E2E2E", "#1A1A2E",                                    # charcoal -> ink
]


def palette_for(n: int, third: str = INK) -> list[str]:
    """Return n colors, choosing Eye palette (1-3) or spectrum (4+).

    n is the count of *distinct things needing distinct colors* -- not data points.
    A 200-bar histogram is one series.

    For 4+ series the returned colors are spectrum positions 1..n in order, which
    assumes your items are already sorted best-to-worst. If items appear across
    multiple figures, do not use this -- use freeze_color_map/load_color_map so a
    given item keeps its color even when the ranking shifts.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if n <= 3:
        return [AMBER, GREEN, third][:n]
    if n > len(SPECTRUM_22):
        raise ValueError(
            f"{n} series exceeds the 22-color spectrum. This is a chart-form "
            "problem, not a palette problem -- see references/chart-selection.md "
            "(small multiples, or top-N plus an aggregated grey remainder)."
        )
    return SPECTRUM_22[:n]


def freeze_color_map(items, path="colors.json", overwrite=False) -> dict[str, str]:
    """Assign colors to items ONCE and persist the mapping.

    `items` must be ordered canonically (best -> worst) on the full dataset. Call
    this a single time at project start; every figure afterwards calls
    load_color_map(). Refuses to overwrite an existing map unless overwrite=True,
    because silently reassigning colors mid-project makes earlier figures lie
    without raising an error anywhere.
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise FileExistsError(
            f"{p} exists. Loading it instead of recomputing is almost always what "
            "you want; pass overwrite=True only if you intend to invalidate every "
            "figure already produced."
        )
    items = list(items)
    cmap = {str(k): c for k, c in zip(items, palette_for(max(len(items), 4)))}
    p.write_text(json.dumps(cmap, ensure_ascii=False, indent=2), encoding="utf-8")
    return cmap


def load_color_map(path="colors.json") -> dict[str, str]:
    """Load the frozen item -> hex mapping."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_to_color_map(new_items, path="colors.json") -> dict[str, str]:
    """Add items discovered after freezing, without renumbering existing entries.

    New items take the next free spectrum positions regardless of their true rank.
    Note the addition in the caption of the figure where they first appear.
    """
    cmap = load_color_map(path)
    used = len(cmap)
    for i, item in enumerate(new_items):
        key = str(item)
        if key in cmap:
            continue
        slot = used + i
        if slot >= len(SPECTRUM_22):
            raise ValueError("spectrum exhausted; see chart-selection.md")
        cmap[key] = SPECTRUM_22[slot]
    Path(path).write_text(json.dumps(cmap, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return cmap


def colors_for(items, path="colors.json") -> list[str]:
    """Look up frozen colors for a subset of items, in the order given."""
    cmap = load_color_map(path)
    missing = [str(i) for i in items if str(i) not in cmap]
    if missing:
        raise KeyError(f"not in frozen map: {missing} -- use append_to_color_map()")
    return [cmap[str(i)] for i in items]


# ---------------------------------------------------------------- style

def apply_style(base_size: int = 11) -> None:
    """Set rcParams for the house style: white ground, ink text, tidy spines."""
    mpl.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",      # has Hebrew coverage; verify if changed
        "font.size": base_size,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": INK,
        "axes.titlecolor": INK,
        "axes.titlesize": base_size + 2,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#E4E4E4",
        "grid.linewidth": 0.8,
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


def title(ax, text: str) -> None:
    """Set a title, warning if it drifts from the house form.

    House form: <=10 words, colon to separate scope from claim, never an em-dash.
    Warns rather than raises -- a project ID prefix legitimately adds words.
    """
    if "—" in text or " - " in text:
        print(f"[figstyle] title uses a dash; house style is a colon: {text!r}")
    if len(text.split()) > 12:
        print(f"[figstyle] title is {len(text.split())} words; aim <=10: {text!r}")
    ax.set_title(text, pad=10)


def caption(fig, text: str, y: float = -0.02) -> None:
    """Place the caption below the figure: size 9, light grey, italic.

    This is where depth goes -- how numbers were computed, the hypothesis, a light
    reading of the result, and any exclusion disclosure. Two to four sentences.
    """
    fig.text(0.5, y, text, ha="center", va="top", fontsize=9,
             color=CAPTION_GREY, style="italic", wrap=True)


def dashed_whiskers(ax, pos, value, err, orient: str = "v", color: str = INK,
                    lw: float = 0.9) -> None:
    """Draw error bars as dashed whiskers (the house form for results charts).

    matplotlib's errorbar() cannot dash its error lines cleanly, so draw them
    directly. `orient="v"` for vertical whiskers on a bar/dot chart (pos is x),
    `"h"` for horizontal (pos is y).

    Whatever dispersion measure you pass -- SD, SEM, CI -- name it in the caption.
    The dashes only signal "dispersion", and readers will assume the wrong one.
    """
    import numpy as np
    pos, value, err = np.atleast_1d(pos), np.atleast_1d(value), np.atleast_1d(err)
    style = dict(ls=(0, (2, 1.5)), color=color, lw=lw, solid_capstyle="butt")
    for p, v, e in zip(pos, value, err):
        if orient == "v":
            ax.plot([p, p], [v - e, v + e], **style)
        else:
            ax.plot([v - e, v + e], [p, p], **style)


def label_grid(axes, xlabel: str, ylabel: str) -> None:
    """Label only the bottom row and left column of a subplot grid."""
    import numpy as np
    a = np.atleast_2d(axes)
    for ax in a[-1, :]:
        ax.set_xlabel(xlabel)
    for ax in a[:, 0]:
        ax.set_ylabel(ylabel)


def lock_limits(axes, lo: float, hi: float, axis: str = "y", pad: float = 0.03) -> None:
    """Apply identical limits across a set of axes so panels stay comparable."""
    span = hi - lo
    limits = (lo - span * pad, hi + span * pad)
    for ax in (axes.ravel() if hasattr(axes, "ravel") else axes):
        (ax.set_ylim if axis == "y" else ax.set_xlim)(*limits)


# ---------------------------------------------------------------- outliers

def clip_outliers(df, column: str, pct: float = 99.0, flag_col: str = "outlier"):
    """Flag values above the pct-th percentile. Returns (df_with_flag, note).

    Rows are FLAGGED, not deleted, so the exclusion stays reversible for whoever
    reads the CSV. Filter with `df[~df[flag_col]]` when plotting.

    `note` is a caption-ready disclosure string. Paste it in -- the house style
    requires disclosing exclusions, and requires you to have checked whether the
    conclusion survives them. This function cannot check that for you.
    """
    out = df.copy()
    threshold = out[column].quantile(pct / 100.0)
    out[flag_col] = out[column] > threshold
    n = int(out[flag_col].sum())
    if n == 0:
        return out, f"No values exceeded the {pct:g}th percentile of {column}."
    note = (f"{n} value{'s' if n != 1 else ''} above the {pct:g}th percentile of "
            f"{column} (>{threshold:.4g}) excluded from the figure and flagged in "
            f"the accompanying CSV.")
    return out, note


def keep(df, flag_col: str = "outlier"):
    """Return the non-flagged rows."""
    return df[~df[flag_col]]


# ---------------------------------------------------------------- Hebrew RTL

_LATIN_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.,:%\-/]*")


def heb(text: str, strip_nikud: bool = True) -> str:
    """Prepare Hebrew for matplotlib, which does no bidi reordering.

    Handles what naive text[::-1] gets wrong:
      - combining marks (nikud, cantillation) landing on the wrong base letter
      - embedded Latin/digit runs being reversed too ("P3" -> "3P")

    strip_nikud=False keeps vowel marks; verify the render visually before relying
    on it, since matplotlib does not position combining marks well.
    """
    s = unicodedata.normalize("NFD", text)
    if strip_nikud:
        s = "".join(c for c in s if not unicodedata.combining(c))
    s = unicodedata.normalize("NFC", s)
    out = s[::-1]
    # Latin/digit runs got reversed along with everything else; put them back.
    return _LATIN_RUN.sub(lambda m: m.group(0)[::-1], out)


def has_hebrew_font() -> bool:
    """True if the active font family can render Hebrew (alef through tav)."""
    try:
        from fontTools.ttLib import TTFont
        from matplotlib.font_manager import findfont, FontProperties
        path = findfont(FontProperties(family=mpl.rcParams["font.family"]))
        f = TTFont(path, fontNumber=0, lazy=True)
        cmap = f.getBestCmap()
        f.close()
        return 0x05D0 in cmap and 0x05EA in cmap
    except Exception:
        return False


# ---------------------------------------------------------------- output

def save_figure(fig, stem: str, data=None, outdir: str = ".") -> dict:
    """Write <stem>.png and <stem>.csv together. Returns the two paths.

    The pairing is not optional in this house style: the CSV holds the exact data
    plotted (post-filter, post-aggregation) so any figure can be audited or rebuilt
    without re-running the analysis. Omitting `data` warns loudly.
    """
    d = Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    png = d / f"{stem}.png"
    csv = d / f"{stem}.csv"
    fig.savefig(png, bbox_inches="tight")
    if data is None:
        print(f"[figstyle] {stem}.png saved with NO CSV. A figure without its data "
              "is unfinished -- pass data= with exactly what was plotted.")
        return {"png": str(png), "csv": None}
    data.to_csv(csv, index=False, encoding="utf-8-sig")  # BOM so Excel reads Hebrew
    return {"png": str(png), "csv": str(csv)}
