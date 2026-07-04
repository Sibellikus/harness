#!/usr/bin/env node

const fs = require("fs");

const severityRanks = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
  p3: 1,
  p2: 2,
  p1: 3,
  p0: 4
};

function usage() {
  console.error("Usage: evaluate_deep_review_output.js --cases <cases.json> --case-id <id> --output <output.md>");
  process.exit(2);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key.startsWith("--") || value === undefined || value.startsWith("--")) {
      usage();
    }
    args[key.slice(2)] = value;
    i += 1;
  }
  if (!args.cases || !args["case-id"] || !args.output) {
    usage();
  }
  return args;
}

function normalize(text) {
  return text.toLowerCase().replace(/\s+/g, " ");
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function containsTerm(output, term) {
  const haystack = normalize(output);
  const needle = normalize(term);
  if (/^[a-z0-9]+$/.test(needle) && needle.length <= 3) {
    return new RegExp(`(^|[^a-z0-9])${escapeRegExp(needle)}([^a-z0-9]|$)`, "i").test(haystack);
  }

  return haystack.includes(needle);
}

function containsAll(output, terms) {
  return (terms || []).map((term) => {
    const ok = containsTerm(output, term);
    return { term, ok };
  });
}

function maxSeverity(output) {
  const haystack = normalize(output);
  let max = 0;
  for (const [label, rank] of Object.entries(severityRanks)) {
    const pattern = new RegExp(`(^|[^a-z0-9])${label}([^a-z0-9]|$)`, "i");
    if (pattern.test(haystack)) {
      max = Math.max(max, rank);
    }
  }
  return max;
}

function evaluateFinding(output, finding) {
  const mentionChecks = containsAll(output, finding.must_mention);
  const boundaryChecks = containsAll(output, finding.owning_boundary_terms);
  const evidenceChecks = containsAll(output, finding.evidence_paths);
  const forbiddenChecks = containsAll(output, finding.forbidden_claims || []).map((x) => ({
    term: x.term,
    ok: !x.ok
  }));
  const severityFloor = severityRanks[String(finding.severity_min || "low").toLowerCase()] || 1;
  const severityOk = maxSeverity(output) >= severityFloor;

  return {
    id: finding.id,
    critical_recall: mentionChecks.every((x) => x.ok),
    boundary_accuracy: boundaryChecks.every((x) => x.ok),
    evidence_quality: evidenceChecks.every((x) => x.ok),
    false_positive_pressure: forbiddenChecks.every((x) => x.ok),
    severity_floor: severityOk,
    details: {
      missing_mentions: mentionChecks.filter((x) => !x.ok).map((x) => x.term),
      missing_boundary_terms: boundaryChecks.filter((x) => !x.ok).map((x) => x.term),
      missing_evidence_paths: evidenceChecks.filter((x) => !x.ok).map((x) => x.term),
      forbidden_claims_present: forbiddenChecks.filter((x) => !x.ok).map((x) => x.term),
      severity_min: finding.severity_min,
      observed_severity_rank: maxSeverity(output)
    }
  };
}

function main() {
  const args = parseArgs(process.argv);
  const suite = JSON.parse(fs.readFileSync(args.cases, "utf8"));
  const testCase = suite.cases.find((x) => x.id === args["case-id"]);
  if (!testCase) {
    console.error(`Case not found: ${args["case-id"]}`);
    process.exit(2);
  }

  const output = fs.readFileSync(args.output, "utf8");
  const findingResults = testCase.expected_findings.map((finding) => evaluateFinding(output, finding));
  const metrics = {
    critical_recall: findingResults.every((x) => x.critical_recall),
    boundary_accuracy: findingResults.every((x) => x.boundary_accuracy),
    evidence_quality: findingResults.every((x) => x.evidence_quality),
    false_positive_pressure: findingResults.every((x) => x.false_positive_pressure),
    severity_floor: findingResults.every((x) => x.severity_floor)
  };
  const passed = Object.values(metrics).every(Boolean);

  const result = {
    suite: suite.suite,
    case_id: testCase.id,
    target_skill: testCase.target_skill,
    commit: testCase.commit,
    base: testCase.base,
    passed,
    metrics,
    findings: findingResults
  };

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  process.exit(passed ? 0 : 1);
}

main();
