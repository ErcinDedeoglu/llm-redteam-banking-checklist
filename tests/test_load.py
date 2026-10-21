# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""The file schema stays narrow: category, severity, and the gate inputs."""

import pytest

from llm_redteam_banking import FindingsFileError, load_assessment


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_yaml_yes_boolean_is_accepted_as_multi_turn(tmp_path):
    path = _write(
        tmp_path,
        "findings.yaml",
        """
system_name: Synthetic desk
findings:
  - ref: F-1
    category: c8
    severity: low
    multi_turn: Yes
    language: English
    human_reviewed: false
    fixed: true
""",
    )
    assessment = load_assessment(path)
    finding = assessment.findings[0]
    assert finding.category == "C8"
    assert finding.severity == "Low"
    assert finding.multi_turn == "Yes"
    assert finding.fixed is True
    assert assessment.languages_served == ["Arabic", "English"]


def test_coverage_list_form_loads(tmp_path):
    path = _write(
        tmp_path,
        "findings.yml",
        """
findings: []
coverage:
  - category: C1
    language: Arabic
    mode: single
    tested: false
""",
    )
    assessment = load_assessment(path)
    assert assessment.coverage[("C1", "Arabic", "single")] is False


def test_unknown_prompt_field_is_rejected(tmp_path):
    path = _write(tmp_path, "bad.yaml", "prompt: removed\nfindings: []\n")
    with pytest.raises(FindingsFileError, match="unknown field"):
        load_assessment(path)


def test_checklist_items_3_and_6_are_rejected(tmp_path):
    path = _write(tmp_path, "bad.yaml", "findings: []\nchecklist_done: [3]\n")
    with pytest.raises(FindingsFileError, match="coverage"):
        load_assessment(path)


def test_unknown_category_is_rejected(tmp_path):
    path = _write(
        tmp_path,
        "bad.json",
        """
        {"findings": [{"ref": "F-1", "category": "C10", "severity": "Low",
        "multi_turn": "No", "language": "English", "human_reviewed": false, "fixed": true}]}
        """,
    )
    with pytest.raises(FindingsFileError, match="C10"):
        load_assessment(path)


def test_empty_and_unknown_suffix_are_rejected(tmp_path):
    empty = _write(tmp_path, "empty.yaml", "   \n")
    with pytest.raises(FindingsFileError, match="empty"):
        load_assessment(empty)
    other = _write(tmp_path, "notes.txt", "findings: []\n")
    with pytest.raises(FindingsFileError, match=".json"):
        load_assessment(other)
