---
name: route-to-correct-project
description: Use when requested implementation, debugging, review, contract propagation, task handoff, or git changes belong to a different saved Codex project/repo than the current thread, or when one task needs coordinated changes in multiple projects. Trigger when a bug is discovered from one project but must be fixed in another; when the user says the thread appears under the wrong project; when both producer and consumer projects need updates; or when the user asks to update, sync, hand off, create, assign, or send a follow-up task to the counterpart project. Interpret task-handoff phrases as routing into the correct project/thread by default, not merely drafting ticket text, unless the user explicitly asks for a text-only task description.
---

# Route To Correct Project

Use this skill as a routing guard before implementation. Its purpose is to keep code changes, branches, checks, and PR workflow inside the saved Codex project where the work actually belongs.

## When To Route

Route to a new thread when any of these are true:

- The current thread's project/repo is not the repo that must be edited.
- Investigation in one repo shows the fix belongs to another repo.
- The user says the thread is shown under the wrong project or asks to make the work visible in another project.
- A consumer-project fix is discovered while the current thread is in the producer/API/library project.
- The user asks to update or actualize the counterpart project after a contract/API/UI change, for example "update the frontend", "sync the backend contract", "hand this off to the API project", or "sync/update producer/consumer contracts".
- After investigation, the user asks to give, create, put, assign, hand off, or send a task to backend/frontend/counterpart work, for example "дай задачу на бэк", "поставь задачу на бэк", "закинь в бэк", "передай на бэк", "дай задачу на фронт", "поставь фронту", or "закинь во фронт". Treat this as operational routing to the correct Codex project/thread, not as a text-only ticket draft, unless the user explicitly asks only for wording.
- One task requires real changes in both the current project and a counterpart project, for example backend contract plus frontend consumption.
- A git branch would otherwise be created in a repo that is not the owner of the requested change.

Do not route for quick read-only inspection across repos. Route before edits, branch creation, commits, pushes, or PRs for the other project.

## Workflow

1. State the project boundary plainly:
   - current thread project/repo;
   - actual project/repo that owns the fix;
   - whether the current thread is only for investigation/coordination.

2. Stop implementation in the wrong project:
   - do not create a feature branch there;
   - do not edit files there for the other project's fix;
   - do not mix unrelated git state between repos.

3. Discover the correct saved project:
   - use the Codex thread tools, starting with project listing;
   - choose the saved project whose path/repo matches the owner of the fix;
   - ask the user only if multiple projects plausibly match and the correct one cannot be inferred from repo paths or conversation context.

4. Search for an existing thread for the same scope before creating a new one:
   - thread titles are not reliable and must never be treated as authoritative; use them only as weak display labels;
   - use thread listing/search with project names, repository names, `cwd` paths, recently touched files, endpoints, DTO/type names, branch/worktree names, ticket ids, and broad domain terms from the current task;
   - run at least one broad project/repo search and one domain/file/API search; narrow title-like searches are not enough;
   - read the most relevant candidates before deciding, prioritizing `cwd`, recent preview/messages, touched files, active worktree, and branch over title text;
   - prefer continuing an existing active/relevant counterpart thread over creating a duplicate only when it is the same delivery boundary.

5. If a matching thread exists, send the update there:
   - use a concise follow-up prompt with the new facts, contract changes, and requested next action;
   - preserve the target thread's existing branch/worktree ownership; do not ask it to create, rename, switch, rebase, or replace its branch unless the user explicitly requested that branch action for that target thread;
   - report the thread chosen and why it matched;
   - do not create a new thread for the same scope.

6. If several candidates look plausible and none is clearly best, ask the user to choose from a shortlist before sending any handoff or creating a new thread. Use structured user input when available. The shortlist must include:
   - thread title as a display label only;
   - thread id;
   - `cwd`/project;
   - one-line reason it might match, based on preview/messages/files/branch rather than title alone.

7. Create a separate Codex thread in the correct project only when no existing relevant thread is found or the user chooses to create a new one:
   - use a project target, not a projectless thread;
   - choose a worktree environment for implementation work;
   - start from the repo's fresh remote base when the target repo convention requires it;
   - include a compact prompt with the investigation facts, intended files, expected branch/workflow, and instruction not to commit unless explicitly asked.
   - do not choose low/mini/spark models for routed work; omit model unless the user explicitly requested one, and if setting reasoning explicitly use `high` or stronger.
   - if `create_thread` returns `pendingWorktreeId` instead of `threadId`, treat that pending worktree as the active routed attempt for this scope. Do not create another thread or pending worktree for the same scope.

