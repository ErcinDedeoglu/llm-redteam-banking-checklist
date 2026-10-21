# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""The gate workflow, the reusable workflow, and the composite action parse."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict:
    path = ROOT / relative
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), path
    return data


def test_gate_workflow_runs_pytest_and_both_examples():
    workflow = _load(".github/workflows/gate.yml")
    assert set(workflow["jobs"]) == {
        "test-and-gate",
        "reusable-passing-gate",
        "composite-failing-gate",
    }
    steps = workflow["jobs"]["test-and-gate"]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)
    assert "python -m pytest" in scripts
    assert "examples/passing.yaml" in scripts
    assert "examples/failing.yaml" in scripts
    assert "expected exit code 1" in scripts
    reusable = workflow["jobs"]["reusable-passing-gate"]
    assert reusable["uses"] == "./.github/workflows/reusable-gate.yml"
    assert reusable["with"]["findings"] == "examples/passing.yaml"
    composite = workflow["jobs"]["composite-failing-gate"]["steps"]
    gate = next(step for step in composite if step.get("uses", "").endswith("llm-redteam-gate"))
    assert gate["continue-on-error"] is True
    assert gate["with"]["findings"] == "examples/failing.yaml"


def test_reusable_workflow_fails_the_job_when_the_gate_is_red():
    workflow = _load(".github/workflows/reusable-gate.yml")
    assert "workflow_call" in workflow["on"]
    assert workflow["on"]["workflow_call"]["inputs"]["findings"]["required"] is True
    script = workflow["jobs"]["gate"]["steps"][-2]["run"]
    assert "llm_redteam_banking" in script
    assert "--evidence-pack" in script


def test_composite_action_invokes_the_same_gate():
    action = _load(".github/actions/llm-redteam-gate/action.yml")
    assert action["runs"]["using"] == "composite"
    assert action["inputs"]["findings"]["required"] is True
    script = action["runs"]["steps"][-1]["run"]
    assert "llm_redteam_banking" in script
    assert "--evidence-pack" in script


def test_release_workflow_publishes_only_on_release_with_oidc():
    workflow = _load(".github/workflows/release.yml")
    assert workflow["on"]["release"]["types"] == ["published"]
    assert workflow["permissions"] == {"contents": "read"}
    build = "\n".join(step.get("run", "") for step in workflow["jobs"]["build"]["steps"])
    assert "python -m pytest" in build
    assert "twine check" in build
    publish = workflow["jobs"]["publish"]
    assert publish["needs"] == "build"
    assert publish["if"] == "vars.PYPI_PUBLISH == 'true'"
    assert publish["permissions"] == {"id-token": "write"}
    assert publish["environment"]["name"] == "pypi"
    uses = [step.get("uses", "") for step in publish["steps"]]
    assert any(u.startswith("pypa/gh-action-pypi-publish@") for u in uses)
