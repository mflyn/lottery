# Random Reference Percentile Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans, test-driven-development, and one final fresh read-only review.

**Goal:** Retain F exactly and add an intuitive comparison against uniformly random legal portfolios of the same cardinality.

**Architecture:** A separate reference service samples Q0 with an independent fixed seed, evaluates existing F, caches immutable reference scores, and returns a portable strict-exceedance summary. Evaluation, recommendation and top-search results attach this summary only after F/ranking is computed. Rendering and export consume saved summaries, with no sampling on the Tk thread.

**Spec:** Existing maximum-entropy fusion design plus the user's explicit request for a random-reference percentage alongside F.

## Global Constraints

- F, weights, sampler acceptance and selected tickets do not change.
- Same lottery, snapshot, scoring profile and K; within a reference portfolio complete tickets are distinct, across reference samples repeats are allowed.
- Default N=2000, seed=20261104, absolute tie tolerance 1e-12. Strict exceedance = count(F_reference < F_target - tolerance)/N; ties reported separately.
- Show approximate percentage, sample count and a 95% Wilson interval for the strict-exceedance rate. All-equal results show 0% exceeded and 100% tied.
- Dedicated RNG; reference generation never consumes target-generation random state. Cache identity excludes temperature, generation seed, chain budget and other parameters that do not change F.
- Capture and export reference version/settings, score distribution hash, target F, lower/tied/higher counts, K and source hashes.
- Background, cancellable comparison; no percentile recomputation when rendering/exporting saved results. Old exports without a reference remain readable.

## Review Focus

- Ties and neutral profiles must not be described as strictly exceeded.
- K=1 and K>1 use different uniform reference spaces; no comparison with biased/generated candidates.
- F and selected tickets remain identical with comparison enabled or disabled.
- Cached samples cannot leak across changed histories, weights, shape reference or K; stochastic generation settings do not unnecessarily fragment the cache.
- Cancellation/window-close and portable metadata validation must cover the additional computation phase.

## Task 1: Reference statistics and portable result

Files: new `src/core/generators/fusion/percentile.py`, `uniform.py`; modify `result.py` and uniform imports in sampler; new `tests/unit/test_random_reference.py`.

- [x] Write known-count/tie/CI, deterministic reference, profile/cache isolation, K legality, cancellation and portable metadata tests; observe RED.
- [x] Implement independent reference settings, bounded immutable score cache, Wilson intervals and strict-count summaries using the existing objective.
- [x] Extract unchanged uniform sampling helpers for reuse; add optional validated reference summaries to FusionResult/JSON/Markdown, retaining old import compatibility.
- [x] Run focused tests and require PASS.

## Task 2: Background integration and display

Files: modify sampler, evaluator adapter, candidate search and evaluation/recommendation GUI; extend core/GUI tests.

- [x] Add tests proving unchanged F/tickets, same-K reference, saved percentile display/export and reference-stage cancellation; observe RED.
- [x] Attach references at completed result boundaries, never in per-candidate scoring. Keep scoring signatures separate from generation/calibration settings.
- [x] Render percentile beside F and include sample size/ties/interval in evaluation and recommendation reports. Reference progress travels through existing queues.
- [x] Run relevant core and real-window tests; require PASS.

## Task 3: Performance, review and complete suite

- [x] Benchmark cold K=1/10/100 reference builds and warm-cache reuse; verify cancellation responsiveness.
- [x] Obtain one independent read-only review; fix material findings with meaningful regression coverage.
- [x] Run the entire desktop suite, verify data hashes and document the sampling definition and results.

## Execution record

- User requested an additive random-reference view and explicitly preserved F; implement directly without changing the mathematical preference model.
- Strict-exceedance display is chosen to match “超过多少比例”; tied values are shown separately rather than given half credit.
- Task 1: 16 initial reference tests RED→GREEN; result/integration tests also observed missing reference_config failures, then 20 passed. Immutable bytes-backed cache prevents re-enabling array writes.
- Task 2: F/tickets/chain identity checks, old-export compatibility, context validation and NumPy integer JSON regression pass. Focused desktop integration: 6 passed including both-lottery display/export and cancellation/close during actual reference computation.
- Performance with 2000 samples, real history: SSQ cold K=1/10/100 0.315/1.903/19.433s; DLT 0.407/2.276/21.580s. Warm cache under 1ms. Target generation streams and scoring parameters are unchanged.
- Focused final core run: 86 passed in 8.53s, including unchanged F/tickets/chains, old JSON compatibility, same-K uniform reference, tie handling, immutable caches, profile/history isolation, portable counts, numeric validation and reference-stage cancellation.
- Independent read-only review found no Critical/Important/Minor defects. Duplicate simultaneous cold-cache builds are permitted and deterministic; imported digests record provenance rather than cryptographic authenticity. No deferred feature fixes.

- Final complete desktop suite: 493 passed, 0 failures/errors/skips, 2 existing warnings, 37.42s. Includes 86 fusion/reference/evaluation/search core tests and 46 real-window tests.
- Final artifacts: `/private/tmp/lottery-reference-full.log`, `/private/tmp/lottery-reference-full.xml`; benchmark `/private/tmp/lottery-reference-benchmark.json`. History hashes verified after the run.
