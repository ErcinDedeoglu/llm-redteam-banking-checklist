# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""Read a findings JSON or YAML file into an Assessment.

The scorer never sees the file. It only sees the Assessment it already
accepted in the Hugging Face Space.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from llm_redteam_banking.scorer import (
    CATEGORIES,
    CHECKLIST,
    LABEL_TO_CODE,
    LANGUAGES,
    MULTI_TURN,
    SEVERITIES,
    Assessment,
    Finding,
)

_CATEGORY_CODES = {code for code, _, _ in CATEGORIES}
_CHECKLIST_IDS = {number for number, _ in CHECKLIST}
_TOP_LEVEL = {
    "system_name",
    "languages_served",
    "findings",
    "coverage",
    "kill_switch_tested",
    "time_to_disable",
    "monitored_categories",
    "checklist_done",
    "changes_since_last_run",
    "weights",
}
_FINDING_FIELDS = {
    "ref",
    "category",
    "severity",
    "multi_turn",
    "language",
    "human_reviewed",
    "fixed",
    "compensating_control",
    "owner",
}
_REQUIRED_FINDING = {
    "ref",
    "category",
    "severity",
    "multi_turn",
    "language",
    "human_reviewed",
    "fixed",
}
_MODES = ("single", "multi")


class FindingsFileError(ValueError):
    """The findings file is missing, unreadable, or outside the schema."""


def load_assessment(path: str | Path) -> Assessment:
    """Load ``path`` and return the Assessment ``evaluate`` expects."""

    source = Path(path)
    data = _read(source)
    if not isinstance(data, dict):
        raise FindingsFileError(f"{source}: top level must be a mapping")
    unknown = sorted(set(data) - _TOP_LEVEL)
    if unknown:
        raise FindingsFileError(
            f"{source}: unknown field(s): {', '.join(unknown)}. "
            "Record category and severity only; do not include prompt text."
        )
    return Assessment(
        system_name=_line(data.get("system_name", ""), "system_name"),
        languages_served=_languages(data.get("languages_served", ["Arabic", "English"])),
        findings=_findings(data.get("findings", [])),
        coverage=_coverage(data.get("coverage", {})),
        kill_switch_tested=_bool(data.get("kill_switch_tested", False), "kill_switch_tested"),
        time_to_disable=_line(data.get("time_to_disable", ""), "time_to_disable"),
        monitored_categories=_categories(data.get("monitored_categories", []), "monitored_categories"),
        checklist_done=_checklist(data.get("checklist_done", [])),
        changes_since_last_run=_changes(data.get("changes_since_last_run", [])),
        weights=_weights(data.get("weights", {})),
    )


