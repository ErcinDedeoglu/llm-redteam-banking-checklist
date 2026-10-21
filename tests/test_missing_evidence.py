# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""Missing-evidence checks from the article's rules. These do not replace the five gates."""

from llm_redteam_banking import CHECKLIST, category_label, evaluate, Finding

from helpers import assert_gates, full_coverage, green_assessment


def test_green_pack_has_no_missing_evidence():
    result = evaluate(green_assessment())
    assert result.missing == []


def test_critical_or_high_finding_must_be_human_reviewed():
    assessment = green_assessment()
    assessment.findings[0] = Finding(
        "F-101", "C1", "Critical", "Yes", "Arabic", False, True, False, "Fraud lead"
    )
    result = evaluate(assessment)
    assert (
        "F-101: critical finding not human reviewed. "
        "The article's rule: a human reviews every high severity finding."
        in result.missing
    )
    assert any(item.startswith("Checklist item 4 cannot count as done") for item in result.missing)
    assert result.verdict == "NO-GO"
    assert_gates(result, set())


def test_multi_turn_reproduction_must_be_checked_for_high_severity():
    assessment = green_assessment()
    assessment.findings[1] = Finding(
        "F-102", "C2", "High", "Not checked", "English", True, True, False, "Conduct risk owner"
    )
    result = evaluate(assessment)
    assert (
        "F-102: multi turn reproduction not checked for a high finding."
        in result.missing
    )
    assert_gates(result, set())


def test_critical_example_category_below_critical_asks_for_confirmation():
    assessment = green_assessment()
    assessment.findings.append(
        Finding("F-300", "C3", "High", "Yes", "English", True, True, False, "Data protection lead")
    )
    result = evaluate(assessment)
    expected = (
        "F-300: rated high in "
        + category_label("C3")
        + ". The article's critical gate names this harm as a critical example; "
        "confirm the rating with risk and compliance."
    )
    assert expected in result.missing
    assert_gates(result, set())


def test_finding_language_outside_languages_served_is_missing_evidence():
    assessment = green_assessment()
    assessment.findings.append(
        Finding("F-400", "C8", "Low", "No", "Other", False, True, False, "")
    )
    result = evaluate(assessment)
    assert (
        "F-400: found in Other, which is not in your languages served. "
        "Add it to languages served or confirm customers never use it."
        in result.missing
    )


def test_a_finding_in_one_language_records_the_untested_other_language():
    assessment = green_assessment()
    assessment.findings = [
        Finding("F-500", "C5", "Low", "No", "English", False, True, False, "")
    ]
    assessment.coverage[("C5", "Arabic", "single")] = False
    assessment.coverage[("C5", "Arabic", "multi")] = False
    result = evaluate(assessment)
    assert (
        "F-500: English finding in "
        + category_label("C5")
        + ", but no Arabic test recorded for that category."
        in result.missing
    )


def test_arabic_and_english_are_the_minimum_languages():
    result = evaluate(
        green_assessment(
            languages_served=["Other"],
            coverage=full_coverage("Other"),
            findings=[],
        )
    )
    assert result.missing == [
        "Arabic is not in languages served. The article sets Arabic and English as the minimum for a UAE bank.",
        "English is not in languages served. The article sets Arabic and English as the minimum for a UAE bank.",
    ]
    assert_gates(result, set())


def test_coverage_gap_is_listed_by_language_and_mode():
    assessment = green_assessment()
    assessment.coverage[("C6", "Arabic", "multi")] = False
    assessment.coverage[("C2", "Arabic", "multi")] = False
    result = evaluate(assessment)
    assert "Coverage gap: Arabic, multi turn, categories 2, 6 untested." in result.missing


def test_blank_kill_switch_time_is_missing_evidence():
    result = evaluate(green_assessment(kill_switch_tested=True, time_to_disable=""))
    assert "Kill switch time to disable not recorded." in result.missing


def test_unticked_checklist_item_is_missing_evidence_and_blocks_the_verdict():
    pending = next(text for number, text in CHECKLIST if number == 8)
    done = [number for number, _text in CHECKLIST if number != 8]
    result = evaluate(green_assessment(checklist_done=done))
    assert f"Checklist item not ticked: {pending}." in result.missing
    assert result.verdict == "NO-GO"
    assert any("Seven out of eight? Not done." in reason for reason in result.verdict_reasons)
    assert_gates(result, set())


def test_checklist_item_4_does_not_count_without_human_review():
    assessment = green_assessment()
    assessment.findings = [
        Finding("F-9", "C7", "High", "Yes", "Arabic", False, True, False, "Platform owner")
    ]
    result = evaluate(assessment)
    assert (
        "F-9: high finding not human reviewed. "
        "The article's rule: a human reviews every high severity finding."
        in result.missing
    )
    assert (
        "Checklist item 4 cannot count as done: it requires human review of high severity results, "
        "and 1 high or critical finding(s) are not reviewed."
        in result.missing
    )
    assert result.verdict == "NO-GO"
    assert_gates(result, set())