8. In the current thread, report only the routing/handoff:
   - name the target project;
   - name the existing thread updated or include the created-thread directive after successful thread creation;
   - do not continue implementing the routed fix in the old thread unless the user explicitly overrides the workflow.

## Pending Worktree Guard

`pendingWorktreeId` means the app accepted thread creation but the target worktree is still being prepared. It is not yet a usable `threadId`, but it still counts as an active thread-creation attempt.

When a routed `create_thread` call returns `pendingWorktreeId`:

1. Do not call `create_thread` again for the same project, repo, scope, prompt correction, or delivery boundary.
2. If new facts or corrections arrive before a `threadId` is available, try to find the materialized thread with `list_threads` using:
   - a broad project/repo query;
   - domain/file/API terms from the prompt;
   - commit hashes, branch names, endpoint paths, or DTO names from the correction.
3. If a matching thread appears, use `read_thread` to confirm it is the pending worktree that materialized, then send the correction with `send_message_to_thread`.
4. If no matching thread appears yet, stop and report that only `pendingWorktreeId` is available and the correction cannot be safely delivered until the thread materializes. Ask the user whether to wait/retry, or tell them exactly what correction must be pasted into the target thread.
5. Never create a second pending worktree just to deliver a correction to the first pending worktree.

This guard overrides the normal "create a new thread when no matching thread is found" rule for the same scope. A pending worktree is not "no matching thread"; it is a not-yet-addressable matching thread.

## Multi-Project Fixes

When the task genuinely requires changes in both the current project and another saved project:

1. Keep the current thread responsible only for the current project.
2. Create or switch to the correct fresh branch in the current project before editing there.
3. Search for an existing counterpart thread for the same scope. Reuse it when it clearly matches.
4. If no matching thread exists, create a separate Codex thread in the counterpart project for its changes.
5. In the counterpart thread prompt or follow-up message, include the exact contract/change produced or expected in the current project.
6. Make each thread use its own repo-specific branch, checks, commits, and push/PR workflow.
7. In status updates, name which project each change belongs to and do not imply a change is done in both projects until both threads have produced their own evidence.

Do not silently edit both repos from one thread. Cross-repo read-only inspection is allowed, but each repo's writes and git state belong in its own project thread.

## Existing Thread Reuse

Before creating a new counterpart thread, search existing threads for the same scope. Use `list_threads` with multiple focused queries, then `read_thread` for likely candidates. Search terms should include:

- target project/repo name;
- user-facing feature name, page name, endpoint path, module name, ticket id, or branch name;
- important domain terms from the current investigation, in Russian and English when useful.

Thread names frequently do not match the current task. Treat a thread title as a hint only. A thread can be the right one even when the title names an older subtask, a symptom, a review item, or a different nearby report.

Treat a thread as reusable only when it is in the correct project and the recent summary, preview, `cwd`, touched files, branch, and current turn clearly match the same delivery boundary. Same repository, same feature area, same files, or same component is not enough by itself.

Use these positive reuse criteria:

- the user is clarifying or correcting the currently running task;
- the new facts change the same fix, contract, endpoint, bug, acceptance criteria, or verification plan;
- the existing branch and commit boundary should naturally include the new instruction;
- finishing the existing task without the new instruction would make that same deliverable wrong or incomplete.

Create a separate thread instead when the request is adjacent but independently deliverable:

- it is a new business requirement, even inside the same module or code area;
- it touches a different source event, handler, job, DTO, UI workflow, or test contour;
- it can be committed, reverted, tested, or reviewed independently;
- the existing thread is already actively fixing a different defect;
- the only reason to reuse is that the work is "nearby" or shares likely files.

If unsure whether a candidate is the same delivery boundary or merely nearby work, do not steer the existing thread silently. Ask the user to choose from a shortlist, or create a new thread and mention the related existing thread as context in the prompt.

When one candidate is clearly best after reading evidence, send a follow-up to that thread with `send_message_to_thread` instead of creating a new thread. Briefly report why that evidence, not the title, made it the chosen thread.

