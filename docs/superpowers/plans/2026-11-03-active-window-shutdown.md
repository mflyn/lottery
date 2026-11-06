# Active GUI Task Shutdown and DLT Evaluation

**Goal:** Verify closing a real window while generation, update, and evaluation workers are active; repair demonstrated errors; cover full DLT evaluation/export; rerun all tests.
**Spec:** User request in this chat, 2026-11-03. Preserve prior work and leave changes in current checkout.

## Approach and file responsibilities

- `tests/gui/test_main_window.py`: real Tk event loop and buttons. Thread Events hold slow work at a known boundary; close via WM_DELETE_WINDOW; release workers and verify timely termination, no post-close Tk calls, dialogs, thread failures or stale callbacks. Exercise success and failure completions. Use local histories and real evaluator/generator computation where practical; replace only remote fetch/search boundary for deterministic timing.
- `src/gui/generation_frame.py`: if tests demonstrate worker reads of Tk settings, snapshot settings on main thread and pass plain values. Retain queue-based completion.
- `src/gui/frames/number_evaluation_frame.py`: if tests demonstrate post-close Tk callbacks, use worker result queue consumed only by live UI; close cancels polling and discards late results. Test ordinary success/error delivery too.
- `src/gui/main_window.py`: update worker already uses queue; change only if lifecycle tests demonstrate a defect.
- `docs/environment_setup.md`: update verified test coverage and counts after completion.

## Tasks

- [x] Add active-close regressions and DLT full evaluation/export. Run focused tests before source edits; expect unsafe generation Tk reads and evaluation callbacks to fail.
- [x] Fix demonstrated worker/UI ownership defects and verify active success/error completion plus open-window behavior.
- [x] Run real GUI tests, default pytest, and complete desktop suite via preflight runner. Expect all passing, inspect thread/Tcl stderr and JUnit.
- [x] Obtain scoped independent code review, address blocking findings, and verify final source state and historical-data hashes.

## Verification commands

- Desktop: `.venv/bin/python tests/gui/run_gui_tests.py -q --tb=short` (all real GUI tests).
- Default: `.venv/bin/python -m pytest -q -p no:cacheprovider` (non-window tests).
- Desktop complete: `.venv/bin/python tests/gui/run_gui_tests.py --all -q --tb=short` (all tests including GUI).
- Expected: zero failures/errors/skips in complete run; existing invalid-date and infinity-boundary warnings may remain.

## Review focus

Worker callbacks that still read Tk variables, error closures, races between close and completion, late result state mutation/dialogs, stale queue polling, and tests that release a worker before actually closing the root. No forced thread termination or blocking joins in UI shutdown. Pending computations/I/O may finish in background and must not access destroyed Tk resources.


## Evidence and review ledger

- RED: `/private/tmp/lottery-active-red.log` confirms worker Tk reads, post-close evaluation `after()` calls and late `current_result` mutation. Existing queue-based update passes success/failure close tests. Both real SSQ/DLT evaluation/export flows pass.
- Expanded RED: `/private/tmp/lottery-active-expanded-red.log` confirms all three generation worker paths and the live-window evaluation error closure (`e` cleared before Tk callback).
- Fixed: generation reads settings only in main thread, passes plain snapshots; evaluation uses pure-worker result queue, main-thread delivery, close Event and canceled poller. Update implementation unchanged.
- Independent scoped review found one important new regression: moving editable Spinbox parsing to main thread lost the worker's error handler. RED `/private/tmp/lottery-active-input-red.log`: five editable fields cause callback exceptions and no visible error. Fixed by catching parse errors before clearing results or disabling controls; tests correct values and generate again.
- GUI after review fix: **29 passed**, 15.37 s (`/private/tmp/lottery-active-gui.log` and matching XML).
- No deferred review findings. Review scope excludes previously existing concurrent repeated evaluations/switching lottery during computation; this task verifies active shutdown and ordinary evaluation/export.


## Final verification

- Desktop GUI: **29 passed**, 15.37 s; `/private/tmp/lottery-active-gui.log` and `.xml`.
- Default suite: **361 passed, 29 deselected, 3 warnings**, 19.52 s; `/private/tmp/lottery-active-default.log` and `.xml`.
- Complete desktop suite after all code fixes: **390 passed, 2 warnings**, 24.61 s; `/private/tmp/lottery-active-full.log` and `.xml`. JUnit confirms zero failures/errors/skips, 29 GUI cases including 12 active-close cases.
- Complete warnings remain the preexisting invalid-date fixture and NumPy infinity-boundary fixture. The sandbox default run additionally warns about physical CPU core detection.
- Original `data/ssq_history.json` and `data/dlt_history.json` SHA-1 hashes match the pre-task snapshot. All update/merge and exported-report test side effects stayed inside temporary directories.
- Final: fixed editable Spinbox parsing regression — five invalid-input/retry cases RED to GREEN, complete suite 390/390. No deferred review findings or required work remains.
