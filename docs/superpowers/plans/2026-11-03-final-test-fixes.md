# Remaining Test Failures and DLT Rules

> **For agentic workers:** Use executing-plans and test-driven-development.

**Goal:** Resolve the five remaining failures, verify official DLT rules, and rerun the default suite.
**Spec:** User-approved third batch in this chat, 2026-11-03.

## Scope and checks

- [x] Restore usable preprocessor initialization/configuration and the declared numeric/categorical preprocessing path; preserve row/column alignment and input data.
- [x] Check missing values, empty columns, invalid selections, reports and config persistence using real frames.
- [x] Correct the numeric-cleaning assertion to check actual amounts and pandas numeric types.
- [x] Feed prepared numerical features to the numerical ensemble test; retain meaningful validation of ensemble and model interpretation.
- [x] Verify the official 26014 transition, seven award levels, the 800-million threshold, and additional-bet rules before changing DLT logic/tests.
- [x] Cover rule boundaries, all winning match patterns, additional bets and grouped bets; clearly distinguish floating awards from known fixed amounts.
- [x] Run scoped tests, the full default suite and independent review. Preserve previous changes and real history files; do not launch real GUI tests.

## Official evidence

- Announcement: https://www.fjtc.com.cn/2026-01/16/content_32117402.htm
- Rule PDF: https://file.fjtc.com.cn/Attachment/2026-01/16/8f534265-b571-4e98-844d-061b31308be1.pdf
- Rule text, article 16: additional bets participate only in floating awards, at 80% of the corresponding basic award.


## Verification results and decisions

- Original five failures reproduced: 5 failed, 24 passed in the initial scoped run.
- Final scoped suite: 149 passed. Final project default suite: 357 passed, 0 failures, 0 collection errors, 6 real-window tests deselected, 3 warnings (environment CPU detection, invalid-date fixture parsing, nonfinite numeric-boundary fixture).
- First-batch 65 regression cases all passed in the final full run; all preceding feature/generator cases also remained green.
- Independent reviewer reproduced and reported nullable integer configuration validation and imputed-zero pool provenance bugs. Added failing regressions and fixed both; independent follow-up ran 119 related cases successfully and reported no new important issue.
- Model rows retain index/column alignment and duplicates; numeric missing values use median (zero for entirely missing columns), categorical missing values use the mode (empty category for entirely missing columns), with integer ordinal output. Named configuration loads/saves and applies validation/transforms.
- DLT supports the 19019/26014 rule transition. Fixed awards have no additional-bet supplement. Floating amounts require official basic-per-ticket values; otherwise None is explicit. Older rules before 19019 are not silently inferred.
- Rule-aware GUI callback uses the matching draw's official amount and the immediately preceding issue's positive pool balance. Missing, imputed-zero or mismatched data stays unknown, including conservatively unresolved year-boundary context.
- Ordinary fixed-prize tables are implemented; special awards/risk-control adjustments and final payment remain governed by the official draw announcement.
- DLTFrame.check_prize was tested with lightweight controls in a subprocess without a Tk root window: high-pool third prize remained 6666 under an additional bet.
- User history files were not edited. Prior user/first/second batch changes were preserved. Changes remain uncommitted.
- Logs: /private/tmp/lottery-batch3-focused.log and /private/tmp/lottery-batch3-full.log. Official rule details: docs/DLT_RULES_VERIFICATION.md.
