<!-- ops-narrative
kind: variance
template: variance.v1.0.0
period: 2026-03
engine: deterministic
-->

# Calderwisp Wholesale — March 2026 variance commentary

Fictional synthetic pack. Template `variance.v1.0.0`. Engine `deterministic`. Currency USD.

> Calderwisp Wholesale is a fictional wholesaler created for this portfolio sample. Nodes, categories, operating notes, and figures are synthetic. They do not describe a real business, person, customer, or site.

This variance commentary covers twelve material plan variances at network, node, and category. Immaterial movements are omitted. Omission is not a claim that those movements were flat.

| Where | Metric | Vs plan | Why it is listed |
| --- | --- | --- | --- |
| Redkiln node | Net revenue | [-3.5%](cite:facility.redkiln.revenue.var_plan_pct_signed) | clears the relative bar |
| Network | Gross margin | [+59 bps](cite:network.gross_margin.var_plan_bps_signed) | clears the absolute bar |
| Redkiln node | OTIF | [-5.8 pp](cite:facility.redkiln.otif.var_plan_pp_signed) | clears the absolute bar |
| Network | OTIF | [-1.5 pp](cite:network.otif.var_plan_pp_signed) | clears the absolute bar |
| Personal care | Forecast accuracy | [-23.9 pp](cite:family.personal.forecast_accuracy.var_plan_pp_signed) | clears the absolute bar |
| Network | Forecast accuracy | [-2.4 pp](cite:network.forecast_accuracy.var_plan_pp_signed) | clears the absolute bar |
| Osier node | Days of supply | [+11.9 days](cite:facility.osier.dos.var_plan_days_signed) | clears the absolute bar |
| Network | Days of supply | [+3.2 days](cite:network.dos.var_plan_days_signed) | clears the absolute bar |
| Redkiln node | Expedite cost | [+73.5%](cite:facility.redkiln.expedite_cost.var_plan_pct_signed) | clears the relative bar |
| Network | Expedite cost | [+20.4%](cite:network.expedite_cost.var_plan_pct_signed) | clears the relative bar |
| Osier node | Ending inventory | [+28.8%](cite:facility.osier.inventory.var_plan_pct_signed) | clears the absolute and relative bars |
| Network | Ending inventory | [+6.2%](cite:network.inventory.var_plan_pct_signed) | clears the absolute bar |

### Net revenue

Net revenue was [$43.7M](cite:network.revenue.actual) against a plan of [$44.1M](cite:network.revenue.plan), [1.0%](cite:network.revenue.var_plan_pct_abs) below plan. That plan variance sits inside the materiality bar. The concentrated movement is Redkiln node, [3.5%](cite:facility.redkiln.revenue.var_plan_pct_abs) below plan. Staples at Redkiln node holds [96.2%](cite:cell.redkiln.staples.revenue.share_of.facility.redkiln.var_plan) of that plan variance. The share is arithmetic, not a cause. Open exception ids: `exc.facility.redkiln.revenue.below_plan`.

### Gross margin

Gross margin was [27.2%](cite:network.gross_margin.actual) against a plan of [26.6%](cite:network.gross_margin.plan), [59 bps](cite:network.gross_margin.var_plan_bps_abs) above plan. That plan variance clears the absolute bar. The move shows up across nodes and categories. None is concentrated enough to narrate on its own. No policy exception is open on this metric.

### OTIF

OTIF was [95.7%](cite:network.otif.actual) against a plan of [97.2%](cite:network.otif.plan), [1.5 pp](cite:network.otif.var_plan_pp_abs) below plan. That plan variance clears the absolute bar. The concentrated movement is Redkiln node, [5.8 pp](cite:facility.redkiln.otif.var_plan_pp_abs) below plan. Open exception ids: `exc.facility.redkiln.otif.below_standard`.

### Forecast accuracy

