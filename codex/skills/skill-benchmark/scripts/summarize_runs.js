#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

function usage() {
  console.error("Usage: summarize_runs.js --run-dir <dir>");
  process.exit(2);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] !== "--run-dir" || !argv[i + 1]) {
      usage();
    }
    args.runDir = argv[i + 1];
    i += 1;
  }
  if (!args.runDir) usage();
  return args;
}

function readScores(runDir) {
  if (!fs.existsSync(runDir)) {
    throw new Error(`Run dir does not exist: ${runDir}`);
  }

  const results = [];
  for (const entry of fs.readdirSync(runDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const scorePath = path.join(runDir, entry.name, "score.json");
    if (!fs.existsSync(scorePath)) {
      results.push({
        case_id: entry.name,
        passed: false,
        missing_score: true,
        score_path: scorePath
      });
      continue;
    }

    const score = JSON.parse(fs.readFileSync(scorePath, "utf8"));
    results.push({
      ...score,
      score_path: scorePath,
      raw_output_path: path.join(runDir, entry.name, "raw-output.md")
    });
  }
  return results.sort((a, b) => String(a.case_id).localeCompare(String(b.case_id)));
}

function main() {
  const args = parseArgs(process.argv);
  const cases = readScores(args.runDir);
  const metricNames = [
    "critical_recall",
    "boundary_accuracy",
    "evidence_quality",
    "false_positive_pressure",
    "severity_floor"
  ];

  const totals = {
    cases: cases.length,
    passed: cases.filter((x) => x.passed).length,
    failed: cases.filter((x) => !x.passed).length,
    metrics: {}
  };

  for (const metric of metricNames) {
    const measured = cases.filter((x) => x.metrics && metric in x.metrics);
    totals.metrics[metric] = {
      passed: measured.filter((x) => x.metrics[metric]).length,
      measured: measured.length
    };
  }

  process.stdout.write(JSON.stringify({
    run_dir: args.runDir,
    passed: totals.failed === 0 && totals.cases > 0,
    totals,
    cases
  }, null, 2));
  process.stdout.write("\n");
}

main();
