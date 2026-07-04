# Benchmark Case Schema

Cases are JSON objects stored in a suite file:

```json
{
  "suite": "deep-review/example",
  "cases": [
    {
      "id": "stable-case-id",
      "target_skill": "deep-review",
      "repo_hint": "example-repo",
      "commit": "reviewed commit",
      "base": "base commit",
      "mode": "backend",
      "expected_findings": []
    }
  ]
}
```

## Required Case Fields

- `id`: stable hyphen-case id.
- `target_skill`: target skill being benchmarked, for example `deep-review`.
- `commit`: Git commit to review.
- `base`: Git base for the review.
- `mode`: expected review mode, such as `backend`, `frontend`, or `mixed`.
- `expected_findings`: one or more semantic gold findings.

## Expected Finding Fields

- `id`: stable finding id inside the case.
- `severity_min`: `low`, `medium`, `high`, or `critical`.
- `invariant_class`: semantic class that must be represented by the output.
- `owning_boundary_terms`: terms that prove the output found the right owner.
- `must_mention`: domain terms or symbols that must appear.
- `evidence_paths`: file names, paths, or symbols that must appear.
- `forbidden_claims`: claims that indicate the output found the wrong issue or overreached.

Use terms that are stable across harmless rewrites. Avoid exact full sentences from old review output.

## Optional Case Fields

- `session_logs`: local JSONL logs that explain why the case exists.
- `notes`: short operator notes.
- `tags`: topic tags for filtering.

Do not put chain-of-thought, private reasoning, or large historical transcripts in a case. Link logs and keep gold data compact.