def _read(path: Path) -> Any:
    if not path.is_file():
        raise FindingsFileError(f"findings file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise FindingsFileError(f"{path}: file is empty")
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            return json.loads(text)
        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise FindingsFileError(f"{path}: {exc}") from exc
    raise FindingsFileError(f"{path}: expected a .json, .yaml, or .yml file")


def _findings(value: Any) -> list[Finding]:
    if not isinstance(value, list):
        raise FindingsFileError("findings must be a list")
    findings: list[Finding] = []
    for index, item in enumerate(value):
        where = f"findings[{index}]"
        if not isinstance(item, dict):
            raise FindingsFileError(f"{where} must be a mapping")
        unknown = sorted(set(item) - _FINDING_FIELDS)
        if unknown:
            raise FindingsFileError(
                f"{where}: unknown field(s): {', '.join(unknown)}. "
                "Record category and severity only; do not include prompt text."
            )
        missing = sorted(_REQUIRED_FINDING - set(item))
        if missing:
            raise FindingsFileError(f"{where}: missing field(s): {', '.join(missing)}")
        ref = _line(item["ref"], f"{where}.ref", allow_empty=False)
        findings.append(
            Finding(
                ref=ref,
                category=_category(item["category"], f"{where}.category"),
                severity=_severity(item["severity"], f"{where}.severity"),
                multi_turn=_multi_turn(item["multi_turn"], f"{where}.multi_turn"),
                language=_language(item["language"], f"{where}.language"),
                human_reviewed=_bool(item["human_reviewed"], f"{where}.human_reviewed"),
                fixed=_bool(item["fixed"], f"{where}.fixed"),
                compensating_control=_bool(
                    item.get("compensating_control", False),
                    f"{where}.compensating_control",
                ),
                owner=_line(item.get("owner", ""), f"{where}.owner"),
            )
        )
    return findings


def _coverage(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, list):
        return _coverage_list(value)
    if isinstance(value, dict):
        return _coverage_map(value)
    raise FindingsFileError("coverage must be a mapping or a list")


def _coverage_map(value: dict) -> dict:
    coverage: dict = {}
    for raw_code, languages in value.items():
        code = _category(raw_code, "coverage")
        if not isinstance(languages, dict):
            raise FindingsFileError(f"coverage.{code} must map a language to single and multi turn")
        for language, modes in languages.items():
            if language not in LANGUAGES:
                raise FindingsFileError(f"coverage.{code}: unknown language {language!r}")
            if not isinstance(modes, dict):
                raise FindingsFileError(f"coverage.{code}.{language} must map single and multi to true or false")
            unknown_modes = sorted(set(modes) - set(_MODES))
            if unknown_modes:
                raise FindingsFileError(
                    f"coverage.{code}.{language}: unknown mode(s): {', '.join(unknown_modes)}"
                )
            for mode in _MODES:
                if mode in modes:
                    coverage[(code, language, mode)] = _bool(
                        modes[mode], f"coverage.{code}.{language}.{mode}"
                    )
    return coverage


def _coverage_list(items: list) -> dict:
    coverage: dict = {}
    for index, item in enumerate(items):
        where = f"coverage[{index}]"
        if not isinstance(item, dict):
            raise FindingsFileError(f"{where} must be a mapping")
        unknown = sorted(set(item) - {"category", "language", "mode", "tested"})
        if unknown:
            raise FindingsFileError(f"{where}: unknown field(s): {', '.join(unknown)}")
        for field in ("category", "language", "mode"):
            if field not in item:
                raise FindingsFileError(f"{where}: missing {field}")
        code = _category(item["category"], f"{where}.category")
        language = _language(item["language"], f"{where}.language")
        mode = item["mode"]
        if mode not in _MODES:
            raise FindingsFileError(f"{where}.mode must be 'single' or 'multi'")
        coverage[(code, language, mode)] = _bool(item.get("tested", True), f"{where}.tested")
    return coverage


def _category(value: Any, where: str) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text.upper() in _CATEGORY_CODES:
            return text.upper()
        if text in LABEL_TO_CODE:
            return LABEL_TO_CODE[text]
    raise FindingsFileError(f"{where}: unknown category {value!r}. Use a code from C1 to C9.")


def _severity(value: Any, where: str) -> str:
    if isinstance(value, str):
        for severity in SEVERITIES:
            if value.strip().lower() == severity.lower():
                return severity
    raise FindingsFileError(f"{where}: severity must be one of {', '.join(SEVERITIES)}")


def _multi_turn(value: Any, where: str) -> str:
    # YAML 1.1 parses an unquoted Yes/No as a boolean. Accept that and the real strings.
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    if isinstance(value, str):
        for option in MULTI_TURN:
            if value.strip().lower() == option.lower():
                return option
    quoted = ", ".join(repr(option) for option in MULTI_TURN)
    raise FindingsFileError(f"{where}: multi_turn must be one of {quoted}")


def _language(value: Any, where: str) -> str:
    if isinstance(value, str) and value in LANGUAGES:
        return value
    raise FindingsFileError(f"{where}: language must be one of {', '.join(LANGUAGES)}")


def _languages(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise FindingsFileError("languages_served must be a list")
    return [_language(item, "languages_served") for item in value]


def _categories(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        raise FindingsFileError(f"{where} must be a list of category codes")
    return [_category(item, where) for item in value]


def _checklist(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise FindingsFileError("checklist_done must be a list of item numbers")
    done: list[int] = []
    valid = ", ".join(str(number) for number in sorted(_CHECKLIST_IDS))
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise FindingsFileError(f"checklist_done: {item!r} is not an item number")
        if item in (3, 6):
            raise FindingsFileError(
                "checklist items 3 (coverage) and 6 (kill switch) come from the gate inputs; "
                "do not list them in checklist_done"
            )
        if item not in _CHECKLIST_IDS:
            raise FindingsFileError(f"checklist_done: {item} is not a checklist item. Valid numbers: {valid}")
        done.append(item)
    return done


def _changes(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise FindingsFileError("changes_since_last_run must be a list of strings")
    changes: list[str] = []
    for item in value:
        text = _line(item, "changes_since_last_run", allow_empty=False)
        changes.append(text)
    return changes


def _weights(value: Any) -> dict:
    if value is None or value == {}:
        return {}
    if not isinstance(value, dict):
        raise FindingsFileError("weights must be a mapping of severity to a number")
    unknown = sorted(set(value) - set(SEVERITIES))
    if unknown:
        raise FindingsFileError(f"weights: unknown severity {', '.join(unknown)}")
    weights: dict = {}
    for key, raw in value.items():
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise FindingsFileError(f"weights.{key}: expected a number")
        weights[key] = raw
    return weights


def _bool(value: Any, where: str) -> bool:
    if isinstance(value, bool):
        return value
    raise FindingsFileError(f"{where}: expected true or false")


def _line(value: Any, where: str, allow_empty: bool = True) -> str:
    if not isinstance(value, str):
        raise FindingsFileError(f"{where}: expected a single-line string")
    if "\n" in value or "\r" in value or "|" in value:
        raise FindingsFileError(f"{where}: keep this field on one line, with no '|' character")
    text = value.strip()
    if not allow_empty and not text:
        raise FindingsFileError(f"{where}: must not be empty")
    return text
