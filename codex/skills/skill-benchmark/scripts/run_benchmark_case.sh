#!/usr/bin/env bash
set -euo pipefail

CASES=""
CASE_ID=""
REPO=""
CHECKOUT="false"
RUN_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cases)
      CASES="$2"
      shift 2
      ;;
    --case-id)
      CASE_ID="$2"
      shift 2
      ;;
    --repo)
      REPO="$2"
      shift 2
      ;;
    --run-dir)
      RUN_DIR="$2"
      shift 2
      ;;
    --checkout)
      CHECKOUT="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$CASES" || -z "$CASE_ID" || -z "$REPO" ]]; then
  echo "Usage: run_benchmark_case.sh --cases <cases.json> --case-id <id> --repo <repo> [--run-dir <dir>] [--checkout]" >&2
  exit 2
fi

node - "$CASES" "$CASE_ID" "$REPO" "$CHECKOUT" "$RUN_DIR" <<'NODE'
const fs = require("fs");
const { execFileSync } = require("child_process");
const path = require("path");

const [casesPath, caseId, repo, checkout, runDirInput] = process.argv.slice(2);
const suite = JSON.parse(fs.readFileSync(casesPath, "utf8"));
const testCase = suite.cases.find((x) => x.id === caseId);
if (!testCase) {
  console.error(`Case not found: ${caseId}`);
  process.exit(2);
}

function git(args) {
  return execFileSync("git", args, { cwd: repo, encoding: "utf8" }).trim();
}

git(["cat-file", "-e", `${testCase.commit}^{commit}`]);
git(["cat-file", "-e", `${testCase.base}^{commit}`]);

if (checkout === "true") {
  const status = git(["status", "--porcelain"]);
  if (status) {
    console.error("Refusing checkout: repository has uncommitted changes.");
    process.exit(1);
  }
  git(["switch", "--detach", testCase.commit]);
}

const runDir = runDirInput || path.join("/tmp/skill-benchmark", new Date().toISOString().replace(/[:.]/g, "-"));
const caseDir = path.join(runDir, testCase.id);
const rawOutputPath = path.join(caseDir, "raw-output.md");
const scorePath = path.join(caseDir, "score.json");
const workerLogPath = path.join(caseDir, "worker.log");
const codexHome = process.env.CODEX_HOME || path.join(process.env.HOME || "", ".codex");
const evaluatorPath = path.join(codexHome, "skills", "skill-benchmark", "scripts", "evaluate_deep_review_output.js");

const prompt = [
  `Use $${testCase.target_skill} to run benchmark case ${testCase.id}.`,
  ``,
  `Repository: ${repo}`,
  `Benchmark case: ${testCase.id}`,
  `Commit under review: ${testCase.commit}`,
  `Base: ${testCase.base}`,
  `Expected mode: ${testCase.mode}`,
  `Run directory: ${caseDir}`,
  `Raw output path: ${rawOutputPath}`,
  `Score path: ${scorePath}`,
  `Worker log path: ${workerLogPath}`,
  ``,
  `Required order:`,
  `1. Verify the worker worktree is clean. If it is dirty, stop and report the dirty state.`,
  `2. Checkout the commit under review in detached HEAD: git switch --detach ${testCase.commit}.`,
  `3. Run the target skill review against base ${testCase.base}. Do not read or inspect benchmark expected_findings before the raw review is complete.`,
  `4. Save the full target-skill review output to ${rawOutputPath}.`,
  `5. Run: node "${evaluatorPath}" --cases "${casesPath}" --case-id "${testCase.id}" --output "${rawOutputPath}" > "${scorePath}".`,
  `6. Return a compact final status with pass/fail, ${rawOutputPath}, ${scorePath}, and the score JSON.`
].join("\n");

console.log(JSON.stringify({
  suite: suite.suite,
  case_id: testCase.id,
  target_skill: testCase.target_skill,
  commit: testCase.commit,
  base: testCase.base,
  checked_out: checkout === "true",
  run_dir: runDir,
  case_dir: caseDir,
  raw_output_path: rawOutputPath,
  score_path: scorePath,
  worker_log_path: workerLogPath,
  prompt
}, null, 2));
NODE