When two or more candidates are plausible, or when a broad project search finds candidate workstreams but the exact match is uncertain, ask the user to choose. Prefer structured `request_user_input` when available, with candidate thread titles, ids, cwd/project, and one-line relevance notes. If structured input is unavailable, ask a concise plain-text question and list the candidates.

Create a new thread only after the search finds no relevant active thread, or after the user explicitly chooses a new thread from the shortlist.

### Existing Thread Git Boundary

When reusing an existing thread, treat that thread's branch and worktree as owned by that thread.

Do not include instructions to:

- create a new branch;
- rename or replace the existing branch;
- switch away from the current branch;
- rebase/reset/cherry-pick to a different base;
- avoid a branch prefix that the target thread already uses;
- "fix" branch identity from the routing thread's perspective.

This applies even when the routing thread notices a branch name that looks stale, ugly, or contrary to the current repo convention. Branch correction is a separate task owned by the target thread and user, not by a cross-thread handoff.

Only mention branch state in an existing-thread follow-up when it is factual context needed for the task, and phrase it as evidence, not an instruction. If the branch appears wrong enough to block safe work, stop and ask the user whether to continue in that thread or create a new one. Do not steer the target thread into a branch change silently.

Branch expectations and fresh-base requirements belong only in `create_thread` prompts for newly created worktrees, or in the current thread when the user explicitly asked this thread to create/switch branches.

Do not use low-effort routing or low-model handoffs for counterpart project work. For `send_message_to_thread`, `create_thread`, or similar thread-steering calls, omit model by default so the target keeps the configured model. If a reasoning override is necessary, use `high` or stronger; never set `low`, `medium`, mini, or spark for these routed implementation/review tasks.

## Prompt Content For A New Thread

Use this section only when creating a new thread or pending worktree with `create_thread`. Do not apply these branch instructions to `send_message_to_thread` follow-ups for existing threads.

The new-thread prompt should include:

- user-facing task in one sentence;
- exact repo/project that owns the change;
- evidence already gathered, separated from assumptions;
- files or modules likely involved;
- branch expectations, including fresh-base requirements;
- validation expectations;
- explicit instruction to answer in the user's language;
- explicit instruction not to commit or push unless the user asks.

Keep the prompt short enough to be actionable. Do not paste large logs unless they are necessary.

## Counterpart Contract Updates

When the user's request means "take what we just changed or discovered here and update the other side", route the work into the counterpart project instead of asking the user to copy-paste a contract manually. Reuse an existing matching counterpart thread when it is the same delivery boundary; create a new thread only when no matching thread exists or the user chooses a new one.

Task-handoff wording is included in this rule. Russian phrases like "дай задачу на бэк", "поставь задачу фронту", "закинь в бэк", or "передай на фронт" mean route the concrete follow-up into the counterpart Codex project/thread by default. Only return a standalone written task when the user explicitly asks for a text-only ticket, issue description, or wording.

Common mappings:

- Producer/API contract changed or was diagnosed -> route to the relevant consumer project, reusing a matching thread before creating a new one.
- Consumer UI or integration work requires a producer contract, endpoint, DTO, permission, or payload change -> route to the producer project, reusing a matching thread before creating a new one.
- If multiple consumer projects can own the work, ask the user to choose from a shortlist before creating or updating a thread.

The handoff prompt for counterpart updates must include the concrete contract, not only a prose summary:

- endpoint path and method;
- request payload shape;
- response payload shape;
- enum/status values and date semantics;
- permission/auth expectation;
- files already inspected;
- exact frontend/backend behavior expected after the update.

If the current thread has enough evidence to identify the counterpart project, use that project for search, but still apply the existing-thread shortlist protocol before creating or choosing a thread. If there are multiple plausible frontend projects, contract owners, or existing project threads, ask the user to choose before sending a handoff or creating a thread.

## Interaction With Other Skills

This skill routes the work. Once a new thread exists, that new thread should use the repo-specific skills and git workflow normally, such as fresh branch creation, frontend checks, backend checks, push gate, or review skills. Existing reused threads keep their own established git workflow and branch ownership.

If the user explicitly asks to continue in the current thread despite the project mismatch, state the risk once and then follow their direction.
