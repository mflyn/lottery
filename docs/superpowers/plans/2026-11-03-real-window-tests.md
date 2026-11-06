# Real Tk Window Tests

> **For agentic workers:** Use systematic-debugging, test-driven-development and executing-plans.

**Goal:** Diagnose native Tk startup aborts, repair six obsolete GUI tests, and verify actual windows plus the full suite.
**Spec:** User's GUI-test repair request in this chat, 2026-11-03.

## Evidence and approach

- The exact minimal Tk create/update/destroy program aborts with SIGABRT in the sandbox and passes under desktop permissions (Tk 8.6.14 aqua, Python 3.13.0).
- Use a child-process Tk preflight in the GUI runner so lack of desktop access cannot abort the parent pytest process.
- Keep GUI tests explicitly selected and run them in the verified desktop context; do not replace actual Tk objects with mocks.
- Current main-window contract: five tabs (双色球、大乐透、数据分析、号码推荐、号码评价), notebook owned by LotteryApp, no application menu bar.
- Use temporary JSON histories and prevent network calls. Respect the GUI's data_path argument through actual managers/evaluators.
- Own/cancel Tk polling callbacks and close embedded chart resources on destruction.
- Embed Matplotlib Figure directly in Tk rather than creating a separate pyplot-managed window.

## Tasks

- [x] Reproduce environment abort and obsolete-test failures with bounded diagnostics.
- [x] Replace the six tests with mapped-window properties, actual tab navigation, fixture data display, real number-generation control flow, evaluation/export, and lifecycle checks.
- [x] Add failing assertions for custom data paths and shutdown cleanup; then repair application ownership/lifecycle.
- [x] Add a safe desktop preflight runner, validate its restricted-environment behavior, and document execution.
- [x] Run all six real window tests under desktop permissions, default tests, and the combined suite.
- [x] Perform an independent scoped review and preserve all prior work/history files.


## Verification evidence

- Before the fix, updated tests failed on non-shared data managers and a pyplot-managed Tk window (`/private/tmp/lottery-gui-red.log`, `/private/tmp/lottery-gui-lifecycle-red.log`).
- Restricted runner: returns 2 and reports `Tk desktop preflight failed (SIGABRT)` without starting pytest (`/private/tmp/lottery-gui-restricted-runner.log`). The desktop preflight passes with Tk 8.6.14 aqua.
- Real window suite: **6 passed**, 4.97 s (`/private/tmp/lottery-gui-final.log`, matching JUnit XML).
- Default suite: **361 passed, 6 deselected, 3 warnings**, 18.06 s (`/private/tmp/lottery-gui-default.log`). Four additional non-window tests exercise runner abort, timeout, suite selection, and pytest exit-code preservation.
- Combined desktop suite: **367 passed, 2 warnings**, 17.83 s (`/private/tmp/lottery-gui-combined.log`, matching JUnit XML). No failures/errors/skips, no stale Tcl callback errors in these logs.
- Remaining combined-suite warnings: invalid-date parsing fixture and NumPy infinity-boundary fixture. Default sandbox run additionally warns about physical CPU core detection.
- Historical data file diffs retain their pre-task counts; all GUI fixtures and exported test reports use temporary directories.

- Independent scoped review found no blocking issues. Strengthened generated-number count/uniqueness assertions, then reran the combined suite successfully. Lifecycle coverage is idle shutdown; active-worker shutdown is outside this verification. Full evaluation/export is verified for SSQ.
