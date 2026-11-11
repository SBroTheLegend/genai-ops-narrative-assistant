"""Language the brief is allowed to use.

The boundary is part of every template. It is prose, not a figure, so it
carries no numerals. Causal connectors are rejected by the reviewer even
inside a quoted note: a note in this sample is a record, not a bridge.
"""

from __future__ import annotations

CLAIMS_BOUNDARY = """## Claims boundary

This brief is a draft for a human reviewer. It is allowed to state:

- Levels, plan, prior-period, and prior-year comparisons present on the pack
- Arithmetic the metric engine defines: profit, margin, days of supply, rates, variances, and variance shares
- Threshold breaches named in the materiality and exception policy
- Operating notes, quoted in full, as recorded context

It is not allowed to state:

- A cause, a customer outcome, or a market fact the pack does not contain
- A price, volume, or mix bridge, or any other bridge that was not supplied
- A forecast, a target, or an action size that is not already a figure on the pack
- A decision. Questions for the reviewer add no new figures

The optional language-model hook is off unless explicitly enabled. A polish pass that changes a cited figure, an unlabeled numeral, the sign of a variance, or this boundary is discarded.

Template scope: commentary below the network is versus plan. Prior year is on the network scorecard. A node or category that only repeats the network movement is omitted. A cell is named only when it holds a published share of a parent plan variance without exceeding that parent gap. Share is arithmetic, not a cause.
"""

BANNED_PHRASES: tuple[str, ...] = (
    "because",
    "due to",
    "driven by",
    "as a result",
    "caused by",
    "led to",
    "thanks to",
    "on the back of",
)

COUNT_WORDS: tuple[str, ...] = (
    "no",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
)


def count_words(count: int) -> str | None:
    if 0 <= count < len(COUNT_WORDS):
        return COUNT_WORDS[count]
    return None
