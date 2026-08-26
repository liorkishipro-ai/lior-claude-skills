---
name: pipeline-validation
description: Use this any time a data-processing pipeline stage runs — filtering, segmentation, feature extraction, dimensionality reduction, or any transformation of EMG/signal data — before moving on to the next stage or reporting a result. Also trigger when the user reports a model performing near chance, when writing EMG data to EDF files, or when the user says things like "let's segment this," "run the pipeline," "extract features," or shares an accuracy number that seems off. A pipeline can look perfectly built and still fail silently — the point of this skill is to make failure loud instead of quiet, at the stage it happens rather than at the end.
---

# Pipeline Validation

## The principle

A perfectly designed pipeline can fail silently. Annotation → filtering → segmentation →
feature extraction → PCA → hyperparameter optimization can all run without error while the
data underneath is destroyed at step one — and nothing downstream will tell you, because
every later step just processes whatever noise it's handed and produces a plausible-looking
number. Systems degrade gracefully and fail silently; catching that requires checking, not
hoping.

**The rule: validate after every stage, not just at the end.** If a stage doesn't get
checked, assume it's broken until proven otherwise.

## Validation protocol — run after every stage

1. **Data integrity** — shape matches expectations; no NaN/Inf; value ranges are sensible
   (not all zero, not all one value).
2. **Separation of concerns** — train/val/test sets don't overlap; metadata is consistent
   (the same `word_id` always maps to the same label).
3. **Feature statistics** — non-zero variance; no feature is all zeros; sample stats match
   domain knowledge.
4. **Baseline sanity checks** — random classifier, majority-class baseline, and a simple
   1-NN on the final features. Even a simple model should beat random by 3–5x. If it
   doesn't, stop — the problem is upstream, not in the model you're about to tune.
5. **Signal presence** — check the upstream data (filtered EDF, segments) for actual
   signal, not just shape. Visual inspection when in doubt (see below).

## When to validate

- After filtering — did the filter destroy signal?
- After segmentation — do a few segments have non-zero values?
- After feature extraction — are features non-zero?
- After dimensionality reduction — how much variance is captured?
- After any transformation, before optimization — establish the baseline first.

## Red flags — stop and investigate

- Accuracy near 1/N (random guessing).
- 1-NN getting <20% on features (features aren't informative).
- Features with mean=0, std=0.
- Filtered/processed data with max value < 1e-8.
- Inconsistent class distributions across train/val/test.

## Visual inspection: the 5-second window

When a numeric check isn't conclusive, plot it — but choose the window deliberately.
A roughly **5-second window** is the standard for spot-checking signal dynamics (RMS
envelopes, waveforms, alignment), because it's long enough to see structure (5000
samples @ 500 Hz) but short enough to resolve individual events without drowning in
detail. Center it on the region of interest (an onset, a transition), and if comparing
signals (e.g. audio vs. EMG), use identical x-axis limits across both. For longer
sessions, take multiple 5-second snapshots rather than one compressed view. (For the
plot's styling itself — palette, titles, captions — use the `graphing-guide` skill.)

## Segmentation checklist

After segmenting filtered data into trials:

**Structure & metadata**
- Correct number of segments (one per trial); metadata arrays match segment count.
- Trial IDs range 1–N, no gaps or duplicates; rep IDs sequential; word IDs in range.

**Per-segment shape & content**
- Each segment is 2D: `(n_channels, n_samples)`; correct channel count.
- Sample count ≈ duration × sampling rate (within 5% tolerance).
- No NaN/Inf; no dead channels (all-zero — suggests a filtering/alignment failure).

**Signal quality (spot-check)**
- Amplitude reasonable (~0.1–1 mV/channel); RMS > 1e-8 V (not noise floor).
- Max > min per channel (not flat); non-zero variance across channels.
- Visualize one or two segments to confirm signal is actually present.

NPZ files don't enforce validation on load — a segment can be empty, misaligned, or pure
noise and nothing will complain. Always spot-check.

## Critical: units in EDF files

When writing EMG data to EDF with `pyedflib`, the `dimension` field (e.g. `"V"`, `"uV"`)
must match the units of `physical_max`/`physical_min` **and** the data array itself. A
mismatch causes silent rescaling on read-back — data in volts but headers claiming
microvolts turns 6.2 mV into 6.2 nanovolts on the next read. Validate by:

1. Checking the filtered signal in-memory, before writing the EDF.
2. Reading the EDF back and comparing statistics against step 1.
3. Treating any max value < 1e-8 as a unit-mismatch suspect, not just a filtering issue.
