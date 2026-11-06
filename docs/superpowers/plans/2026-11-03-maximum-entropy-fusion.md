# Maximum Entropy Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved maximum-entropy portfolio generator for SSQ/DLT, integrate Tk controls and reproducible export, and pass the full desktop test suite.

**Architecture:** Immutable configuration/history feed pure bounded features and an incremental portfolio objective. A request-local Metropolis sampler returns a structured result with explanations and diagnostics; the GUI passes frozen inputs to a cancellable worker and renders/exports that result.

**Tech Stack:** Existing Python, NumPy, pandas, pytest and Tk; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-03-maximum-entropy-fusion-design.md` (approved 2026-11-03).

## Global Constraints

- Preserve existing uncommitted repairs and history files; do not commit unrelated work.
- Both supported lotteries; integer 1 ≤ K ≤ 100; complete tickets unique.
- Implement all six factors and Q(S) proportional to exp(K F(S)/tau); tau > 0.
- Uniform proposals plus symmetric one-ball swaps; duplicate proposals are self-loops.
- All-zero weights use exact uniform sampling; finite runs are labeled approximate.
- Same snapshot/config/seed/environment reproduce outputs; no global RNG mutation.
- No worker accesses Tk; cancellation at most every 100 proposals and during reference preparation.

## Review Focus

- Changing UI controls/data during generation must not relabel the running request or export another snapshot.
- Empty, unsorted, duplicated or gapped histories must not fabricate exact omission counts.
- Numeric extremes, booleans and malformed input must fail before starting a worker.
- Cancellation immediately before result delivery must not publish a successful stale result.
- K=100 and a cold reference cache must remain cancellable; incremental scoring must not drift.

## Task 1: Immutable inputs and feature model

**Files:** Create `src/core/generators/fusion/{config,history,features}.py`, `__init__.py`; create `tests/unit/test_fusion_features.py`.

**Interfaces:** `FusionConfig`, `FusionHistorySnapshot.from_data(lottery_type, data, periods)`, `FusionFeatureContext(snapshot, config, cancel_event=None)`, `context.ticket_features(ticket)` returning H/T/C/R and contribution; tickets are tuples of sorted area tuples.

- [x] Add tests for defaults/invalid config, snapshot ordering/dedup/conflicts/truncation/copy, censored omissions, bounded two-zone features, empty history, fixed reference and cancellation.
- [x] Run `.venv/bin/python -m pytest tests/unit/test_fusion_features.py -q -p no:cacheprovider` and observe missing implementation failures.
- [x] Implement immutable data validation, shrinking frequency/EWMA, JSD targets, cached regularized joint shape features, style and historical novelty costs per spec.
- [x] Run the same focused tests; require PASS.

## Task 2: Portfolio objective and sampler

**Files:** Create `src/core/generators/fusion/{objective,sampler,result}.py`; modify `src/core/generators/factory.py`; create `tests/unit/test_fusion_sampler.py`.

**Interfaces:** `FusionPortfolioObjective(context, tickets)` with `propose(index,ticket)` and `accept(proposal)`; `MaximumEntropyFusionGenerator.generate_portfolio(count, snapshot, config, cancel_event=None, progress=None) -> FusionResult`; `generate` adapts to existing models; `FusionResult.to_dict()/to_markdown()` and `reevaluate()` reuse the snapshot.

- [x] Write tests for exact toy transition balance using production proposal/acceptance functions, uniform neutral sampling, deterministic seeds, increment/full recomputation, nonredundant E/D, K=1/100, both lotteries and cancellation.
- [x] Observe missing implementation failures with `.venv/bin/python -m pytest tests/unit/test_fusion_sampler.py -q -p no:cacheprovider`.
- [x] Implement cached/incremental objective, symmetric sampling, log acceptance, 4 independent chains, final-state selection and diagnostics; factory registration.
- [x] Implement JSON/Markdown export containing config, snapshot, explanations, reference version and seed; verify immutable reevaluation after caller data changes.
- [x] Run both fusion unit modules; require PASS.

## Task 3: GUI controls, execution and export

**Files:** Create `src/gui/fusion_controls.py`; modify `src/gui/generation_frame.py`; add real-window tests in `tests/gui/test_main_window.py`.

**Interfaces:** `FusionControls.read_request()` returns validated config; frozen history and request type travel in the worker result; the frame stores `fusion_result` independently of mutable controls.

- [x] Add GUI tests for parameter validation, both-lottery generation/reevaluation/export, snapshot isolation, cancellation and closing a genuinely active worker.
- [x] Run these tests through the desktop runner and observe the missing fusion controls/strategy failures.
- [x] Add fusion controls (history, tau, seed, advanced weights), worker/result queue branch, progress/cancel controls and expandable explanation.
- [x] Hide incompatible hard-filter controls, render clearly labeled factor scores, export the captured result as JSON or Markdown, offer same-snapshot reevaluation.
- [x] Run focused GUI tests and the existing GUI suite; require PASS.

## Task 4: Performance, independent review and full verification

**Files:** Update user documentation and this plan's progress record.

- [x] Time the default sampler on SSQ/DLT K=1/10/100; record diagnostics and cancellation responsiveness.
- [x] Obtain one fresh read-only review of this feature; fix material findings with regression tests.
- [x] Run `.venv/bin/python tests/gui/run_gui_tests.py --all -q --junitxml=/private/tmp/lottery-fusion-full.xml` in the desktop session; save full output to `/private/tmp/lottery-fusion-full.log`.
- [x] Verify history-file hashes unchanged, record final counts/warnings/timings and user-facing usage instructions.

## Execution record

- User explicitly approved implementation of the design. Execute directly in the current checkout to preserve the prior repairs; no additional design/plan confirmation or commits required.
- Pre-flight: feature context feeds the objective; objective/result feed GUI. Interfaces and constants agree with the approved spec.
- Ruling: use one structured JSON export containing the immutable history snapshot, plus Markdown for human review. This makes exported results independently reproducible without depending on mutable on-disk history.
- Ruling: native implementation in this session with one final independent review; no per-task delegation needed.
- Task 1 complete: `tests/unit/test_fusion_features.py` observed missing-module RED, then 23 passed.
- Task 2 complete: sampler tests observed missing-module RED, then both core modules 35 passed in 1.32s.
- Task 3 complete: real-window tests observed missing-controls RED, then 8 fusion GUI tests passed in 5.89s (29 existing tests deselected).
- Snapshot continuity ruling: cross-year issue continuity cannot be proved from issue numbers alone; label it unverified and preserve omission lower bounds, rather than asserting exact omissions.
- Implementation runs in the authorized existing checkout and leaves the combined repair work uncommitted. Final review uses the feature files directly because the baseline includes earlier uncommitted repairs.
- Real-data benchmark exposed DLT native five-digit issues. Added failing regression, normalized YYYYNNN aliases to YYNNN, preserved leading zeroes, and corrected year-boundary detection; core suite then 36 passed.
- Additional GUI boundary checks cover cancellation after success is queued, worker failure followed by retry, empty-history neutral mode and fractional counts. All 40 real-window tests passed in 19.88s.
- Independent review found one Important issue: repeated weight normalization changed canonical floating-point values and broke config-hash round trips. Both JSON restore and automatic-seed replacement regressions reproduced RED. Preserve validated unit-sum vectors and use stable summation for initial normalization.
- Review also independently checked 1,000 incremental replacements at K=100 for both lotteries; full-recompute differences stayed below 3.2e-16. No Critical findings or deferred Minor findings.
- Default-budget real-data timings (seconds): SSQ K=1/10/100 = 2.590/2.704/11.444; DLT = 3.863/3.251/14.207. These measure runtime, not convergence.

- Final review fix verified: custom-weight JSON restoration and seed replacement both RED→GREEN; fusion core 38 passed.
- Final full desktop suite: 439 passed, 0 failed, 0 skipped, 2 existing warnings, 32.05s. Command: `.venv/bin/python tests/gui/run_gui_tests.py --all -q --junitxml=/private/tmp/lottery-fusion-full.xml`. Full output: `/private/tmp/lottery-fusion-full.log`.
- User-facing additions: 38 core fusion tests and 11 real-window fusion tests; total real-window suite 40. No unresolved review findings.
