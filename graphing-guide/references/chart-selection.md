# Chart selection

For pre-flight Q6: *what is the best way to showcase the biggest secret?*

The question is not "what chart type fits this data" — many fit. It is "which form
makes the finding unmissable." Work backwards from the sentence you wrote in Q3.

## Contents

- [By question being asked](#by-question-being-asked)
- [Default upgrades](#default-upgrades)
- [Forms to avoid](#forms-to-avoid)
- [Checking for what is missing (Q5)](#checking-for-what-is-missing-q5)

## By question being asked

| The finding is about… | Reach for | Instead of |
|---|---|---|
| Shape of one distribution | Histogram, or ECDF when tails matter | Mean ± error bar |
| Comparing 2–5 groups | Bar with dashed whiskers, or paired dot plot | Box plot for small n |
| Comparing many groups | Horizontal dot/lollipop, sorted by value | Rotated-label bar chart |
| Per-item change across two conditions | Slopegraph (one line per item) | Two side-by-side bars |
| Relationship between two variables | Scatter + fit, residuals if the fit is the claim | Correlation coefficient in prose |
| Change over time | Line, one per series | Stacked area |
| Same pattern across many units | Small multiples, shared axes | One overplotted panel |
| Part-to-whole | Stacked bar, or just a table | Pie, donut |
| Two-dimensional density | Heatmap or hexbin | Scatter with 50k points |
| Individual variation hidden by a mean | Strip/jitter plot over the summary | Summary alone |
| Ranking that is contested | Dot plot with CIs, sorted | Bar chart implying precision |

## Default upgrades

Applied by default unless there is a reason not to:

- **Show the raw points** when n is small enough (roughly n < 60 per group). A bar of
  height 0.7 with a whisker hides whether that is a tight cluster or a bimodal split.
  Jittered points over the bar cost nothing and often *are* the secret.
- **Sort by value, not alphabetically**, unless the category order is meaningful
  (time, dose, condition sequence). Alphabetical order is a randomizer.
- **Label directly** instead of using a legend when there are few enough series. A
  reader should not have to move their eyes to decode a color.
- **Horizontal bars** when labels are long. Rotated tick labels are a tax on the reader.
- **Start bar axes at zero.** Truncating a bar axis exaggerates differences; bars
  encode length. Line and dot plots may be truncated — they encode position — but say
  so in the caption.
- **Difference plots** when the claim is about a difference. If the finding is "B beats
  A by 8 points," plot B−A with a zero line rather than making the reader subtract two
  bar heights.

## Forms to avoid

- **Pie and donut charts.** Angle comparison is poor; a sorted bar or a table beats
  them in nearly every case.
- **Dual y-axes.** Two scales invite a spurious visual correlation that depends
  entirely on where the axes were placed. Use two stacked panels sharing an x-axis.
- **3D anything.** Perspective distorts the encoding it is decorating.
- **Box plots with small n.** They imply a distribution five summary statistics cannot
  support. Show the points.
- **Connecting lines across categorical gaps.** A line between unordered categories
  asserts a trend that does not exist.

## Checking for what is missing (Q5)

Run these before plotting. Each one has produced a wrong conclusion in a real analysis:

- **Unequal n across groups.** Compute and report per-group n. A group with n=3 next to
  one with n=40 should not get equal visual weight without comment.
- **Zeros standing in for nulls.** Check whether zero means "measured zero" or "no
  data." A mean including phantom zeros is not a mean.
- **Silently dropped rows.** Compare row count before and after every merge and filter.
  Log the delta. Inner joins lose data quietly.
- **Missing combinations.** Cross-tabulate the grouping variables and look for empty
  cells. An absent condition is a finding.
- **Truncated ranges.** Confirm the time or measurement range covers what the title
  claims. A trend over a subset is not a trend.
- **Ceiling and floor effects.** Values pinned at the maximum mean the instrument, not
  the participant, is being measured.
- **Aggregation over the wrong unit.** Averaging across trials when the unit of
  interest is the participant inflates apparent precision. Aggregate within unit first,
  then across.

Anything found here goes into the pre-flight summary, and if it survives into the
final figure, into the caption.
