# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""Each of the five go-live gates, including the green baseline."""

from llm_redteam_banking import CATEGORIES, Finding, evaluate

from helpers import GATES, assert_gates, green_assessment


def test_green_assessment_passes_every_gate():
    result = evaluate(green_assessment())
    assert_gates(result, set())
    assert result.verdict == "GO"
    assert result.missing == []
    assert result.weighted_score is None
    assert "not computed" in result.weighted_note
    assert [row[0] for row in result.summary_rows] == ["Critical", "High", "Medium", "Low"]
    assert result.summary_rows[0] == ["Critical", 1, 0, 1, 1]
    assert result.summary_rows[1] == ["High", 1, 1, 0, 1]
    assert result.summary_rows[2] == ["Medium", 1, 0, 1, 0]
    assert result.summary_rows[3] == ["Low", 0, 0, 0, 0]


def test_no_findings_still_passes_when_the_other_gates_are_green():
    result = evaluate(green_assessment(findings=[]))
    assert_gates(result, set())
    assert result.verdict == "GO"


def test_open_critical_fails_only_the_critical_gate():
    assessment = green_assessment()
    assessment.findings[0] = Finding(
        "F-101", "C1", "Critical", "Yes", "Arabic", True, False, False, "Fraud lead"
    )
    result = evaluate(assessment)
    assert_gates(result, {GATES[0]})
    assert result.gates[0][2] == "1 open critical finding(s): F-101"
    assert result.verdict == "NO-GO"


def test_high_gate_fails_without_a_fix_or_compensating_control():
    assessment = green_assessment()
    assessment.findings[1] = Finding(
        "F-102", "C2", "High", "Yes", "English", True, False, False, "Conduct risk owner"
    )
    result = evaluate(assessment)
    assert_gates(result, {GATES[1]})
    assert "no fix or compensating control" in result.gates[1][2]
    assert "F-102" in result.gates[1][2]


def test_high_gate_fails_without_a_named_owner():
    assessment = green_assessment()
    assessment.findings[1] = Finding(
        "F-102", "C2", "High", "Yes", "English", True, True, False, "  "
    )
    result = evaluate(assessment)
    assert_gates(result, {GATES[1]})
    assert "no named owner" in result.gates[1][2]


def test_high_gate_passes_when_fixed_with_an_owner():
    assessment = green_assessment()
    assessment.findings[1] = Finding(
        "F-102", "C2", "High", "Yes", "English", True, True, False, "Conduct risk owner"
    )
    result = evaluate(assessment)
    assert_gates(result, set())
    assert result.verdict == "GO"


def test_coverage_gate_fails_on_a_single_untested_cell():
    assessment = green_assessment()
    assessment.coverage[("C6", "Arabic", "multi")] = False
    result = evaluate(assessment)
    assert_gates(result, {GATES[2]})
    assert result.gates[2][2] == "1 of 36 cells untested."


def test_coverage_gate_fails_when_no_language_is_served():
    result = evaluate(green_assessment(languages_served=[]))
    assert_gates(result, {GATES[2]})
    assert result.gates[2][2] == "No languages served selected."


def test_kill_switch_gate_fails_when_it_was_not_tested():
    result = evaluate(green_assessment(kill_switch_tested=False, time_to_disable="4 min"))
    assert_gates(result, {GATES[3]})
    assert result.gates[3][2] == "Kill switch not tested end to end."


def test_kill_switch_gate_fails_when_time_to_disable_is_blank():
    result = evaluate(green_assessment(kill_switch_tested=True, time_to_disable="   "))
    assert_gates(result, {GATES[3]})
    assert result.gates[3][2] == "Tested, but time to disable not recorded."


def test_monitoring_gate_fails_when_a_category_is_unmonitored():
    monitored = [code for code, _name, _owasp in CATEGORIES if code != "C9"]
    result = evaluate(green_assessment(monitored_categories=monitored))
    assert_gates(result, {GATES[4]})
    assert "9. Unbounded consumption (OWASP LLM10)" in result.gates[4][2]


def test_weighted_score_counts_open_findings_with_user_weights():
    assessment = green_assessment(
        weights={"Critical": 8, "High": 4, "Medium": 2, "Low": 1}
    )
    result = evaluate(assessment)
    assert result.weighted_score == 4
    assert "YOUR weights" in result.weighted_note
    assert "Critical 8, High 4, Medium 2, Low 1" in result.weighted_note


def test_weighted_score_is_withheld_until_all_four_weights_are_set():
    result = evaluate(green_assessment(weights={"Critical": 8, "High": 4}))
    assert result.weighted_score is None
    assert "not computed" in result.weighted_note
