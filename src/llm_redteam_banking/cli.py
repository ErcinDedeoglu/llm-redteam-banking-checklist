# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""Command line gate. Exits non-zero when any go-live gate is red."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llm_redteam_banking import __version__
from llm_redteam_banking.load import FindingsFileError, load_assessment
from llm_redteam_banking.scorer import evaluate, evidence_pack_md


def main(argv: list[str] | None = None) -> int:
    """Evaluate a findings file. Return 1 when a gate is red, 2 when the file is unusable."""

    parser = argparse.ArgumentParser(
        prog="llm-redteam-gate",
        description=(
            "Run evaluate() on a banking LLM red-team findings file and "
            "exit non-zero when any go-live gate is red."
        ),
    )
    parser.add_argument("findings", type=Path, help="Findings file (.json, .yaml, or .yml)")
    parser.add_argument(
        "-o",
        "--evidence-pack",
        type=Path,
        default=Path("evidence-pack.md"),
        help="Where to write the markdown evidence pack (default: evidence-pack.md)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        assessment = load_assessment(args.findings)
    except (FindingsFileError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = evaluate(assessment)
    _print_report(assessment.system_name, result)
    try:
        _write_pack(args.evidence_pack, assessment, result)
    except OSError as exc:
        print(f"error: could not write the evidence pack: {exc}", file=sys.stderr)
        return 2

    print(f"evidence pack: {args.evidence_pack}")
    red = [name for name, ok, _why in result.gates if not ok]
    return 1 if red else 0


def _print_report(system_name: str, result) -> None:
    print(system_name.strip() or "unnamed system")
    print(f"verdict: {result.verdict}")
    for reason in result.verdict_reasons:
        print(f"  {reason}")
    print()
    for name, ok, why in result.gates:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        print(f"      {why}")
    if result.notes:
        print()
        for note in result.notes:
            print(f"note: {note}")
    print()
    red = [(name, why) for name, ok, why in result.gates if not ok]
    if red:
        print("red gates:")
        for name, why in red:
            print(f"- {name}: {why}")
        return
    print("red gates: none")
    if result.verdict == "NO-GO":
        print(
            "The five gates are green. The article verdict is still NO-GO "
            "until the checklist is complete and any material change has been re-tested. "
            "This command exits 0 because no gate is red."
        )


def _write_pack(path: Path, assessment, result) -> None:
    if path.exists() and path.is_dir():
        raise OSError(f"{path} is a directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(evidence_pack_md(assessment, result), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
