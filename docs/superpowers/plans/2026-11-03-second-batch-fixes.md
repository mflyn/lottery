# Feature Engineering and Generator Repairs

> **For agentic workers:** Use superpowers:executing-plans and test-driven-development.

**Goal:** Resolve the 20 reproduced feature/generator failures with real behavior tests and preserve the first batch.
**Spec:** User-approved second batch in this chat, 2026-11-03.
**Architecture:** Normalize number columns once for feature extraction and frequency analysis; keep DataFrame feature APIs and typed number outputs; exercise recommendation/control paths with real components.
**Tech Stack:** Python, pandas, NumPy, scikit-learn, pytest.

## Constraints

- Preserve prior user and first-batch changes; do not edit real history files.
- No new legacy generator methods merely to satisfy obsolete tests.
- Keep row indexes aligned and feature values finite; temporal calculations must not use future rows.
- Reject invalid lottery types and malformed number/count inputs explicitly.
- Do not change prize rules, model preprocessor initialization, or real GUI behavior.

## Tasks

- [x] Replace obsolete Mock/old-API tests with real supported-API regressions and observe failures.
- [x] Add shared number-column normalization for canonical lists, strings, expanded columns, and SSQ blue aliases.
- [x] Correct feature statistics, consecutive counts, blue features, causal rolling windows, DLT index alignment, and feature-selection indexes.
- [x] Connect controller period-based requests to an explicit history-loading feature API; test real callbacks.
- [x] Migrate random-generator tests to generate(count) and typed numbers; reject invalid types/counts.
- [x] Normalize frequency-analysis input so integrated smart generation does not silently fall back on valid history.
- [x] Exercise real recommendation training with arrays/DataFrames, validate inputs, order history chronologically, and use the latest feature row for candidates.
- [x] Run targeted tests, the project default suite, and an independent scoped review.

## Review Focus

- Partial/invalid columns, numeric strings, aliases and nondefault indexes.
- Derived input columns must not be counted as lottery balls.
- Short rolling windows and shuffled histories must not leak future values.
- Controller and recommendation tests must exercise actual core objects.
- Previous-batch regression suite must stay green; report unrelated baseline failures.


## Results

- Targeted baseline: 20 failed, 20 passed. Final targeted suite: 76 passed (one environment CPU-detection warning).
- Final default suite: 233 passed, 5 failed, 0 collection errors, 6 real-window tests deselected, 3 warnings.
- All 65 first-batch regression cases passed in the final default suite.
- Scoped whitespace/diff checks passed.
- Real local-history smoke checks used 30 SSQ and 30 DLT draws with the default three models: feature matrices (30, 14) and (30, 17), with two validated recommendations each. The default MLP emitted a non-convergence warning on SSQ; model tuning remains outside this batch.
- Independent review found target-Series label misalignment and a mismatch with the existing view's callback payload. Added failing regressions and fixed both; the reviewer independently confirmed 8 relevant cases pass and no new blocker.
- Ruling: Retain the core DataFrame API and typed generate(count) API. Migrate tests for nonexistent legacy APIs rather than recreating those methods.
- Ruling: Series targets align by unique labels; arrays use positional semantics. Apply this rule to feature selection, importance and DataFrame-based training.
- Ruling: The controller adapts core DataFrames into the existing view's structured callback payload, including raw history and float-normalized features; no real Tk window was launched.
- Remaining failures: numeric-cleaning scalar-type assertion; three model-pipeline setup failures due to missing DataPreprocessor._setup_default_config; DLT prize-level assertion 7 versus 9. No prize rules or model-preprocessor behavior were changed.
- Logs: /private/tmp/lottery-batch2-focused.log, /private/tmp/lottery-batch2-full.log, /private/tmp/lottery-batch2-smoke.log.
