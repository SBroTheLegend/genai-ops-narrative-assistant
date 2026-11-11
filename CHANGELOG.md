# Changelog

## 0.6.0

- The review gate checks cited figures, unlabeled numerals, the sign of variance language, and causal connectors.
- Coverage is pinned to the template version. The retired month-end scorecard does not pretend to cover exceptions.
- A node or category that only repeats the network movement is left off the variance table.
- The optional external polish hook stays off unless `OPS_NARRATIVE_LLM=1`. This build does not call a provider. A polish that fails the gate is discarded.

## 0.5.0

- Materiality and exception thresholds live in one policy module, shared by the narrative and the reviewer.
- Comparisons use the same displayed precision as the brief, so a figure that prints as 95.0% is not also called a breach of a 95.0% standard.

## 0.4.0

- Deterministic synthetic packs for a fictional wholesaler, with operating notes that are records rather than calculated bridges.
