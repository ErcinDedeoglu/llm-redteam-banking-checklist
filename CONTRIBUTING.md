# Contributing

Thanks for looking at the checklist. The repository is [llm-redteam-banking-checklist](https://github.com/ErcinDedeoglu/llm-redteam-banking-checklist). The maintainer is [Ercin Dedeoglu](https://ercin.info).

Views are my own.

## Ground rules

This is a defender's tool. It scores findings a team has already recorded. It does not generate tests, call a model, or store what you type.

- Synthetic findings only. No customer data, no live model output, and no attack prompts in issues, pull requests, examples, or tests.
- Record a harm by category and severity. A finding ref is a ticket id, not a prompt.
- Keep `evaluate()` and the `Finding` model compatible with the [Hugging Face Space](https://huggingface.co/spaces/Ercin/llm-red-teaming-banking-severity-scorer). Change the rules engine only when the article's rule changed, and say why in the pull request.
- The CLI exits 1 when any of the five go-live gates is red. Checklist gaps and re-test triggers stay in the verdict and the evidence pack.

## Develop

Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
llm-redteam-gate examples/passing.yaml -o /tmp/passing-evidence.md
llm-redteam-gate examples/failing.yaml -o /tmp/failing-evidence.md
```

The passing command exits 0. The failing command exits 1 and prints the red gate names.

## License

By contributing you agree that your contribution is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