Forecast accuracy was [85.6%](cite:network.forecast_accuracy.actual) against a plan of [88.0%](cite:network.forecast_accuracy.plan), [2.4 pp](cite:network.forecast_accuracy.var_plan_pp_abs) below plan. That plan variance clears the absolute bar. The concentrated movement is Personal care, [23.9 pp](cite:family.personal.forecast_accuracy.var_plan_pp_abs) below plan. Open exception ids: `exc.family.personal.forecast_accuracy.below_floor`.

### Days of supply

Days of supply was [43.2 days](cite:network.dos.actual) against a plan of [40.0 days](cite:network.dos.plan), [3.2 days](cite:network.dos.var_plan_days_abs) above plan. That plan variance clears the absolute bar. The concentrated movement is Osier node, [11.9 days](cite:facility.osier.dos.var_plan_days_abs) above plan. Open exception ids: `exc.facility.osier.dos.above_ceiling`.

### Expedite cost

Expedite cost was [$186K](cite:network.expedite_cost.actual) against a plan of [$154K](cite:network.expedite_cost.plan), [20.4%](cite:network.expedite_cost.var_plan_pct_abs) above plan. That plan variance clears the relative bar. The concentrated movement is Redkiln node, [73.5%](cite:facility.redkiln.expedite_cost.var_plan_pct_abs) above plan. Open exception ids: `exc.facility.redkiln.expedite_cost.above_plan`.

### Ending inventory

Ending inventory was [$44.4M](cite:network.inventory.actual) against a plan of [$41.8M](cite:network.inventory.plan), [6.2%](cite:network.inventory.var_plan_pct_abs) above plan. That plan variance clears the absolute bar. The concentrated movement is Osier node, [28.8%](cite:facility.osier.inventory.var_plan_pct_abs) above plan. Staples at Osier node holds [63.2%](cite:cell.osier.staples.inventory.share_of.network.var_plan) of the network plan variance. The share is arithmetic, not a cause. No policy exception is open on this metric.

Node and category lines are versus plan. Prior year is not re-judged in this commentary.

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

- `facility.redkiln.revenue.var_plan_pct_signed`
- `network.gross_margin.var_plan_bps_signed`
- `facility.redkiln.otif.var_plan_pp_signed`
- `network.otif.var_plan_pp_signed`
- `family.personal.forecast_accuracy.var_plan_pp_signed`
- `network.forecast_accuracy.var_plan_pp_signed`
- `facility.osier.dos.var_plan_days_signed`
- `network.dos.var_plan_days_signed`
- `facility.redkiln.expedite_cost.var_plan_pct_signed`
- `network.expedite_cost.var_plan_pct_signed`
- `facility.osier.inventory.var_plan_pct_signed`
- `network.inventory.var_plan_pct_signed`
- `network.revenue.actual`
- `network.revenue.plan`
- `network.revenue.var_plan_pct_abs`
- `facility.redkiln.revenue.var_plan_pct_abs`
- `cell.redkiln.staples.revenue.share_of.facility.redkiln.var_plan`
- `network.gross_margin.actual`
- `network.gross_margin.plan`
- `network.gross_margin.var_plan_bps_abs`
- `network.otif.actual`
- `network.otif.plan`
- `network.otif.var_plan_pp_abs`
- `facility.redkiln.otif.var_plan_pp_abs`
- `network.forecast_accuracy.actual`
- `network.forecast_accuracy.plan`
- `network.forecast_accuracy.var_plan_pp_abs`
- `family.personal.forecast_accuracy.var_plan_pp_abs`
- `network.dos.actual`
- `network.dos.plan`
- `network.dos.var_plan_days_abs`
- `facility.osier.dos.var_plan_days_abs`
- `network.expedite_cost.actual`
- `network.expedite_cost.plan`
- `network.expedite_cost.var_plan_pct_abs`
- `facility.redkiln.expedite_cost.var_plan_pct_abs`
- `network.inventory.actual`
- `network.inventory.plan`
- `network.inventory.var_plan_pct_abs`
- `facility.osier.inventory.var_plan_pct_abs`
- `cell.osier.staples.inventory.share_of.network.var_plan`
