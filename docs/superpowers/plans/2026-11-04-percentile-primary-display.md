# Percentile Primary Display Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with focused GUI interaction tests and final read-only review.

**Goal:** Make the random-reference percentage the main evaluation display; retain native F and signed contributions in collapsed details.

**Architecture:** Change presentation only. The main card shows the percentage, its actual lottery/K and reference sample/tie/interval context. Existing F/factor widgets move into a details frame. Recommendation summaries and full reports follow the same information order.

**Tech Stack:** Existing Tk and Markdown rendering.

**Spec:** User explicitly requests percentile-primary display with F/contributions in details; all scoring/reference computation remains as defined in the existing fusion design.

## Global Constraints

- No score, reference, RNG, sorting or JSON schema changes.
- Default details collapsed; expanding shows original F and all six factors; folding retains the same main percentage.
- Reset/new request hides prior details and clears prior percentile. Missing reference displays unavailable, never substitutes raw F as a percentage.
- Markdown brief omits F; full report keeps F/contributions in a details section after the main percentile.

## Review Focus

- Missing-reference results and reset/in-progress/error states cannot display an old percentage.
- Opening details must reveal the stored F, not trigger scoring or sampling.
- A later result updates both visible summary and hidden detail values.

## Tasks

- [x] Extend mapped-window tests for collapsed default, expansion/folding, reset and missing-reference behavior; add brief/full report regression. Observe RED.
- [x] Reorganize `src/gui/fusion_evaluation.py`; adapt reset/progress labels in evaluation frame; reorder `FusionResult.to_markdown` and update recommendation details toggle.
- [x] Run focused tests and whole real-window suite; inspect one fresh read-only review and resolve material issues.
- [x] Run complete desktop suite and document the final display and test results.

## Execution record

- User has specified the presentation hierarchy; implement directly without another confirmation or changes to mathematical logic.
- Focused interaction checks observed RED on missing collapsed-details controls, then 5 real-window cases passed (both-lottery expansion/export, recommendation summaries, missing-reference reset). Brief/full report regression also observed RED, then 38 reference/sampler tests passed.
- Primary card shows the approximate percentage with actual lottery/K and sample/tie/interval context. Raw F and six factors live in one collapsed details frame; no scoring/reference/serialization code changed.
- Whole desktop GUI run before review: 47 passed in 28.66s.
- Independent review found one Important lifecycle issue: expanding details during a new/failed request exposed old factor values. Reproduced with a controlled real worker, then centralized score-widget reset for new requests and clearing, and marked failed detail state explicitly. Regression checks pending and failed states; no deferred review findings.

- Review fix RED→GREEN: previous contributions are cleared during a new pending/failed request; 4 focused GUI tests passed.
- Final full desktop suite: 495 passed, 0 failures/errors/skips, 2 existing warnings, 52.02s. Includes 48 real-window tests. Artifacts: `/private/tmp/lottery-percentile-display-full.log` and `/private/tmp/lottery-percentile-display-full.xml`.
