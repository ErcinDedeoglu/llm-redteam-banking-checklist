# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""A material change restarts the loop. The six article triggers all do."""

import pytest

from llm_redteam_banking import RETEST_TRIGGERS, evaluate

from helpers import assert_gates, green_assessment


def test_no_declared_change_leaves_the_verdict_at_go():
    result = evaluate(green_assessment(changes_since_last_run=[]))
    assert result.notes == []
    assert result.verdict == "GO"
    assert_gates(result, set())


@pytest.mark.parametrize("trigger", RETEST_TRIGGERS)
def test_each_retest_trigger_forces_a_new_run(trigger):
    result = evaluate(green_assessment(changes_since_last_run=[trigger]))
    assert_gates(result, set())
    assert result.verdict == "NO-GO"
    assert result.notes == [
        "Changed since the last run: "
        + trigger
        + ". Re-run the suite before this verdict counts."
    ]
    assert result.verdict_reasons == [
        "Material change since the last run. Any material change restarts the loop: re-test first."
    ]


def test_retest_note_names_every_declared_change():
    changes = ["System prompt", "Retrieval corpus"]
    result = evaluate(green_assessment(changes_since_last_run=changes))
    assert result.notes == [
        "Changed since the last run: System prompt; Retrieval corpus. "
        "Re-run the suite before this verdict counts."
    ]
    assert result.verdict == "NO-GO"


def test_retest_trigger_catalog_matches_the_article():
    assert RETEST_TRIGGERS == [
        "Model or version (including provider side automatic updates)",
        "System prompt",
        "Retrieval corpus",
        "Tools or agent permissions",
        "Guardrail configuration",
        "Languages served",
    ]
