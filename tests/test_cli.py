# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""The CLI is the CI step: green example exits 0, red example exits 1."""

import json
import subprocess
import sys
import sysconfig
from importlib.metadata import entry_points, version
from pathlib import Path

import yaml

from llm_redteam_banking import __version__
from llm_redteam_banking.cli import main

ROOT = Path(__file__).resolve().parents[1]
PASSING = ROOT / "examples" / "passing.yaml"
FAILING = ROOT / "examples" / "failing.yaml"


def test_cli_passing_example_exits_zero_and_writes_the_pack(tmp_path, capsys):
    pack = tmp_path / "evidence" / "pack.md"
    code = main([str(PASSING), "--evidence-pack", str(pack)])
    output = capsys.readouterr().out
    assert code == 0
    assert "verdict: GO" in output
    assert "red gates: none" in output
    assert "FAIL" not in output
    text = pack.read_text(encoding="utf-8")
    assert "## Verdict: GO" in text
    assert "Ercin Dedeoglu" in text


def test_cli_failing_example_exits_nonzero_and_names_the_red_gates(tmp_path, capsys):
    pack = tmp_path / "pack.md"
    code = main([str(FAILING), "-o", str(pack)])
    output = capsys.readouterr().out
    assert code == 1
    assert "verdict: NO-GO" in output
    assert "FAIL  Critical findings: zero open at go-live" in output
    assert "FAIL  High findings: each has a fix or compensating control and a named owner" in output
    assert "red gates:" in output
    assert "- Critical findings: zero open at go-live:" in output
    assert "- High findings: each has a fix or compensating control and a named owner:" in output
    text = pack.read_text(encoding="utf-8")
    assert "## Verdict: NO-GO" in text
    assert "F-201" in text
    assert "F-202" in text


def test_cli_accepts_the_same_pack_as_json(tmp_path, capsys):
    data = yaml.safe_load(PASSING.read_text(encoding="utf-8"))
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    code = main([str(path), "-o", str(tmp_path / "pack.md")])
    assert code == 0
    assert "verdict: GO" in capsys.readouterr().out


def test_material_change_does_not_by_itself_turn_the_exit_code_red(tmp_path, capsys):
    data = yaml.safe_load(PASSING.read_text(encoding="utf-8"))
    data["changes_since_last_run"] = ["System prompt"]
    path = tmp_path / "changed.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    code = main([str(path), "-o", str(tmp_path / "pack.md")])
    output = capsys.readouterr().out
    assert code == 0
    assert "verdict: NO-GO" in output
    assert "red gates: none" in output
    assert "System prompt" in output
    assert "exits 0 because no gate is red" in output


def test_cli_rejects_a_bad_file_without_writing_a_pack(tmp_path, capsys):
    path = tmp_path / "bad.yaml"
    path.write_text("prompt: removed\nfindings: []\n", encoding="utf-8")
    code = main([str(path), "-o", str(tmp_path / "pack.md")])
    assert code == 2
    assert "unknown field" in capsys.readouterr().err
    assert not (tmp_path / "pack.md").exists()


def test_cli_missing_file_exits_2(tmp_path, capsys):
    code = main([str(tmp_path / "missing.yaml"), "-o", str(tmp_path / "pack.md")])
    assert code == 2
    assert "not found" in capsys.readouterr().err


def test_package_version_matches_the_installed_metadata():
    assert __version__ == version("llm-redteam-banking-checklist") == "0.1.0"


def test_console_script_points_at_the_cli():
    scripts = {item.name: item.value for item in entry_points(group="console_scripts")}
    assert scripts["llm-redteam-gate"] == "llm_redteam_banking.cli:main"


def test_module_and_script_both_fail_the_red_example(tmp_path):
    pack = tmp_path / "pack.md"
    module = subprocess.run(
        [sys.executable, "-m", "llm_redteam_banking", str(FAILING), "-o", str(pack)],
        check=False,
        capture_output=True,
        text=True,
    )
    script = Path(sysconfig.get_path("scripts")) / "llm-redteam-gate"
    assert script.is_file()
    via_script = subprocess.run(
        [str(script), str(FAILING), "-o", str(pack)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert module.returncode == 1
    assert via_script.returncode == 1
    assert "Critical findings: zero open at go-live" in module.stdout
    assert "red gates:" in module.stdout
    assert module.stdout == via_script.stdout
    assert "NO-GO" in pack.read_text(encoding="utf-8")
