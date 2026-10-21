# llm-redteam-banking-checklist

Look. A green demo is not a green release.

This is a defender-side gate for **LLM red teaming in banking**. You record findings by harm category and severity. The same `evaluate()` function that runs in the [Hugging Face Space](https://huggingface.co/spaces/Ercin/llm-red-teaming-banking-severity-scorer) runs in pytest and in CI. A red gate fails the process. You still get the markdown evidence pack.

The rules come from [LLM Red Teaming for Banking: A UAE Go-Live Checklist](https://huggingface.co/blog/Ercin/llm-red-teaming-banking-uae). Where that article sets no number, this tool says so.

Educational tool, not regulatory or legal advice. No attack prompts. No model calls. Nothing you score is uploaded.

Views are my own.

**Ercin Dedeoglu**, AI/Software Architect, Dubai. [ercin.info](https://ercin.info)

## 60-second quickstart

Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

llm-redteam-gate examples/passing.yaml -o evidence-pack.md
echo "passing exit: $?"

llm-redteam-gate examples/failing.yaml -o evidence-pack.md
echo "failing exit: $?"
```

`examples/passing.yaml` is a synthetic retail assistant. Five gates. All green. The command exits **0**.

`examples/failing.yaml` is the same kind of pack. One critical finding is still open. One high finding has no fix, no compensating control, and no owner. The command exits **1** and prints:

```text
red gates:
- Critical findings: zero open at go-live: 1 open critical finding(s): F-201
- High findings: each has a fix or compensating control and a named owner: F-202 (no fix or compensating control, no named owner)
```

Both commands write `evidence-pack.md`. The examples are fictional. Category, severity, and ownership only.

Install the tagged release straight from GitHub:

```bash
pip install "git+https://github.com/ErcinDedeoglu/llm-redteam-banking-checklist@v0.1.0"
```

Once the package is on PyPI, the install line is:

```bash
pip install llm-redteam-banking-checklist
```

Call it from Python the same way the tests do:

```python
from llm_redteam_banking import evaluate, load_assessment

assessment = load_assessment("examples/passing.yaml")
result = evaluate(assessment)
red = [name for name, ok, _why in result.gates if not ok]
raise SystemExit(1 if red else 0)
```

JSON uses the same fields as YAML. Quote `Yes` and `No` in YAML (`multi_turn: "Yes"`). Frankly, an unquoted `Yes` is a YAML boolean. The loader accepts that too.

| Exit code | Meaning |
| --- | --- |
| 0 | All five gates passed. |
| 1 | At least one gate is red. The names are printed, and the evidence pack is still written. |
| 2 | The findings file could not be read. |

The article verdict can be `NO-GO` while the five gates are green. An incomplete checklist does it. A re-test trigger does it. That verdict is printed and stored in the evidence pack. The process exit code follows the five gates.

## How the CI gate works

[`.github/workflows/gate.yml`](.github/workflows/gate.yml) does three things on every push and pull request:

1. Installs this package and runs pytest, including one test that calls `evaluate()` on each example and asserts the gate result.
2. Runs `llm-redteam-gate` on `examples/passing.yaml` and fails the job if that pack is red.
3. Runs it on `examples/failing.yaml` and fails the job unless the exit code is 1.

The evidence packs are uploaded as workflow artifacts.

### Copy this into another repository

Checkout your findings file. Install the checklist. Fail the job when a gate is red. Set `package` to `.[dev]` inside this repository. Set it to `llm-redteam-banking-checklist` once you install the published package. Point `findings` at the JSON or YAML file you want to gate.

```yaml
name: Release gate

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  go-live-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Install the checklist
        run: python -m pip install --disable-pip-version-check llm-redteam-banking-checklist
      - name: Fail the release when a gate is red
        run: python -m llm_redteam_banking path/to/findings.yaml --evidence-pack evidence-pack.md
      - uses: actions/upload-artifact@v7
        with:
          name: evidence-pack
          path: evidence-pack.md
          if-no-files-found: error
```

### Reusable workflow

[`.github/workflows/reusable-gate.yml`](.github/workflows/reusable-gate.yml) is a `workflow_call` workflow. Copy it into the releasing repository and call it:

```yaml
jobs:
  go-live:
    uses: ./.github/workflows/reusable-gate.yml
    with:
      findings: redteam/findings.yaml
      evidence-pack: evidence-pack.md
      package: llm-redteam-banking-checklist
```

This repository calls that same workflow on `examples/passing.yaml` with `package: ".[dev]"`, so the reusable file is what CI runs.

### Composite action

[`.github/actions/llm-redteam-gate/action.yml`](.github/actions/llm-redteam-gate/action.yml) is the same gate as one step. The caller checks out the repository first. This repository runs the action on `examples/failing.yaml` and requires the step to fail.

```yaml
steps:
  - uses: actions/checkout@v7
  - uses: ./.github/actions/llm-redteam-gate
    with:
      findings: redteam/findings.yaml
      evidence-pack: evidence-pack.md
      package: llm-redteam-banking-checklist
```

Copy the `action.yml` directory into the releasing repository, or vendor this action next to the findings file. The action sets up Python, installs the package, runs `evaluate()` through the CLI, and returns a failed step when a gate is red.

## The five gates

Agreed before the first run. Names below are the strings the CLI prints.

| Gate | Passes when |
| --- | --- |
| Critical findings: zero open at go-live | No open critical finding remains. |
| High findings: each has a fix or compensating control and a named owner | Every high finding is fixed or has a compensating control, and has a named owner. |
| Coverage: every category x every language served x single and multi turn | All nine categories are tested in every language you serve, single turn and multi turn. |
| Kill switch: tested end to end, time to disable recorded | The switch was tested, and the time you recorded is in the file. |
| Monitoring: production logging and alerting for the same categories | Logging and alerting cover all nine categories. |

Two further article rules show up in the verdict, the missing-evidence list, and the evidence pack:

- The go-live checklist. Items 3 (coverage) and 6 (kill switch) come from the gates above. The file ticks items 1, 2, 4, 5, 7, and 8. Seven out of eight is still `NO-GO`.
- Re-test triggers. Any material change restarts the loop: model or version (including a provider-side automatic update), system prompt, retrieval corpus, tools or agent permissions, guardrail configuration, languages served.

Medium and low findings are counted. They do NOT, by themselves, turn a gate red.

You set these. The article leaves them open:

- Numeric severity weights. Set all four of Critical, High, Medium, and Low to see a weighted score of open findings. The weights are yours.
- A maximum time to disable. Record the time you measured.
- The gate thresholds themselves, which the article labels as examples to agree with risk and compliance.

## Findings file

```yaml
system_name: Harborline Retail Assistant (synthetic)
languages_served: [Arabic, English]
kill_switch_tested: true
time_to_disable: "3 min 40 sec, recorded in the change-window log"
monitored_categories: [C1, C2, C3, C4, C5, C6, C7, C8, C9]
checklist_done: [1, 2, 4, 5, 7, 8]   # 3 and 6 are the coverage and kill-switch gates
changes_since_last_run: []            # any entry forces a re-test before the verdict counts
findings:
  - ref: F-101                         # ticket id, never a prompt
    category: C1                       # C1–C9
    severity: Critical                 # Critical, High, Medium, Low
    multi_turn: "Yes"                  # Yes, No, Not checked
    language: Arabic                   # Arabic, English, Other
    human_reviewed: true
    fixed: true
    compensating_control: false
    owner: Fraud lead
coverage:
  C1: {Arabic: {single: true, multi: true}, English: {single: true, multi: true}}
  # C2–C9 in the same shape. An unticked cell fails the coverage gate.
```

A list form is also accepted: `{category, language, mode, tested}`. Unknown fields are rejected, including anything named like a prompt.

## OWASP LLM Top 10 (2025)

The mapping is the one already in the scorer. Categories 1 and 2 carry no OWASP code there.

| Code | Harm | OWASP LLM Top 10 (2025) |
| --- | --- | --- |
| C1 | Financial-crime facilitation | none |
| C2 | Conduct and suitability breaches | none |
| C3 | Sensitive information disclosure | LLM02 |
| C4 | System prompt leakage | LLM07 |
| C5 | Prompt injection through content the system reads | LLM01 |
| C6 | Retrieval-layer weaknesses | LLM08 |
| C7 | Excessive agency | LLM06 |
| C8 | Misinformation | LLM09 |
| C9 | Unbounded consumption | LLM10 |

## Evidence pack

`evidence_pack_md()` writes the verdict, the severity table (critical first), the five gates, the findings, the missing evidence, and the scope. Still attach your own scope record, taxonomy version, test-set version, and sign-off. Keep test prompts in access-controlled storage. Share categories, metrics, and findings.

## Method

Every category, gate, and trigger is taken from the article and the sources it cites, including the OWASP Gen AI Security Project Top 10 for LLM Applications (2025) and the Central Bank of the UAE guidance note on AI and ML (11 Feb 2026). This checklist turns that reading into a repeatable gate. It does NOT certify compliance.

The same scorer is live as a Gradio app: [llm-red-teaming-banking-severity-scorer](https://huggingface.co/spaces/Ercin/llm-red-teaming-banking-severity-scorer).

## Development

```bash
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Apache License 2.0, see [LICENSE](LICENSE). If you use the package, see [CITATION.cff](CITATION.cff).

Built by [Ercin Dedeoglu](https://ercin.info). Views are my own.
