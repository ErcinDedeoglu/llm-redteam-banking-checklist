# Copyright 2026 Ercin Dedeoglu
# SPDX-License-Identifier: Apache-2.0
"""Go-live checklist for banking LLM red-team findings.

``evaluate`` is the rules engine from the Hugging Face Space
https://huggingface.co/spaces/Ercin/llm-red-teaming-banking-severity-scorer.
Wire that same function into pytest and into the ``llm-redteam-gate`` CLI.
"""

from importlib.metadata import PackageNotFoundError, version

from llm_redteam_banking.load import FindingsFileError, load_assessment
from llm_redteam_banking.scorer import (
    ARTICLE_URL,
    CATEGORIES,
    CATEGORY_CHOICES,
    CHECKLIST,
    CRITICAL_EXAMPLE_CATEGORIES,
    LABEL_TO_CODE,
    LANGUAGES,
    MULTI_TURN,
    RETEST_TRIGGERS,
    SEVERITIES,
    Assessment,
    Finding,
    Result,
    category_label,
    evaluate,
    evidence_pack_md,
)

try:
    __version__ = version("llm-redteam-banking-checklist")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "ARTICLE_URL",
    "CATEGORIES",
    "CATEGORY_CHOICES",
    "CHECKLIST",
    "CRITICAL_EXAMPLE_CATEGORIES",
    "LABEL_TO_CODE",
    "LANGUAGES",
    "MULTI_TURN",
    "RETEST_TRIGGERS",
    "SEVERITIES",
    "Assessment",
    "Finding",
    "FindingsFileError",
    "Result",
    "category_label",
    "evaluate",
    "evidence_pack_md",
    "load_assessment",
]
