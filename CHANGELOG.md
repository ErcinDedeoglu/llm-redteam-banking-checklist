# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Go-live gate pytest job runs on Python 3.10, 3.11, 3.12 and 3.13, the package declares the 3.13 classifier, and the README shows the Go-live gate status badge (2026-11-05).
- This changelog, so each change to the gate, the categories and the skill has a dated entry.
- Defender-side `llm-redteam-banking` Agent Skill under `skills/`, with the `skills` CLI install documented in the README (#5, 2026-10-23).
- Issue forms, a pull request checklist and the Contributor Covenant 2.1 code of conduct (#4, 2026-10-23).

## [0.1.0] - 2026-10-21

### Added
- The banking LLM go-live gate: `evaluate()`, five gates, harm categories with severity, pytest checks, a GitHub Actions workflow and a markdown evidence pack.
- `CITATION.cff` with ORCID, an SPDX license header and a PyPI Trusted Publishing workflow kept behind `PYPI_PUBLISH` (#1, #2).
- Release to GitHub and Zenodo.

### Changed
- Release metadata cleaned before tagging: release date fixed (#3).

[Unreleased]: https://github.com/ErcinDedeoglu/llm-redteam-banking-checklist/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ErcinDedeoglu/llm-redteam-banking-checklist/releases/tag/v0.1.0
