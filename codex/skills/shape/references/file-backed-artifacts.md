# File-Backed Artifacts

Plan pipeline must keep long-lived planning state in files, not in chat context.

## Artifact Location

Default to a task-local directory:

```text
.shape/
  implementation-spec.md
  questions.md
  agent-runs/
```

If the repository already has an obvious planning/spec location requested by the user, use it and record the chosen path in the chat result.

## Templates

Use these skill-bundled templates when creating new artifacts:

- [../assets/implementation-spec.template.md](../assets/implementation-spec.template.md)
- [../assets/questions.template.md](../assets/questions.template.md)

Do not paste the templates into chat. Create or update the files in the task workspace.

## Ownership

The orchestrator owns writes to:

- `implementation-spec.md`
- `questions.md`

Subagents do not edit these files directly. They return structured results to the orchestrator. If raw output must be preserved, write it under `agent-runs/` and link to it from `Evidence`.

## Main Plan File

`implementation-spec.md` is the authoritative planning artifact. It contains:

- selected mode;
- `RiskScan`;
- scout execution log;
- `ResearchPlanDossier` or `HardenedTaskHandoff`;
- accepted decisions;
- compact index of open question IDs;
- reviewer output for deep runs;
- final verdict and next action.

## Questions File

`questions.md` is the clarification queue. It stores detailed open and answered questions.

Rules:

- Put every material open decision in `DecisionQuestionMatrix` and mirror its ID in `questions.md`.
- The user answers in chat or voice; do not require manual file edits.
- Normalize the user's answer into `Answer`, `Source`, and `Impact on spec`.
- If transcription is ambiguous, ask a narrow follow-up before writing an accepted decision.
- After an answer is accepted, update `questions.md` and transfer the decision into `implementation-spec.md`.

## Subagent Result Shape

Subagents return this structure to the orchestrator:

```text
SubagentResult
- status: completed | blocked | partial
- scope:
- findings:
- evidence:
- decisions_suggested:
- open_questions:
- suggested_spec_update:
```

The orchestrator validates and writes accepted content into the artifacts.

## Chat Result

The final chat response is a compact pointer, not the plan body:

```text
ShapeChatResult
- mode:
- verdict:
- plan_artifact:
- questions_artifact:
- open_question_ids:
- accepted_decision_ids:
- next_action:
```

If the user explicitly asks to inspect a section, quote only that section or point to the file path.
