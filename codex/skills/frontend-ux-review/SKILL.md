---
name: frontend-ux-review
description: Review frontend UI ergonomics, readability, information hierarchy, accessibility baseline, responsive behavior, tables, forms, dashboards, and rendered screens. Use when the user asks to review UI/UX/design/readability, assess whether an interface is ergonomic, inspect frontend screenshots or local/remote app screens, review a frontend diff for user-facing regressions, or find practical UI issues before shipping. Prefer evidence-backed findings over generic design advice.
---

# Frontend UX Review

Use this as a product-design review skill, not as a redesign generator or CSS polish checklist. The output should help a product/frontend engineer decide what to fix, and help stakeholders resolve UI disputes without relying on taste, role authority, or "I like it this way."

Core rule: findings first, evidence-based, business-oriented. Do not give generic taste advice such as "make it cleaner" unless it is tied to a specific user task, screen, viewport, selector, screenshot, or code path.

Product ergonomics comes before component styling. First decide whether the interface pattern fits the user goal, information structure, frequency of use, and sales/activation moment. Only then discuss alignment, spacing, color, or copy inside that pattern.

## Depth Modes

Choose the lightest mode that can answer the request.

### Quick Review

Use when the user provides code, a diff, a screenshot, a specific component, or a stakeholder dispute but no running app URL.

- Read the relevant UI code and existing design patterns.
- Inspect labels, layout decisions, state handling, table/form behavior, and responsive constraints from code.
- If screenshots are provided, treat them as evidence.
- Do not start a dev server unless the user asked for rendered verification or the repo workflow naturally requires it.

### Rendered Review

Use when a local/remote URL is available, after significant frontend changes, or when the user asks whether the actual screen is readable/usable.

- Open the screen with Browser/Playwright.
- Capture at least desktop and mobile viewports when responsive behavior matters.
- Check visible hierarchy, clipping/overflow, contrast, target sizes, form labels, empty/loading/error states where reachable, and whether the main workflow can be scanned.
- Use `scripts/rendered-probe.mjs` only when a deterministic DOM/screenshot report is useful. It is optional, not a required pipeline.

### Deep Flow Audit

Use only when the user names a workflow or asks for a thorough UX audit.

- Walk the real flow: navigation, filters, forms, validation, submit, loading, success, empty/error states, and back/restore behavior.
- Scope the audit to named screens or workflows. Do not crawl the whole app by default.

### Design Dispute Review

Use when stakeholders disagree about a UI choice such as tile vs list layout, wizard vs one-page form, dashboard vs guided empty state, card density, CTA hierarchy, centered vs left-aligned labels, button copy, hero layout, or "what sells better."

- Translate preferences into testable UX claims: scan speed, comprehension, choice confidence, perceived affordance, error risk, and conversion friction.
- Start at the pattern level: is this a comparison problem, a navigation problem, a sales/activation problem, a repeated-work operator screen, or a one-time onboarding choice?
- State which context changes the answer: number of options, information density, user expertise, repeated use vs first-time landing, mobile width, icon presence, and whether users compare options or choose one.
- Prefer "best default under these constraints" over universal rules.
- If conversion is the claim, separate ergonomics from marketing taste: a UI sells better when it reduces ambiguity, exposes value, and makes the next action obvious. Do not claim a conversion lift without analytics, A/B data, or a clear behavioral mechanism.
- If the dispute is between CEO/CTO/SEO/engineering preferences, treat those as inputs, not authority. Decide from user task, product intent, design heuristics, and evidence.

## Workflow

1. **Freeze scope.** Name the screen, flow, component, or diff being reviewed. If the request is broad, keep the first pass to the highest-risk user path.
2. **Identify the product job.** Decide what the screen is for: sell/activate, choose, compare, configure, monitor, recover, or repeat work.
3. **Check pattern fitness first.** Before judging styling, ask whether the chosen page/component patterns match that job. If a tile/card/table/wizard/dashboard pattern is wrong, report that as a primary finding.
4. **Gather evidence.** Prefer real rendered screenshots/DOM facts when available. Otherwise use code and provided screenshots.
5. **Compare against product intent.** SaaS/operator tools should optimize scanning, comparison, repeated action, and low ambiguity. Avoid marketing-style hero/layout advice unless the screen is actually a marketing page.
6. **Emit findings.** Use the report contract in `references/review-rubric.md`.
7. **Separate fixes from taste.** A finding needs a user impact and a concrete fix direction.

## What To Check

- **Readability:** text size, line length, density, contrast, truncation, number formatting, units, labels, visual rhythm.
- **Hierarchy:** primary task is visually obvious; secondary actions do not compete; headings match the user's mental model.
- **Layout:** no accidental overlap, clipping, horizontal scroll, card-inside-card clutter, unstable dimensions, or cramped controls.
- **Tables and dense data:** sticky context where useful, aligned numbers, sortable/filterable affordances, row scanning, empty/loading/error states, column priority on mobile.
- **Forms:** labels, required/optional clarity, validation timing, error placement, disabled/loading states, destructive confirmation, keyboard path.
- **Navigation:** current location, back path, breadcrumbs/tabs, predictable grouping, no hidden critical action.
- **Accessibility baseline:** contrast, focus visibility, semantic controls, accessible names, touch target size, reduced-motion concerns where motion exists.
- **Responsive behavior:** mobile layout preserves task priority; controls do not wrap into unreadable shapes; text and actions remain reachable.
- **Conversion ergonomics:** value proposition and primary CTA are easy to find, choice sets are comparable, copy is specific, and visual treatment reduces hesitation rather than adding decoration.
- **Pattern fitness:** selected UI pattern matches the job: compare, choose, configure, monitor, purchase, learn, recover, or repeat.

## Rendered Probe

Optional helper:

```bash
node "$CODEX_HOME/skills/frontend-ux-review/scripts/rendered-probe.mjs" http://localhost:3000/path --out /tmp/frontend-ux-review
```

The script writes screenshots and `frontend-ux-report.json`. It uses Playwright and can optionally use `pngjs` for pixel-sampled contrast. If `pngjs` is unavailable, it still reports DOM-based findings.

Run it from a frontend repo that already has Playwright installed, or use Browser/manual screenshots instead. Do not install browser tooling just to satisfy a quick review unless rendered evidence is actually needed.

Use the script output as evidence, then apply judgment. Do not blindly paste every automated warning.

## Output Shape

Lead with findings, ordered by severity. Use concrete references:

```text
[High] pattern.tile-vs-list - The page uses equal-weight tiles for a task that requires fast comparison across many similar options.
Evidence: screenshot path or component file, option count, content variability, viewport if relevant.
Impact: users must read each tile separately instead of scanning a stable structure, which increases choice friction and weakens activation.
Fix: replace the tile grid with a grouped list/table, or reserve tiles only for the first-level category choice and move detailed comparison into a scan-friendly layout.

[High] layout.overflow - Mobile 390px: primary action text clips in the order toolbar.
Evidence: screenshot path or selector, viewport, relevant file/line if known.
Impact: user cannot reliably identify the action during repeated order review.
Fix: keep the primary action text, move secondary actions behind icon buttons/menu, and give the toolbar stable wrapping rules.
```

If no issues are found, say that clearly and list residual risk, such as "not verified in a real browser" or "flow states beyond the initial screen were out of scope."

## References

- Read `references/review-rubric.md` when producing a formal review, adapting an automated report, or doing a deep flow audit.
