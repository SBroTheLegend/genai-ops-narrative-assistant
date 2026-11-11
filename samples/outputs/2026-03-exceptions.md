<!-- ops-narrative
kind: exception
template: exception.v1.0.0
period: 2026-03
engine: deterministic
-->

# Calderwisp Wholesale — March 2026 exception brief

Fictional synthetic pack. Template `exception.v1.0.0`. Engine `deterministic`. Currency USD.

> Calderwisp Wholesale is a fictional wholesaler created for this portfolio sample. Nodes, categories, operating notes, and figures are synthetic. They do not describe a real business, person, customer, or site.

This exception brief covers five policy breaches. A breach is a break of a published standard or plan bar. It is not, by itself, a cause.

| Id | Where | Metric | Reading | Bar | Rule |
| --- | --- | --- | --- | --- | --- |
| `exc.family.personal.forecast_accuracy.below_floor` | Personal care | Forecast accuracy | [64.1%](cite:family.personal.forecast_accuracy.actual) | [80.0%](cite:policy.forecast_accuracy_floor) | `below_floor` |
| `exc.facility.osier.dos.above_ceiling` | Osier node | Days of supply | [51.9 days](cite:facility.osier.dos.actual) | [46.0 days](cite:facility.osier.dos.ceiling) | `above_ceiling` |
| `exc.facility.redkiln.otif.below_standard` | Redkiln node | OTIF | [91.4%](cite:facility.redkiln.otif.actual) | [95.0%](cite:policy.otif_standard) | `below_standard` |
| `exc.facility.redkiln.expedite_cost.above_plan` | Redkiln node | Expedite cost | [+73.5%](cite:facility.redkiln.expedite_cost.var_plan_pct_signed) | [+25.0%](cite:policy.expedite_overrun) | `above_plan` |
| `exc.facility.redkiln.revenue.below_plan` | Redkiln node | Net revenue | [-3.5%](cite:facility.redkiln.revenue.var_plan_pct_signed) | [-3.0%](cite:policy.revenue_shortfall) | `below_plan` |

Personal care is an exception `exc.family.personal.forecast_accuracy.below_floor` on Forecast accuracy: actual [64.1%](cite:family.personal.forecast_accuracy.actual). The bar is [80.0%](cite:policy.forecast_accuracy_floor) (`below_floor`). No operating note is attached. A cause is not assigned.

Osier node is an exception `exc.facility.osier.dos.above_ceiling` on Days of supply: actual [51.9 days](cite:facility.osier.dos.actual). The bar is [46.0 days](cite:facility.osier.dos.ceiling) (`above_ceiling`).

> Osier node again received an early purchase-order pull-in. The note records the pull-in. It is not a write-down proposal.

Recorded context only. The note is not a quantified bridge.

Redkiln node is an exception `exc.facility.redkiln.otif.below_standard` on OTIF: actual [91.4%](cite:facility.redkiln.otif.actual). The bar is [95.0%](cite:policy.otif_standard) (`below_standard`).

> Redkiln node logged late inbounds on two staples lanes during week 3. The note records dwell and a re-wave. It does not record cancellations or a customer concession.

Recorded context only. The note is not a quantified bridge.

Redkiln node is an exception `exc.facility.redkiln.expedite_cost.above_plan` on Expedite cost: actual [$75K](cite:facility.redkiln.expedite_cost.actual), a plan gap of [+73.5%](cite:facility.redkiln.expedite_cost.var_plan_pct_signed). The bar is [+25.0%](cite:policy.expedite_overrun) (`above_plan`). The operating note on this slice is already quoted above. It is not a quantified bridge.

Redkiln node is an exception `exc.facility.redkiln.revenue.below_plan` on Net revenue: actual [$11.9M](cite:facility.redkiln.revenue.actual), a plan gap of [-3.5%](cite:facility.redkiln.revenue.var_plan_pct_signed). The bar is [-3.0%](cite:policy.revenue_shortfall) (`below_plan`). No operating note is attached. A cause is not assigned.

## Reviewer questions

- Does the service breach at Redkiln node qualify the network month, even though network OTIF still meets the standard?
- Personal care forecast accuracy breaches the floor and no operating note is attached. What should demand planning add before this brief is treated as closed?
- Osier node is past the days-of-supply ceiling and a note is attached. The note is not a write-down. Is the close disclosure only, or does finance want a separate inventory action?
- Redkiln node expedite cost breaches its plan bar. Should premium freight be disclosed on its own, without being treated as the explanation of service?
- Redkiln node revenue breaches the plan bar. No price, volume, or mix bridge was supplied. What should commercial add before a cause is written into the close?

## Claims boundary

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

## Fact index

- `family.personal.forecast_accuracy.actual`
- `policy.forecast_accuracy_floor`
- `facility.osier.dos.actual`
- `facility.osier.dos.ceiling`
- `facility.redkiln.otif.actual`
- `policy.otif_standard`
- `facility.redkiln.expedite_cost.var_plan_pct_signed`
- `policy.expedite_overrun`
- `facility.redkiln.revenue.var_plan_pct_signed`
- `policy.revenue_shortfall`
- `facility.redkiln.expedite_cost.actual`
- `facility.redkiln.revenue.actual`
