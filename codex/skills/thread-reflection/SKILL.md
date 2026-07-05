---
name: thread-reflection
description: Run a post-delivery or post-push reflection for a completed business task in the current thread or an archived thread file. Use when the user asks for reflection, retrospective, ретро, рефлексию, postmortem, lessons learned, what helped or slowed the task, or how to codify repeated workflow learnings into skills, AGENTS.md, memory, or agent behavior.
---

# Thread Reflection

## Overview

Produce one concise, evidence-backed reflection after delivery work, usually after a push or PR. The subject of the reflection is the business task that was being delivered: its goal, decisions, implementation path, blockers, and delivery result. Skills, AGENTS.md, memory, and agent workflow are not the object of reflection; mention them only as places to codify a lesson when they materially helped or slowed the business task.

The reflection must always run through a neutral Thread Map phase first. The Thread Map is an evidence index, not a judgment or final summary.

## Core Rules

- Treat this as business-delivery process analysis, not code review and not skill review. Do not reopen the implementation unless the reflection requires a concrete example.
- Be direct. Do not flatter the agent, the workflow, or the user.
- Separate observed facts from inferred causes.
- Prefer thread evidence, command outcomes, git state, changed files, and applicable instructions over generic productivity advice.
- Do not update memories, skills, AGENTS.md, or repo files unless the user explicitly asks for follow-up edits.
- Do not expose intermediate scout/subagent output. Return one synthesized reflection.
- If the task did not actually reach push/delivery, say so and reflect on the completed portion plus the remaining blocker.
- Do not make "skill reflection" a standalone topic unless the user explicitly asks to evaluate a skill itself. Default to business-task reflection first; then add concrete codification recommendations only for lessons that should change skills, AGENTS.md, memory, or agent behavior.
- For current-thread reflection, do not spawn subagents by default. The active context is already available; forking it usually adds cost and noise without improving evidence.
- For archived-thread reflection, use one isolated archive reflection worker when subagent tooling is available. The main thread should receive only the final ThreadReflection by default, not the raw archive and not the full ThreadMap.

## Evidence Intake

Gather only what is needed for the reflection:

- User's original business ask, later corrections, final requested outcome, and delivered result.
- Major turning points: business semantics clarified, ownership/storage/API decisions, implementation, review, tests, push, PR, blockers, reversals.
- Planning evidence:
  - whether there was an explicit `shape` / plan skill run;
  - if not, what informal or mini-plan still existed in assistant messages or execution order;
  - where the plan missed business invariants, ownership, contracts, lifecycle, storage, tests, or stop conditions;
  - whether the final code diverged from the initial requirements/doc/transcript and why.
- Review evidence:
  - whether `deep-review` was invoked;
  - how many times it was invoked and at which task phases;
  - why it was invoked repeatedly, if it was;
  - whether repeated deep-review calls indicate missing planning, unclear invariants, unstable implementation, or genuinely high-risk surface.
- Skills or agent mechanisms only when they materially affected delivery or are a good codification target for a repeated lesson.
- Applicable instruction sources:
  - current thread system/developer instructions;
  - project `AGENTS.md` content supplied in context;
  - local `AGENTS.md` files and linked docs when cheap to inspect;
  - repo scripts or skill contracts that constrained the work.
- Git evidence when relevant: branch/base, commits, push/PR result, dirty state, and files touched.

Use `rg`/`sed`/`git` for local evidence. Avoid full build/test logs and long transcript dumps.

When judging whether an instruction, skill, or agent rule should change, run a targeted rule search before concluding:

- Derive search terms from the task surface: branch, push, test, migration, Mongo, frontend, backend, API, DTO, auth, fallback, or the changed feature/domain names.
- Search applicable `AGENTS.md` and linked workflow docs for those terms.
- If the rule exists, classify the problem as discoverability, timing, contradiction, or ignored behavior, and tie it back to the business task impact.
- If the rule does not exist, classify it as a missing-rule candidate only when the failure was repeated, costly, or likely to recur in future business delivery.

## Source Modes

### Current Thread Mode

Use this mode when reflecting on the active task in the current conversation.

- Do not spawn subagents by default.
- Build the Thread Map directly from the active context.
- Use targeted local evidence checks (`git`, `rg`, `sed`, PR state, commit state) only when needed to verify concrete facts.
- Then run reflection and codification in the same active thread.

### Archive Mode

Use this mode when reflecting on a different archived thread, usually a file under `${CODEX_HOME:-$HOME/.codex}/archived_sessions/*.jsonl`.

- Spawn one isolated archive reflection worker when subagent tooling is available.
- Give the worker the archive path and any target task hint. Do not paste the archive into the main thread.
- The worker must run all phases internally: Thread Map, coverage check, targeted reread, reflection, codification.
- The worker returns only the final ThreadReflection by default. It may include minimal metadata such as archive file, confidence, task segments, and raw evidence ranges consulted.
- If the user explicitly asks for the Thread Map, the worker may return a compact map plus evidence pointers. Otherwise keep the map internal.
- If subagent tooling is unavailable, return a `BLOCKER` for archive mode unless the user explicitly approves a local no-subagent fallback.

## Reflection Phases

Run these phases in order for both current-thread and archive modes.

### 1. Neutral Thread Map

Build an evidence-indexed map of the business task. This is not a final reflection and must avoid judgments.

