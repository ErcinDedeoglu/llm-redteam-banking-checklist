# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""The example packs are what CI evaluates. Same evaluate() a pytest would call."""

from pathlib import Path

from llm_redteam_banking import CATEGORIES, evaluate, evidence_pack_md, load_assessment

from helpers import GATES, assert_gates

ROOT = Path(__file__).resolve().parents[1]
PASSING = ROOT / "examples" / "passing.yaml"
FAILING = ROOT / "examples" / "failing.yaml"


def test_evaluate_on_the_passing_example_is_go():
    assessment = load_assessment(PASSING)
    result = evaluate(assessment)
    assert_gates(result, set())
    assert result.verdict == "GO"
    assert result.missing == []
    assert result.verdict_reasons == [
        "All five gates pass, all eight checklist items ticked, no material change since the last run."
    ]
    pack = evidence_pack_md(assessment, result)
    assert "## Verdict: GO" in pack
    assert "* None." in pack
    assert "Ercin Dedeoglu" in pack
    assert "ercin.info" in pack
    assert "Harborline Retail Assistant (synthetic)" in pack
    assert "OWASP LLM09" in pack


def test_evaluate_on_the_failing_example_names_the_red_gates():
    assessment = load_assessment(FAILING)
    result = evaluate(assessment)
    assert_gates(result, {GATES[0], GATES[1]})
    assert result.verdict == "NO-GO"
    assert "F-201" in result.gates[0][2]
    assert "F-202" in result.gates[1][2]
    assert "no fix or compensating control" in result.gates[1][2]
    assert "no named owner" in result.gates[1][2]
    pack = evidence_pack_md(assessment, result)
    assert "## Verdict: NO-GO" in pack
    assert "| FAIL |" in pack
    assert "| PASS |" in pack
    assert "Gate failed: " + GATES[0] in pack


def test_examples_are_synthetic_and_carry_no_payload_fields():
    for path in (PASSING, FAILING):
        text = path.read_text(encoding="utf-8").lower()
        assert "synthetic" in text
        for banned in ("ignore previous", "jailbreak", "api_key", "password", "bearer ", "sk-"):
            assert banned not in text
        assessment = load_assessment(path)
        assert assessment.findings
        assert all(finding.ref.startswith("F-") for finding in assessment.findings)


def test_package_does_not_call_a_model_or_ship_the_space_ui():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src").rglob("*.py")
    )
    for banned in ("openai", "anthropic", "gradio", "httpx", "requests", "urllib"):
        assert banned not in source


def test_owasp_llm_top_10_2025_mapping_is_the_scorer_mapping():
    assert CATEGORIES == [
        ("C1", "Financial-crime facilitation", None),
        ("C2", "Conduct and suitability breaches", None),
        ("C3", "Sensitive information disclosure", "LLM02"),
        ("C4", "System prompt leakage", "LLM07"),
        ("C5", "Prompt injection through content the system reads", "LLM01"),
        ("C6", "Retrieval-layer weaknesses", "LLM08"),
        ("C7", "Excessive agency", "LLM06"),
        ("C8", "Misinformation", "LLM09"),
        ("C9", "Unbounded consumption", "LLM10"),
    ]
