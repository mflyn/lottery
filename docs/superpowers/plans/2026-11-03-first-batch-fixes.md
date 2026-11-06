# First Batch Reliability Fixes Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task by task.

**Goal:** Reject invalid imports without changing history, validate real issue numbers, restore test collection, and migrate data-manager tests to JSON.

**Architecture:** Normalize supported import formats at the data-manager boundary, validate the complete batch, and replace history atomically. Reuse the current validators and JSON schema. Keep optional feature dependencies explicit.

**Tech Stack:** Python, pandas, pytest, JSON, openpyxl, SHAP/LIME, XGBoost.

**Spec:** The repair order and first-batch scope approved in this chat on 2026-11-03.

## Global Constraints

- Preserve existing user changes and history files; use temporary data in tests.
- SSQ issue format is seven digits (YYYYNNN); DLT is five digits (YYNNN).
- Invalid or partly invalid import batches return False without modifying history.
- Valid duplicate imports are successful no-ops; existing records take precedence.
- Retain CSV aliases date/issue/numbers at the import boundary.
- This batch excludes generator APIs, feature engineering, prize rules, and GUI behavior.

## Review Focus

- Invalid rows mixed with valid rows must not partially import.
- Failed serialization or replacement must preserve the original file.
- JSON list input and leading-zero DLT issues must round-trip.
- Already existing issues must not duplicate or overwrite history.
- Optional model dependencies must not break unrelated test collection.

## Task 1: Data correctness and JSON test migration

- [x] Replace legacy data-manager fixtures with temporary JSON histories.
- [x] Add import regressions for missing fields, invalid numbers/dates/issues, mixed batches, JSON list input, CSV round-trips, duplicate issues, and failed writes.
- [x] Add seven-digit SSQ issue and DLT sequence regressions; run and observe failures.
- [x] Normalize and validate imports before merging; use a temporary sibling file and atomic replacement.
- [x] Correct issue validation and statistics date-column usage exposed by JSON fixtures.
- [x] Run focused tests and verify all pass.

## Task 2: Collection and dependency configuration

- [x] Set pytest import mode to importlib and separate real-window tests with a gui marker.
- [x] Declare Excel/model-explanation dependencies and document macOS libomp setup.
- [x] Install required dependencies in the existing environment where permitted; report any remaining environment restriction.
- [x] Verify collection with the normal project command, then run non-GUI tests and controller tests.

## Execution Notes

- Ruling: The user explicitly approved executing the previously proposed first batch; no further design approval is needed.
- Ruling: Reuse the current checkout and leave changes uncommitted to preserve the existing mixed worktree.
- Ruling: The previous GUI run aborted in tk.Tk(); mark real-window tests for explicit desktop execution instead of rerunning an abort in the core suite. Do not claim GUI success.


## Verification Results

- Focused regression suite: 65 passed (data manager, issue validation, optional model imports).
- Project default suite: 177 passed, 25 failed, 0 collection errors, 6 real-window tests deselected, 2 warnings.
- Full test log: /private/tmp/lottery-batch1-full.log; focused log: /private/tmp/lottery-batch1-focused.log.
- XGBoost 3.1.1 loads successfully after installing Homebrew libomp 23.1.4.
- Installed openpyxl 3.1.5, xlrd 2.0.2, SHAP 0.54.1, and LIME 0.2.0.1 in the existing virtual environment; pip check reports no broken requirements.
- Read-only smoke checks: latest local SSQ/DLT records validate and keep their issue numbers after cleaning; real-tree SHAP explanation returns a (6, 2) array.
- Independent review found numeric-date coercion and sparse optional metadata serialization defects. Added failing regressions, corrected both, and obtained a clean follow-up review for those findings.
- Ruling: Reject ambiguous numeric dates; accept date strings and real Excel date cells. Reject explicit nonfinite values, retain absent metadata as null, and default missing optional amounts to zero.
- Ruling: Existing failures outside the approved first batch remain visible. Three model-pipeline failures, previously hidden behind missing dependencies, now expose the existing missing DataPreprocessor._setup_default_config method.
- Scoped diff whitespace checks pass. Existing user changes, including history files and prize-rule edits, were not edited by this batch.
