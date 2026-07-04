#!/usr/bin/env python3
"""Validate and render a deep-review structured artifact.

The model owns review content. This script owns the final Markdown shape.
It intentionally uses only the Python standard library so it can run in the
bundled Codex runtime without package installation.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, NonNegativeInt, StrictStr, ValidationError, model_validator


RESULTS = {"STABLE_FIX_PLAN", "GRADED_REVIEW", "BLOCKER"}


class ArtifactError(Exception):
    pass


MetricValue = NonNegativeInt | Literal["unknown", "not_tracked"]


class StrictArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BannerModel(StrictArtifactModel):
    level: Literal["WARNING", "NOTE", "IMPORTANT", "CAUTION"]
    text: StrictStr


class SummaryRowModel(StrictArtifactModel):
    field: StrictStr
    value: StrictStr


class FindingModel(StrictArtifactModel):
    id: StrictStr
    priority: Literal["P0", "P1", "P2", "P3"]
    title: StrictStr
    impact: StrictStr
    evidence: list[StrictStr]
    invariant: StrictStr
    owning_boundary: StrictStr


class InlineCommentModel(StrictArtifactModel):
    finding_id: StrictStr
    file: StrictStr
    start: NonNegativeInt
    end: NonNegativeInt | None = None
    title: StrictStr
    body: StrictStr
    priority: Literal[0, 1, 2, 3]

    @model_validator(mode="after")
    def validate_line_range(self) -> "InlineCommentModel":
        if self.start <= 0:
            raise ValueError("start must be positive")
        if self.end is not None and self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self


class FixPlanItemModel(StrictArtifactModel):
    finding_id: StrictStr | None = None
    priority: Literal["P0", "P1", "P2", "P3"] | None = None
    title: StrictStr | None = None
    steps: list[StrictStr] | None = None
    plan: list[StrictStr] | None = None
    body: StrictStr | None = None
    alternative_rejected: StrictStr | None = None
    weaker_alternative_rejected: StrictStr | None = None


class VerificationRowModel(StrictArtifactModel):
    check: StrictStr
    evidence: StrictStr
    status: StrictStr


class CheckedNearbyCaseModel(StrictArtifactModel):
    case: StrictStr
    result: StrictStr
    evidence: StrictStr


class ReviewHealthRowModel(StrictArtifactModel):
    area: StrictStr
    status: StrictStr
    meaning: StrictStr


class ProcessMetricsModel(StrictArtifactModel):
    invariants_classified: NonNegativeInt
    candidate_observations: NonNegativeInt
    candidate_observations_accounted: NonNegativeInt
    candidate_observations_unaccounted: NonNegativeInt
    findings_accepted: NonNegativeInt
    fixed_point_iterations: NonNegativeInt
    nearby_cases_checked: NonNegativeInt
    same_invariant_cases_open: NonNegativeInt
    blocking_residuals: NonNegativeInt
    verification_residuals: MetricValue = "unknown"
    production_wiring_paths_checked: MetricValue = "unknown"
    restart_persistence_paths_checked: MetricValue = "unknown"
    participating_domains_count: NonNegativeInt
    domains_with_expectation_source: NonNegativeInt
    domains_unaccounted: NonNegativeInt
    semantic_entity_paths_checked: NonNegativeInt
    semantic_entity_paths_unaccounted: NonNegativeInt
    expanded_domain_inventories: MetricValue = "unknown"
    patch_simulation_rows: NonNegativeInt
    trace_file: StrictStr


class RejectedCandidateAccountingModel(StrictArtifactModel):
    reason: StrictStr
    count: NonNegativeInt
    sample_or_note: StrictStr = ""


class CandidateAccountingBreakdownModel(StrictArtifactModel):
    accepted_findings: NonNegativeInt
    rejected: list[RejectedCandidateAccountingModel]
    deferred_to_residual_risk: NonNegativeInt
    protected_input_non_findings: NonNegativeInt
    unaccounted: NonNegativeInt


class ResidualRiskModel(StrictArtifactModel):
    risk: StrictStr
    classification: StrictStr
    follow_up: StrictStr


class BlockerModel(StrictArtifactModel):
    summary: StrictStr
    details: StrictStr
    evidence_needed: StrictStr
    minimal_next_action: StrictStr


class StructuredReviewArtifactModel(StrictArtifactModel):
    result: Literal["STABLE_FIX_PLAN", "GRADED_REVIEW", "BLOCKER"]
    output_language: StrictStr
    banner: BannerModel | None = None
    summary: list[SummaryRowModel] | None = None
    findings: list[FindingModel] | None = None
    inline_comments: list[InlineCommentModel] = []
    fix_plan: list[StrictStr | FixPlanItemModel] | None = None
    verification: list[VerificationRowModel] | None = None
    checked_nearby_cases: list[CheckedNearbyCaseModel] | None = None
    review_health: list[ReviewHealthRowModel] | None = None
    participating_domain_inventory: list[StrictStr] | None = None
    process_metrics: ProcessMetricsModel | None = None
    candidate_accounting_breakdown: CandidateAccountingBreakdownModel | None = None
    closure_evidence: list[StrictStr] | None = None
    residual_risks: list[ResidualRiskModel] | None = None
    launcher_gate_assessment: StrictStr | None = None
    blocker: BlockerModel | None = None

    @model_validator(mode="after")
    def validate_result_shape(self) -> "StructuredReviewArtifactModel":
        if self.result == "BLOCKER":
            if self.blocker is None:
                raise ValueError("blocker is required when result is BLOCKER")
            return self

        required_fields = [
            "banner",
            "summary",
            "findings",
            "fix_plan",
            "verification",
            "checked_nearby_cases",
            "review_health",
            "participating_domain_inventory",
            "process_metrics",
            "candidate_accounting_breakdown",
            "closure_evidence",
            "residual_risks",
        ]
        missing = [field for field in required_fields if getattr(self, field) is None]
        if missing:
            raise ValueError(f"non-blocker artifact is missing required fields: {', '.join(missing)}")
        return self


def validate_artifact_schema(artifact: dict[str, Any]) -> dict[str, Any]:
    try:
        return StructuredReviewArtifactModel.model_validate(artifact).model_dump(exclude_none=True)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            errors.append(f"{location}: {error['msg']}")
        raise ArtifactError("schema validation failed: " + "; ".join(errors)) from exc


def as_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArtifactError(f"{field} must be an integer")
    if value < 0:
        raise ArtifactError(f"{field} must be non-negative")
    return value


def require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArtifactError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ArtifactError(f"{field} must be an array")
    return value


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def table_escape(value: Any) -> str:
    return text(value).replace("\n", "<br>").replace("|", "\\|")


def display_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ": "))
    return text(value)


def directive_escape(value: Any) -> str:
    return " ".join(text(value).replace('"', "'").split())


def quote_text(value: Any) -> list[str]:
    raw = text(value)
    if not raw:
        return []
    return [f"> {line}" if line else ">" for line in raw.splitlines()]


def is_ru(artifact: dict[str, Any]) -> bool:
    lang = text(artifact.get("output_language", "")).lower()
    return lang.startswith("ru") or "russian" in lang or "рус" in lang


def heading(artifact: dict[str, Any], en: str, ru: str) -> str:
    return ru if is_ru(artifact) else en


def metric(metrics: dict[str, Any], name: str, strict_int: bool = True) -> int | str:
    if name not in metrics:
        raise ArtifactError(f"process_metrics.{name} is missing")
    value = metrics[name]
    if strict_int:
        return as_int(value, f"process_metrics.{name}")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if value in {"unknown", "not_tracked"}:
        return value
    raise ArtifactError(f"process_metrics.{name} must be integer, unknown, or not_tracked")


def finding_priority(finding: dict[str, Any]) -> str:
    raw_priority = finding.get("priority")
    if isinstance(raw_priority, int) and not isinstance(raw_priority, bool):
        return f"P{raw_priority}" if 0 <= raw_priority <= 3 else ""

    priority = text(raw_priority).strip().upper()
    if priority in {"P0", "P1", "P2", "P3"}:
        return priority

    severity = text(finding.get("severity", "")).strip().lower()
    severity_map = {
        "critical": "P0",
        "blocker": "P0",
        "high": "P1",
        "medium": "P2",
        "moderate": "P2",
        "low": "P3",
        "info": "P3",
    }
    return severity_map.get(severity, "")


def normalize_candidate_accounting_breakdown(breakdown: dict[str, Any], findings_accepted: int) -> dict[str, Any]:
    """Return the canonical accounting shape accepted by the renderer.

    Older launcher instructions allowed an "equivalent structured list". Keep
    that compatibility here, then validate the normalized counters strictly.
    """
    normalized = dict(breakdown)
    totals = normalized.get("totals")
    if isinstance(totals, dict):
        normalized.setdefault("accepted_findings", totals.get("accepted", findings_accepted))
        normalized.setdefault("unaccounted", totals.get("unaccounted", 0))
        normalized.setdefault("merged_findings", totals.get("merged", 0))
        if "rejected" not in normalized:
            rejection_notes: list[str] = []
            for value in breakdown.values():
                if not isinstance(value, dict):
                    continue
                raw_reasons = value.get("rejection_reasons", [])
                if isinstance(raw_reasons, list):
                    rejection_notes.extend(text(reason) for reason in raw_reasons if text(reason).strip())

            normalized["rejected"] = [{
                "reason": "other",
                "count": totals.get("rejected", 0),
                "sample_or_note": "; ".join(rejection_notes),
            }]

    normalized["accepted_findings"] = as_int(
        normalized.get("accepted_findings", findings_accepted),
        "candidate_accounting_breakdown.accepted_findings",
    )
    normalized["deferred_to_residual_risk"] = as_int(
        normalized.get("deferred_to_residual_risk", 0),
        "candidate_accounting_breakdown.deferred_to_residual_risk",
    )
    normalized["protected_input_non_findings"] = as_int(
        normalized.get("protected_input_non_findings", 0),
        "candidate_accounting_breakdown.protected_input_non_findings",
    )
    normalized["unaccounted"] = as_int(
        normalized.get("unaccounted", 0),
        "candidate_accounting_breakdown.unaccounted",
    )

    rejected_items: list[dict[str, Any]] = []
    raw_rejected = normalized.get("rejected", [])
    if isinstance(raw_rejected, list):
        for index, item in enumerate(raw_rejected):
            item_obj = require_dict(item, f"candidate_accounting_breakdown.rejected[{index}]")
            rejected_items.append({
                "reason": text(item_obj.get("reason", "other")).strip() or "other",
                "count": as_int(item_obj.get("count", 0), f"candidate_accounting_breakdown.rejected[{index}].count"),
                "sample_or_note": item_obj.get("sample_or_note", ""),
            })
    else:
        rejected_total = as_int(raw_rejected, "candidate_accounting_breakdown.rejected")
        raw_rejections = normalized.get("rejections", [])
        rejections = require_list(raw_rejections, "candidate_accounting_breakdown.rejections")
        rejection_sum = 0
        for index, item in enumerate(rejections):
            item_obj = require_dict(item, f"candidate_accounting_breakdown.rejections[{index}]")
            count = as_int(item_obj.get("count", 0), f"candidate_accounting_breakdown.rejections[{index}].count")
            rejection_sum += count
            rejected_items.append({
                "reason": "other",
                "count": count,
                "sample_or_note": item_obj.get("sample_or_note", item_obj.get("reason", "")),
            })
        if not rejections and rejected_total:
            rejected_items.append({"reason": "other", "count": rejected_total, "sample_or_note": ""})
        elif rejection_sum != rejected_total:
            raise ArtifactError("candidate_accounting_breakdown.rejections must sum to rejected")

    merged_findings = as_int(normalized.get("merged_findings", 0), "candidate_accounting_breakdown.merged_findings")
    if merged_findings:
        rejected_items.append({
            "reason": "duplicate_or_covered",
            "count": merged_findings,
            "sample_or_note": "merged into accepted findings",
        })

    normalized["rejected"] = rejected_items
    return normalized


def breakdown_count(breakdown: dict[str, Any]) -> int:
    total = as_int(breakdown.get("accepted_findings", 0), "candidate_accounting_breakdown.accepted_findings")
    total += as_int(breakdown.get("deferred_to_residual_risk", 0), "candidate_accounting_breakdown.deferred_to_residual_risk")
    total += as_int(breakdown.get("protected_input_non_findings", 0), "candidate_accounting_breakdown.protected_input_non_findings")
    total += as_int(breakdown.get("unaccounted", 0), "candidate_accounting_breakdown.unaccounted")
    for index, item in enumerate(require_list(breakdown.get("rejected", []), "candidate_accounting_breakdown.rejected")):
        item_obj = require_dict(item, f"candidate_accounting_breakdown.rejected[{index}]")
        total += as_int(item_obj.get("count", 0), f"candidate_accounting_breakdown.rejected[{index}].count")
    return total


def validate_inline_comments(artifact: dict[str, Any]) -> None:
    comments = artifact.get("inline_comments", [])
    require_list(comments, "inline_comments")

    finding_priorities = {}
    for item in require_list(artifact.get("findings"), "findings"):
        finding = require_dict(item, "findings[]")
        finding_id = text(finding.get("id", "")).strip()
        priority = finding_priority(finding)
        if finding_id:
            finding_priorities[finding_id] = priority

    for index, item in enumerate(comments):
        obj = require_dict(item, f"inline_comments[{index}]")
        finding_id = text(obj.get("finding_id", "")).strip()
        if not finding_id:
            raise ArtifactError(f"inline_comments[{index}].finding_id is required")
        if finding_id not in finding_priorities:
            raise ArtifactError(f"inline_comments[{index}].finding_id must match a finding id")

        for field in ["file", "title", "body"]:
            if not text(obj.get(field, "")).strip():
                raise ArtifactError(f"inline_comments[{index}].{field} is required")

        start = as_int(obj.get("start"), f"inline_comments[{index}].start")
        if start <= 0:
            raise ArtifactError(f"inline_comments[{index}].start must be positive")

        end = obj.get("end", start)
        end_int = as_int(end, f"inline_comments[{index}].end")
        if end_int < start:
            raise ArtifactError(f"inline_comments[{index}].end must be greater than or equal to start")

        priority = as_int(obj.get("priority"), f"inline_comments[{index}].priority")
        if priority > 3:
            raise ArtifactError(f"inline_comments[{index}].priority must be between 0 and 3")
        expected_priority = f"P{priority}"
        if finding_priorities[finding_id] != expected_priority:
            raise ArtifactError(f"inline_comments[{index}].priority must match finding priority")


def validate_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    artifact = validate_artifact_schema(artifact)
    result = artifact.get("result")
    if result not in RESULTS:
        raise ArtifactError("result must be STABLE_FIX_PLAN, GRADED_REVIEW, or BLOCKER")

    if result == "BLOCKER":
        require_dict(artifact.get("blocker"), "blocker")
        return artifact

    required_lists = [
        "summary",
        "findings",
        "fix_plan",
        "verification",
        "checked_nearby_cases",
        "review_health",
        "participating_domain_inventory",
        "closure_evidence",
        "residual_risks",
    ]
    for field in required_lists:
        require_list(artifact.get(field), field)

    metrics = require_dict(artifact.get("process_metrics"), "process_metrics")
    breakdown = require_dict(artifact.get("candidate_accounting_breakdown"), "candidate_accounting_breakdown")
    validate_inline_comments(artifact)

    candidate_observations = metric(metrics, "candidate_observations")
    accounted = metric(metrics, "candidate_observations_accounted")
    unaccounted = metric(metrics, "candidate_observations_unaccounted")
    findings_accepted = metric(metrics, "findings_accepted")
    breakdown = normalize_candidate_accounting_breakdown(breakdown, findings_accepted)
    metric(metrics, "invariants_classified")
    metric(metrics, "fixed_point_iterations")
    metric(metrics, "nearby_cases_checked")
    metric(metrics, "same_invariant_cases_open")
    metric(metrics, "blocking_residuals")
    metric(metrics, "participating_domains_count")
    metric(metrics, "domains_with_expectation_source")
    metric(metrics, "domains_unaccounted")
    metric(metrics, "semantic_entity_paths_checked")
    metric(metrics, "semantic_entity_paths_unaccounted")
    metric(metrics, "patch_simulation_rows")

    if candidate_observations != accounted + unaccounted:
        raise ArtifactError("candidate accounting mismatch: observations != accounted + unaccounted")
    if breakdown_count(breakdown) != candidate_observations:
        raise ArtifactError("candidate_accounting_breakdown must sum to candidate_observations")
    if as_int(breakdown.get("accepted_findings", 0), "candidate_accounting_breakdown.accepted_findings") != findings_accepted:
        raise ArtifactError("candidate_accounting_breakdown.accepted_findings must equal findings_accepted")
    if as_int(breakdown.get("unaccounted", 0), "candidate_accounting_breakdown.unaccounted") != unaccounted:
        raise ArtifactError("candidate_accounting_breakdown.unaccounted must equal candidate_observations_unaccounted")

    if result == "STABLE_FIX_PLAN":
        zero_fields = [
            "candidate_observations_unaccounted",
            "same_invariant_cases_open",
            "blocking_residuals",
            "domains_unaccounted",
            "semantic_entity_paths_unaccounted",
        ]
        for field in zero_fields:
            if metric(metrics, field) != 0:
                raise ArtifactError(f"STABLE_FIX_PLAN requires process_metrics.{field}=0")

    return artifact


def render_callout(artifact: dict[str, Any]) -> list[str]:
    raw_banner = artifact.get("banner", {"level": "NOTE", "text": ""})
    if isinstance(raw_banner, str):
        banner = {"level": "NOTE", "text": raw_banner}
    else:
        banner = require_dict(raw_banner, "banner")
    level = text(banner.get("level", "NOTE")).upper()
    if level not in {"WARNING", "NOTE", "IMPORTANT", "CAUTION"}:
        level = "NOTE"
    message = text(banner.get("text", ""))
    if not message:
        return []
    label = callout_label(artifact, level)
    return [f"> **{label}**", ">", f"> {message}", ""]


def render_inline_comments(artifact: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in require_list(artifact.get("inline_comments", []), "inline_comments"):
        obj = require_dict(item, "inline_comments[]")
        start = as_int(obj.get("start"), "inline_comments[].start")
        end = as_int(obj.get("end", start), "inline_comments[].end")
        priority = as_int(obj.get("priority"), "inline_comments[].priority")
        lines.append(
            '::code-comment{'
            f'title="{directive_escape(obj.get("title"))}" '
            f'body="{directive_escape(obj.get("body"))}" '
            f'file="{directive_escape(obj.get("file"))}" '
            f"start={start} "
            f"end={end} "
            f"priority={priority}"
            "}"
        )
    if lines:
        lines.append("")
    return lines


def render_details(summary: str, body: list[str], open_by_default: bool = False) -> list[str]:
    if not body:
        return []
    attrs = f'summary="{directive_escape(summary)}"'
    if open_by_default:
        attrs += ' open="true"'
    lines = [f":::github-details{{{attrs}}}", *body]
    while lines and lines[-1] == "":
        lines.pop()
    lines.extend([":::", ""])
    return lines


def render_card(artifact: dict[str, Any], level: str, title: str, body: list[str]) -> list[str]:
    label = callout_label(artifact, level)
    lines = [f"> **{label} · {title}**"]
    for item in body:
        if item:
            lines.append(f"> {item}")
        else:
            lines.append(">")
    lines.append("")
    return lines


def callout_label(artifact: dict[str, Any], level: str) -> str:
    labels_en = {
        "WARNING": "Warning",
        "NOTE": "Note",
        "IMPORTANT": "Important",
        "CAUTION": "Caution",
    }
    labels_ru = {
        "WARNING": "Внимание",
        "NOTE": "Заметка",
        "IMPORTANT": "Важно",
        "CAUTION": "Критично",
    }
    return (labels_ru if is_ru(artifact) else labels_en).get(level, level.title())


def render_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(table_escape(cell) for cell in row) + " |")
    return lines


def render_summary(artifact: dict[str, Any]) -> list[str]:
    rows = []
    for index, item in enumerate(require_list(artifact.get("summary"), "summary"), start=1):
        if isinstance(item, dict):
            rows.append([item.get("field", f"#{index}"), item.get("value", display_value(item))])
        else:
            rows.append([f"#{index}", display_value(item)])
    return ["# " + heading(artifact, "Summary", "Резюме"), *render_table(
        [heading(artifact, "Field", "Поле"), heading(artifact, "Value", "Значение")],
        rows,
    ), ""]


def render_review_panel(artifact: dict[str, Any]) -> list[str]:
    metrics = require_dict(artifact.get("process_metrics"), "process_metrics")
    findings = require_list(artifact.get("findings"), "findings")
    priorities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for item in findings:
        obj = require_dict(item, "findings[]")
        priority = finding_priority(obj)
        if priority in priorities:
            priorities[priority] += 1

    accepted = metric(metrics, "findings_accepted")
    unaccounted = metric(metrics, "candidate_observations_unaccounted")
    blocking = metric(metrics, "blocking_residuals")
    same_invariant_open = metric(metrics, "same_invariant_cases_open")
    verification_residuals = metrics.get("verification_residuals", "unknown")

    lines = ["# " + heading(artifact, "Review Panel", "Панель ревью")]
    lines.extend(render_card(artifact, "IMPORTANT", heading(artifact, "Result", "Результат"), [
        f"`{artifact['result']}`",
        f"{heading(artifact, 'Accepted findings', 'Принятые findings')}: **{accepted}**",
    ]))
    finding_level = "CAUTION" if priorities["P0"] or priorities["P1"] else "NOTE"
    lines.extend(render_card(artifact, finding_level, heading(artifact, "Finding Severity", "Серьезность проблем"), [
        f"P0: **{priorities['P0']}**",
        f"P1: **{priorities['P1']}**",
        f"P2/P3: **{priorities['P2'] + priorities['P3']}**",
    ]))
    closure_level = "WARNING" if unaccounted or blocking or same_invariant_open else "NOTE"
    lines.extend(render_card(artifact, closure_level, heading(artifact, "Closure Gate", "Закрытие инвариантов"), [
        f"{heading(artifact, 'Unaccounted observations', 'Неучтенные observations')}: **{unaccounted}**",
        f"{heading(artifact, 'Open same-invariant cases', 'Открытые same-invariant случаи')}: **{same_invariant_open}**",
        f"{heading(artifact, 'Blocking residuals', 'Блокирующие остатки')}: **{blocking}**",
    ]))
    verification_level = "WARNING" if verification_residuals not in {0, "0"} else "NOTE"
    lines.extend(render_card(artifact, verification_level, heading(artifact, "Verification", "Проверка"), [
        f"{heading(artifact, 'Verification residuals', 'Остатки проверки')}: **{verification_residuals}**",
        f"{heading(artifact, 'Trace', 'Trace')}: `{text(metrics.get('trace_file', 'not_written'))}`",
    ]))
    return lines


def render_findings(artifact: dict[str, Any]) -> list[str]:
    lines = ["# " + heading(artifact, "Findings", "Проблемы")]
    findings = require_list(artifact.get("findings"), "findings")
    if not findings:
        lines.extend(render_card(artifact, "NOTE", heading(artifact, "No findings", "Проблем нет"), [
            heading(artifact, "No accepted findings in this review.", "В этом ревью нет принятых finding."),
        ]))
        return lines

    level_by_priority = {
        "P0": "CAUTION",
        "P1": "WARNING",
        "P2": "IMPORTANT",
        "P3": "NOTE",
    }
    for item in findings:
        obj = require_dict(item, "findings[]")
        priority = finding_priority(obj)
        level = level_by_priority.get(priority, "NOTE")
        finding_id = text(obj.get("id", "")).strip()
        title_prefix = f"{priority} {finding_id}".strip()
        title = text(obj.get("title", "")).strip()
        card_title = f"{title_prefix}: {title}" if title_prefix else title
        label = callout_label(artifact, level)
        lines.extend([f"> **{label} · {card_title}**"])
        impact = text(obj.get("impact", obj.get("risk", ""))).strip()
        if impact:
            lines.extend([">", f"> **{heading(artifact, 'Impact', 'Влияние')}:** {impact}"])
        evidence = obj.get("evidence", "")
        if evidence:
            lines.extend([">", f"> **{heading(artifact, 'Evidence', 'Доказательства')}:**"])
            if isinstance(evidence, list):
                for evidence_item in evidence:
                    lines.append(f"> - {text(evidence_item)}")
            else:
                lines.extend(quote_text(evidence))
        invariant = text(obj.get("invariant", obj.get("broken_invariant", obj.get("invariant_id", "")))).strip()
        if invariant:
            lines.extend([">", f"> **{heading(artifact, 'Invariant', 'Инвариант')}:** {invariant}"])
        boundary = text(obj.get("owning_boundary", "")).strip()
        if boundary:
            lines.extend([">", f"> **{heading(artifact, 'Owning boundary', 'Граница владения')}:** {boundary}"])
        lines.append("")
    return lines


def render_numbered(artifact: dict[str, Any], field: str, en: str, ru: str) -> list[str]:
    lines = ["# " + heading(artifact, en, ru)]
    items = require_list(artifact.get(field), field)
    if not items:
        lines.append(heading(artifact, "None.", "Нет."))
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {display_value(item)}")
    lines.append("")
    return lines


def render_fix_plan(artifact: dict[str, Any]) -> list[str]:
    lines = ["# " + heading(artifact, "Fix Plan", "План исправления")]
    items = require_list(artifact.get("fix_plan"), "fix_plan")
    if not items:
        lines.append(heading(artifact, "None.", "Нет."))
        lines.append("")
        return lines

    priority_by_finding_id = {
        text(finding.get("id", "")).strip(): finding_priority(finding)
        for finding in (require_dict(item, "findings[]") for item in require_list(artifact.get("findings"), "findings"))
    }

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            lines.append(f"{index}. {display_value(item)}")
            continue

        finding_id = text(item.get("finding_id", "")).strip()
        priority = priority_by_finding_id.get(finding_id) or finding_priority(item)
        title = text(item.get("title", "")).strip()
        lead = " · ".join(part for part in [finding_id, priority, title] if part)
        lines.append(f"{index}. **{lead}**" if lead else f"{index}.")

        steps = item.get("steps", item.get("plan", []))
        if isinstance(steps, list) and steps:
            for step in steps:
                step_text = text(step).strip()
                if step_text:
                    lines.append(f"   - {step_text}")
        else:
            body = text(item.get("body", "")).strip()
            if body:
                lines.append(f"   - {body}")

        alternative_rejected = text(item.get("alternative_rejected", item.get("weaker_alternative_rejected", ""))).strip()
        if alternative_rejected:
            lines.append(
                f"   - **{heading(artifact, 'Rejected approach', 'Отклоненный подход')}:** "
                f"{alternative_rejected}"
            )
    lines.append("")
    return lines


def render_object_table(artifact: dict[str, Any], field: str, en: str, ru: str, columns: list[tuple[str, str, str]]) -> list[str]:
    def cell(obj: dict[str, Any], key: str) -> Any:
        aliases = {
            "result": ["result", "status"],
            "area": ["area", "check"],
            "meaning": ["meaning", "evidence"],
            "follow_up": ["follow_up", "evidence"],
        }
        for candidate in aliases.get(key, [key]):
            if candidate in obj:
                return obj.get(candidate)
        return None

    rows = []
    for item in require_list(artifact.get(field), field):
        if isinstance(item, dict):
            if any(key in item for key, _, _ in columns):
                rows.append([cell(item, key) for key, _, _ in columns])
            else:
                rows.append([display_value(item), *("" for _ in columns[1:])])
        else:
            rows.append([display_value(item), *("" for _ in columns[1:])])
    if not rows:
        rows.append([heading(artifact, "None", "Нет"), "", ""])
    return ["# " + heading(artifact, en, ru), *render_table(
        [heading(artifact, en_col, ru_col) for _, en_col, ru_col in columns],
        rows,
    ), ""]


def render_metrics(artifact: dict[str, Any]) -> list[str]:
    metrics = require_dict(artifact.get("process_metrics"), "process_metrics")
    rows = [[key, value] for key, value in metrics.items()]
    return ["# " + heading(artifact, "Process Metrics", "Метрики процесса"), *render_table(
        [heading(artifact, "Metric", "Метрика"), heading(artifact, "Value", "Значение")],
        rows,
    ), ""]


def render_breakdown(artifact: dict[str, Any]) -> list[str]:
    metrics = require_dict(artifact.get("process_metrics"), "process_metrics")
    findings_accepted = metric(metrics, "findings_accepted")
    breakdown = normalize_candidate_accounting_breakdown(
        require_dict(artifact.get("candidate_accounting_breakdown"), "candidate_accounting_breakdown"),
        findings_accepted,
    )
    rows = [
        ["accepted_findings", breakdown.get("accepted_findings", 0), ""],
        ["deferred_to_residual_risk", breakdown.get("deferred_to_residual_risk", 0), ""],
        ["protected_input_non_findings", breakdown.get("protected_input_non_findings", 0), ""],
        ["unaccounted", breakdown.get("unaccounted", 0), ""],
    ]
    for item in require_list(breakdown.get("rejected", []), "candidate_accounting_breakdown.rejected"):
        obj = require_dict(item, "candidate_accounting_breakdown.rejected[]")
        rows.append([f"rejected:{obj.get('reason', 'other')}", obj.get("count", 0), obj.get("sample_or_note", "")])
    return ["# " + heading(artifact, "Candidate Accounting", "Учет observations"), *render_table(
        [heading(artifact, "Bucket", "Группа"), heading(artifact, "Count", "Количество"), heading(artifact, "Note", "Примечание")],
        rows,
    ), ""]


def render_blocker(artifact: dict[str, Any]) -> str:
    blocker = require_dict(artifact.get("blocker"), "blocker")
    lines = [f"BLOCKER: {text(blocker.get('summary', 'deep-review blocked'))}", ""]
    lines.extend(["# " + heading(artifact, "Blocker", "Блокер"), text(blocker.get("details", "")), ""])
    lines.extend(["# " + heading(artifact, "Evidence Needed", "Каких данных не хватает"), text(blocker.get("evidence_needed", "")), ""])
    lines.extend(["# " + heading(artifact, "Minimal Next Action", "Минимальное следующее действие"), text(blocker.get("minimal_next_action", "")), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_artifact(artifact: dict[str, Any]) -> str:
    artifact = validate_artifact(artifact)
    if artifact["result"] == "BLOCKER":
        return render_blocker(artifact)

    lines: list[str] = []
    lines.extend(render_inline_comments(artifact))
    lines.extend([artifact["result"], ""])
    lines.extend(render_callout(artifact))
    if artifact["result"] == "GRADED_REVIEW" and artifact.get("launcher_gate_assessment"):
        lines.append("# " + heading(artifact, "Launcher Gate Assessment", "Оценка launcher gate"))
        lines.append(text(artifact["launcher_gate_assessment"]))
        lines.append("")
    lines.extend(render_review_panel(artifact))
    lines.extend(render_summary(artifact))
    lines.extend(render_findings(artifact))
    lines.extend(render_fix_plan(artifact))
    lines.extend(render_object_table(artifact, "verification", "Verification", "Проверка", [
        ("check", "Check", "Проверка"),
        ("evidence", "Command or evidence", "Команда или доказательство"),
        ("status", "Status", "Статус"),
    ]))
    lines.extend(render_details(
        heading(artifact, "Nearby cases and review health", "Проверенные соседние случаи и состояние ревью"),
        [
            *render_object_table(artifact, "checked_nearby_cases", "Checked Nearby Cases", "Что еще проверили", [
                ("case", "Case checked", "Сценарий"),
                ("result", "Result", "Результат"),
                ("evidence", "Evidence", "Доказательство"),
            ]),
            *render_object_table(artifact, "review_health", "Review Health", "Состояние ревью", [
                ("area", "Area", "Область"),
                ("status", "Status", "Статус"),
                ("meaning", "Meaning", "Что значит"),
            ]),
            *render_numbered(artifact, "participating_domain_inventory", "Participating Domain Inventory", "Участвующие домены"),
        ],
    ))
    lines.extend(render_details(
        heading(artifact, "Process metrics and candidate accounting", "Метрики процесса и учет observations"),
        [*render_metrics(artifact), *render_breakdown(artifact)],
    ))
    lines.extend(render_details(
        heading(artifact, "Closure evidence", "Доказательная часть"),
        render_numbered(artifact, "closure_evidence", "Closure Evidence", "Доказательная часть"),
    ))
    lines.extend(render_details(
        heading(artifact, "Residual risks", "Остаточные риски"),
        render_object_table(artifact, "residual_risks", "Residual Risks", "Остаточные риски", [
            ("risk", "Risk", "Риск"),
            ("classification", "Classification", "Классификация"),
            ("follow_up", "Follow-up", "Что дальше"),
        ]),
    ))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to JSON artifact. Reads stdin when omitted.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    raw = open(args.input, "r", encoding="utf-8").read() if args.input else sys.stdin.read()
    try:
        artifact = require_dict(json.loads(raw), "artifact")
        rendered = render_artifact(artifact)
    except (json.JSONDecodeError, ArtifactError) as exc:
        print(f"ARTIFACT_INVALID: {exc}", file=sys.stderr)
        return 2

    if not args.validate_only:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
