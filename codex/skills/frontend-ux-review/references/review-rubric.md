# Frontend UX Review Rubric

This reference adapts the useful parts of a media-evaluator pattern to frontend UI review: decomposed dimensions, evidence, deterministic checks where possible, and actionable findings. Do not use a single opaque score.

## Report Contract

```ts
{
  schemaVersion: "1.0",
  meta: {
    target: string,                 // URL, file, screenshot, component, or diff
    reviewedAt: string,             // ISO timestamp
    mode: "quick" | "rendered" | "deep-flow",
    viewports?: { name: string, width: number, height: number }[],
    evidence?: string[]             // screenshot/report/file paths
  },
  scope: {
    screenOrFlow: string,
    userGoal: string | null,
    outOfScope: string[]
  },
  dimensions: DimensionVerdict[],
  findings: Finding[],
  residualRisk: string[]
}
```

## Dimension Verdict

```ts
{
  id:
    | "readability"
    | "information_hierarchy"
    | "layout_resilience"
    | "navigation"
    | "tables_dense_data"
    | "forms_validation"
    | "accessibility_baseline"
    | "responsive_behavior"
    | "state_coverage"
    | "pattern_fitness"
    | "conversion_ergonomics"
    | "stakeholder_dispute",
  verdict: "pass" | "warn" | "fail" | "not_checked",
  reason: string,
  evidence: string[]
}
```

## Finding

```ts
{
  id: "F1" | "F2",
  severity: "critical" | "high" | "medium" | "low",
  category: string,
  viewport?: string,
  selector?: string,
  file?: string,
  line?: number,
  message: string,
  impact: string,
  evidence: string[],
  fixHint: string
}
```

Severity guide:

- `critical`: blocks a primary workflow, hides/destructively misleads critical data, or makes a core form/action unusable.
- `high`: materially slows or confuses a primary repeated workflow, clips critical controls/data, or creates a likely wrong action.
- `medium`: weakens scanability, causes avoidable ambiguity, or breaks an important secondary/responsive state.
- `low`: polish, consistency, naming, minor spacing, or non-blocking accessibility improvement.

## Categories

- `readability.contrast`
- `readability.typography`
- `readability.copy-density`
- `hierarchy.primary-action`
- `hierarchy.visual-priority`
- `layout.overflow`
- `layout.clipping`
- `layout.spacing`
- `layout.stability`
- `navigation.orientation`
- `navigation.grouping`
- `tables.scanability`
- `tables.numeric-alignment`
- `tables.column-priority`
- `forms.labels`
- `forms.validation`
- `forms.submit-state`
- `a11y.accessible-name`
- `a11y.focus`
- `a11y.target-size`
- `responsive.mobile`
- `pattern.tile-vs-list`
- `pattern.cards-vs-table`
- `pattern.wizard-vs-single-page`
- `pattern.dashboard-vs-guided-flow`
- `conversion.choice-clarity`
- `conversion.cta-hierarchy`
- `conversion.value-visibility`
- `dispute.claim-framing`
- `dispute.context-missing`
- `states.loading`
- `states.empty`
- `states.error`

## SaaS And Operator UI Heuristics

Prioritize:

- fast scanning over visual drama
- clear object/action relationships
- stable dimensions for toolbars, tables, counters, and repeated items
- visible filters/sort/context for data screens
- aligned numbers and explicit units
- predictable navigation and back paths
- low-ambiguity destructive actions
- useful empty/error/loading states

Avoid recommending:

- decorative hero patterns for operational tools
- oversized cards where dense comparison is the task
- gradients/orbs/illustrations as a solution to hierarchy
- hiding important repeated actions behind vague icons without labels or tooltips
- a redesign that changes product semantics without evidence

## Pattern Fitness

Before judging visual styling, decide whether the chosen UI pattern fits the user's job.

Ask:

- What is the user trying to do: compare, choose, configure, monitor, buy, learn, recover, or repeat an operation?
- Is this a first-time persuasion/activation screen or a repeated-use production screen?
- Does the pattern make the next action obvious without hiding required information?
- Does the pattern support the amount and variability of content?
- Does mobile preserve the same decision quality, or does the pattern collapse into noise?
- Is the pattern chosen for the user goal, or because a stakeholder prefers how it looks?

Common defaults:

- Use tiles/cards when the user chooses among a small set of distinct options, each option benefits from a visual anchor, and comparison depth is low.
- Use lists when labels vary, users scan many options, order/ranking matters, or each row has a concise repeated structure.
- Use tables when users compare numeric/status fields across many entities.
- Use a guided flow when the user needs confidence, sequencing, or validation more than overview.
- Use a dense dashboard when repeated monitoring and exception handling are the job.

Reject a pattern when its visual form fights the task, even if the pattern looks modern.

## Conversion Ergonomics

Treat "sellability" as reduced cognitive friction, not decoration.

Check:

- The user can identify the offer, next action, and consequence of clicking without reading the whole screen.
- Primary CTA is visually dominant but not misleading.
- Secondary options are comparable: labels start from predictable positions, lengths do not create accidental visual priority, and supporting text has a stable rhythm.
- Button/card copy names outcomes, not internal features.
- Trust or proof elements support the decision instead of competing with the CTA.
- Mobile preserves the same decision order as desktop.

Do not assert "this will convert better" as fact unless there is data. Say "this is the stronger ergonomic default because..." and name the mechanism.

Good frontend "sells itself" when the user feels oriented, competent, and pulled toward the next useful action. That comes from fast comprehension, low ambiguity, credible value, and pleasant repeated use. It is not the same as visual novelty.

## Common Design Disputes

### Tile Layouts

Good default when:

- there are few options
- labels are short and similarly shaped
- each tile is a standalone choice rather than a comparison row
- an icon or strong visual anchor sits above the label
- the user is making a first-level category choice, not scanning a dense set

Risky when:

- labels vary in length
- each tile has title + description + metadata
- users must compare options quickly
- mobile wraps labels onto multiple lines
- the set is large, ordered, filterable, or data-heavy

Why: tiles create equal visual weight and spatial separation. That is useful for a small, distinct choice set; it is harmful when the user's real task is fast comparison, ranking, or scanning many similar items.

If tiles are appropriate, then evaluate internal alignment:

- centered text can work for short, symmetric labels
- variable title/body content usually needs a left-aligned text block for scanability
- icons can stay centered while text is aligned for comparison

Safer alternatives:

- center icon/visual, left-align title and body text
- keep one-line centered labels only for short action chips
- use fixed title height and line clamp
- group comparable text in a left-aligned content block inside equal-size tiles
- reserve centered alignment for hero/marketing emphasis, not dense choice comparison

## Rendered Evidence Checklist

For each relevant viewport:

- Screenshot is nonblank and loaded after app settles.
- Main task is visible without hunting.
- Text does not clip, overlap, or overflow its intended container.
- Page does not introduce unintended horizontal scroll.
- Primary and destructive actions are distinguishable.
- Interactive controls have accessible names and visible affordances.
- Touch/click targets are not cramped for primary controls.
- Text contrast clears WCAG AA where feasible; if automated pixel checks are unavailable, inspect visually and use computed colors as a fallback.
- Forms expose label, value, validation, loading, disabled, success, and error behavior where reachable.
- Tables preserve object identity and important columns at mobile/tablet widths or provide an intentional alternative.

## Output Rules

- Findings first.
- Evidence before opinion.
- One finding per distinct fix direction.
- Do not inflate severity for taste.
- Do not suppress business-requirement conflicts just because the UI looks polished.
- Mention unverified layers explicitly: browser not run, mobile not checked, authenticated state unavailable, API states not reachable, etc.
