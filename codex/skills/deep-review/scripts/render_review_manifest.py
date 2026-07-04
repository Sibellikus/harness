#!/usr/bin/env python3
"""Render a deep-review artifact referenced by a short terminal manifest."""

from __future__ import annotations

import argparse
import os
import shlex
import sys

from render_review_artifact import ArtifactError, render_artifact, require_dict

import json


class ManifestError(Exception):
    pass


def parse_manifest(raw: str) -> dict[str, str]:
    line = raw.strip()
    if not line:
        raise ManifestError("manifest is empty")
    parts = shlex.split(line)
    if not parts or parts[0] != "ARTIFACT_READY":
        raise ManifestError("manifest must start with ARTIFACT_READY")
    result: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            raise ManifestError(f"invalid manifest token: {part}")
        key, value = part.split("=", 1)
        result[key] = value
    if "artifact_path" not in result:
        raise ManifestError("artifact_path is missing")
    if "result" not in result:
        raise ManifestError("result is missing")
    return result


def validate_artifact_path(path: str) -> str:
    if not os.path.isabs(path):
        raise ManifestError("artifact_path must be absolute")
    normalized = os.path.realpath(path)
    marker = f"{os.sep}.codex{os.sep}tmp{os.sep}deep-review{os.sep}"
    if marker not in normalized:
        raise ManifestError("artifact_path must be under .codex/tmp/deep-review")
    if not os.path.isfile(normalized):
        raise ManifestError("artifact_path does not exist")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", help="Manifest string. Reads stdin when omitted.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    raw_manifest = args.manifest if args.manifest is not None else sys.stdin.read()
    try:
        manifest = parse_manifest(raw_manifest)
        artifact_path = validate_artifact_path(manifest["artifact_path"])
        with open(artifact_path, "r", encoding="utf-8") as handle:
            artifact = require_dict(json.load(handle), "artifact")
        if artifact.get("result") != manifest["result"]:
            raise ManifestError("manifest result does not match artifact result")
        rendered = render_artifact(artifact)
    except (json.JSONDecodeError, ArtifactError, ManifestError) as exc:
        print(f"MANIFEST_INVALID: {exc}", file=sys.stderr)
        return 2

    if not args.validate_only:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
