# Unified Fusion Scoring Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with test-driven-development; one final fresh code review.

**Goal:** Replace the legacy percentile score with the existing fusion utility in the evaluators, GUI, export and top-score search.

**Architecture:** A shared evaluator adapter builds one canonical historical snapshot and delegates scoring to FusionFeatureContext/FusionPortfolioObjective. Single-ticket evaluation uses K=1 (D=0); descriptive statistics share that snapshot. GUI and search consume the same factors and configuration.

**Tech Stack:** Existing Python, NumPy, pandas, Tk and pytest; no new dependency.

**Spec:** Existing maximum-entropy fusion design, extended by the user's request to replace the old percentage score.

## Global Constraints

- Native F and signed six-factor contributions; no old /100 conversion or arbitrary quality stars.
- Default history 180; None explicitly selects all available records. Scoring and descriptive statistics use the same canonical snapshot.
- SSQ and DLT both regions participate. Empty history, unseen balls and exact historical matches must be handled consistently.
- Preserve current uncommitted work and data. Execute directly under the user's request, no additional approval or commits.
- Top-score search remains a restricted candidate search, ranks K=1 F without rounding, and uses the evaluation profile frozen on the UI thread.

## Review Focus

- Negative F values must sort and display with adequate precision.
- Identical ticket/snapshot/config must score identically in recommendation, evaluation and search.
- Changing profile/c彩种/history while evaluation runs cannot relabel or alter the delivered result.
- Unseen/censored omissions and full exact matches must retain correct descriptive details.
- Repeated candidate scoring must reuse features/context, not reload history per candidate.

## Task 1: Unified evaluation adapter

Files: new `src/core/evaluators/fusion_evaluation.py`; modify both evaluator classes and base; tests `tests/unit/test_fusion_evaluation.py`.

- [x] Write tests for direct fusion equivalence, custom weights, canonical windows, exact matches, censored omissions, empty history, both zones and context reuse; run and observe RED.
- [x] Add `prepare_fusion_context`, `score_ticket`, shared evaluation and portable FusionResult. Remove legacy percentage scoring functions; preserve descriptive result fields and a native-F `total_score` compatibility alias.
- [x] Normalize/sort/truncate once; fix full-match early exit and unseen omission counts. Return native factors/contributions and deterministic-evaluation metadata.
- [x] Run core evaluation and fusion tests; require PASS.

## Task 2: Interface, reports and search

Files: new `src/gui/fusion_evaluation.py`; modify evaluation frame, generation frame and `scripts/find_top_{ssq,dlt}.py`; tests GUI and search.

- [x] Update GUI contracts for six factors/native F and add export, invalid-profile, active-request-isolation and search equivalence regressions; observe RED.
- [x] Replace percentage/settings widgets with six-weight settings, signed contributions and a K=1 explanation. Freeze snapshot/config/lottery in requests; Markdown and JSON export the captured context.
- [x] Top search prepares one context, ranks native F without rounding, uses requested history/profile and actual data-manager paths. Remove obsolete legacy curve/blue-weight controls from this route.
- [x] Run focused tests and real-window suite; require PASS.

## Task 3: Review and complete verification

- [x] Obtain one independent read-only review, fix material findings with regression coverage.
- [x] Run the complete desktop suite, record results/warnings and check history file hashes unchanged.
- [x] Update usage documentation and report the implemented scoring semantics and final results.

## Execution record

- User requested replacement of the old scoring method; proceed within that scope using the approved fusion engine.
- `total_score` remains a numeric API alias for F, but percentage factors/rating logic are removed rather than mixed with the new score.
- Core tests observed RED on old evaluation and search interfaces, then 56 fusion/evaluation tests passed; search adds 2 tests.
- Fixed a reproduced parallel-snapshot cache collision by making legacy descriptive SSQ statistics request-local. Controlled two-thread regression RED→GREEN.
- GUI tests cover native precision, six factors, JSON/Markdown export, invalid weights and profile/c彩种 capture. Existing full GUI suite then 42 passed.
- Added a two-outcome late-delivery regression (obsolete success and obsolete error); request IDs now discard older evaluation results.
- Search decision: return at most top_k, resolving equal F lexicographically, rather than collecting an unbounded number of ties. This bounds memory for zero-weight or tied profiles and matches the GUI's requested count.
- Independent review: no Critical/Important findings. Fixed the selected-window historical-match wording and added actual record count metadata; the metadata regression was observed RED→GREEN. Added both-lottery equal-score cap/order tests. No deferred findings remain.
- First complete desktop run: 464 passed, 2 existing warnings, 39.95s; final verification repeated after the review fix and additional tie tests.

- Final complete desktop suite: 466 passed, 0 failures, 0 errors, 0 skipped, 2 existing warnings, 36.94s. XML `/private/tmp/lottery-score-migration-full.xml`; log `/private/tmp/lottery-score-migration-full.log`.
- Focused fusion/evaluation/search tests: 61 passed. Full suite includes 44 real-window tests. History-file hashes verified unchanged after the full run.