Capture:

```text
ThreadMap
- source:
- task_segments:
- original_business_ask:
- final_business_outcome:
- user_corrections:
- decisions:
- decision_changes:
- abandoned_approaches:
- planning_moments:
- deep_review_invocations:
- implementation_facts:
- delivery_facts:
- unresolved_or_dirty_state:
- evidence_ledger:
- unclear_or_conflicting_points:
```

Rules:

- Store evidence pointers for important claims: turn, timestamp, command, file, PR, commit, jsonl event id, or nearby text marker.
- Use neutral labels such as `decision_changes`, `abandoned_approaches`, and `user_corrections`; do not label them as mistakes in the map.
- Preserve task segmentation when a long thread contains multiple business tasks or a technical tail after the business task.
- Include short user phrasing for key business invariants when it prevents meaning drift.

### 2. Coverage Check

Before reflection, check whether the map likely missed important details:

- all explicit user corrections are represented;
- all final delivery facts are represented;
- all planning moments, including informal mini-plans, are represented;
- all `deep-review` invocations and review-like passes are represented;
- late technical work did not obscure the original business task;
- unclear or conflicting points are marked as unclear instead of silently resolved.

For archive mode, use the map's evidence pointers to reread targeted raw sections before finalizing reflection.

### 3. Reflection

Evaluate the mapped facts:

- what helped business delivery;
- what accelerated implementation;
- what slowed or blocked delivery;
- where planning missed important invariants, ownership, contracts, lifecycle, storage, tests, or stop conditions;
- why `deep-review` was invoked as often as it was;
- whether repeated `deep-review` indicates task risk or weak planning;
- whether final code can serve as benchmark/eval evidence for future planning from initial docs, transcripts, or requirements.

### 4. Codification

Recommend only changes that would improve future business delivery:

- planning skill changes;
- deep-review handoff changes;
- AGENTS.md changes;
- memory candidates;
- agent behavior changes.

Do not write memories, skills, AGENTS.md, or repo files unless the user explicitly asks for follow-up edits.

## Codification Guidance

Include codification guidance only after the business-task reflection. This section answers: "What should we change in skills, AGENTS.md, memory, or agent habits so future business tasks go better?"

Check:

- `Skill change`: only if a skill caused a real delivery problem or can encode a repeated lesson.
- `Planning skill change`: if the final code shows that the initial plan should have captured additional business invariants, storage boundaries, endpoint contracts, lifecycle effects, tests, or review stop conditions. Treat the final delivered implementation as benchmark evidence for future plan quality.
- `Deep-review change`: if deep-review was invoked repeatedly, late, or for issues that better planning should have prevented. Recommend a change only when the review pattern points to a reusable planning/review handoff lesson.
- `AGENTS.md change`: only if a project rule was missing, ignored, too hard to find, or should be placed closer to the work surface.
- `Memory change`: only if the user explicitly asks to persist the lesson; otherwise say it is a candidate. Reflection may recommend an exact memory note, but must not write memory by itself.
- `Agent behavior change`: a concrete habit for next time, such as "freeze business invariant before endpoint shape."
- `No change`: if the lesson is specific to this task and not worth codifying.

Do not treat skills or AGENTS.md as topics to grade. Judge them only by their impact on the business task and by whether a concrete codification change would prevent a similar failure.

If AGENTS.md or project instructions were present, include a short AGENTS.md-oriented check inside codification guidance:

- `used well`: rule or instruction that materially helped delivery.
- `missed or late`: rule that applied but was not used soon enough, with business impact.
- `missing`: rule that would have prevented a repeated or costly delivery issue.
- `size/placement impact`: only if length or placement caused a concrete miss or delay.
- `suggested edit`: the smallest useful wording/placement change, or `None`.

## Output Contract

Return this shape unless the user asks for a different format:

```text
ThreadReflection
1. Outcome
2. What Helped
3. What Made It Fast
4. What Slowed or Blocked It
5. Planning and Review Signals
6. Business Lessons
7. Codification Recommendations
8. Next-Time Changes
```

Keep the result compact. Each claim should point to concrete evidence or be marked as inference.

For `Codification Recommendations`, use this shape:

```text
- skills:
- AGENTS.md:
- memory:
- agent behavior:
```

For `Planning and Review Signals`, cover:

```text
- planning:
- deep-review:
- benchmark/eval candidate:
```

If there were no meaningful issues in a section, say `None found from this thread evidence`.

## Quality Gate

Before finalizing, check:

- Does the answer start from the business task and delivered business outcome, not from skills or agent internals?
- Does it include what helped, what accelerated success, and what slowed the business delivery?
- Does it explicitly cover planning quality, including informal planning when no plan skill was used?
- Does it explicitly cover deep-review frequency, timing, and why it was needed that many times?
- Does it identify whether final code can be used as benchmark/eval evidence for improving planning from initial docs/transcripts/requirements?
- Does it translate only relevant learnings into concrete skill/AGENTS.md/memory/agent-behavior recommendations?
- If AGENTS.md was present, does it mention rule use/miss/missing/size-placement only where it affected delivery?
- Are claims grounded in this thread rather than generic agent advice?
- Are speculative improvements labeled as suggestions, not facts?
- Is the output one synthesized reflection, not raw scout notes?
