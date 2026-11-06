"""Real, mapped Tk windows; run with tests/gui/run_gui_tests.py in a desktop session."""
import json
import re
import time
import tkinter as tk
from pathlib import Path

import pytest

pytestmark = pytest.mark.gui


@pytest.fixture
def fast_fusion(monkeypatch):
    from dataclasses import replace
    from src.gui.fusion_controls import FusionControls
    read = FusionControls.read_config
    monkeypatch.setattr(FusionControls, 'read_config', lambda self: replace(
        read(self), steps=160, burn_in=20, chains=2, reference_samples=300))


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
def test_fusion_generate_reevaluate_export_frozen_request(gui, fast_fusion, monkeypatch, lottery):
    from src.core.generators.fusion.result import FusionResult
    root, wrapper, directory, _ = gui
    frame = wrapper.app.generation_tab
    wrapper.app.notebook.select(frame)
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    frame.lottery_type_var.set(lottery)
    frame.num_sets_var.set(3)
    frame.fusion_controls.periods_var.set('5')
    frame.fusion_controls.seed_var.set('123')
    frame.generate_button.invoke()
    assert frame.is_generating
    # Edits made after dispatch must not relabel or rescore the captured request.
    frame.lottery_type_var.set('dlt' if lottery == 'ssq' else 'ssq')
    frame.fusion_controls.seed_var.set('999')
    wait_for(root, lambda: not frame.is_generating)
    result = frame.fusion_result
    assert result.snapshot.lottery_type == lottery
    assert len(result.tickets) == 3
    assert len(result.snapshot.issues) == 5
    assert result.config.seed == 123
    reference=result.to_dict()['random_reference']
    assert reference['count']==3 and reference['samples']==2000
    assert '严格超过约' in frame.result_text.get('1.0','end')
    assert not frame.filter_frame.winfo_ismapped()
    frame.fusion_reevaluate_button.invoke()
    assert '复算一致' in frame.status_label.cget('text')
    frame.fusion_details_var.set(True); frame._render_fusion_result()
    assert '单注解释' in frame.result_text.get('1.0', 'end')
    for suffix in ('json', 'md'):
        path = directory / f'fusion-{lottery}.{suffix}'
        monkeypatch.setattr('tkinter.filedialog.asksaveasfilename', lambda **kwargs: str(path))
        frame.fusion_export_button.invoke()
        assert path.exists()
        if suffix == 'json':
            saved = json.loads(path.read_text())
            assert saved['config']['seed'] == 123
            assert FusionResult.from_dict(saved).reevaluate()['F'] == pytest.approx(result.score)
        else:
            assert result.snapshot.digest in path.read_text()


@pytest.mark.parametrize('field,value', [('temperature_var','nan'), ('temperature_var','0'), ('periods_var','2.5'), ('seed_var','-1')])
def test_fusion_invalid_input_does_not_start_task(gui, monkeypatch, field, value):
    _, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    getattr(frame.fusion_controls,field).set(value)
    errors = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *a, **k: errors.append(a))
    frame.generate_button.invoke()
    assert errors
    assert not frame.is_generating
    assert frame._fusion_thread is None


@pytest.mark.parametrize('close_window', [False, True])
def test_fusion_cancel_and_close_during_real_sampling(gui, monkeypatch, close_window):
    from dataclasses import replace
    from src.gui.fusion_controls import FusionControls
    read = FusionControls.read_config
    monkeypatch.setattr(FusionControls, 'read_config', lambda self: replace(
        read(self), steps=100000, burn_in=20, chains=1, reference_samples=300))
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    wrapper.app.notebook.select(frame)
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    frame.generate_button.invoke()
    wait_for(root, lambda: '融合采样' in frame.status_label.cget('text'))
    worker = frame._fusion_thread
    assert worker.is_alive()
    if close_window:
        wrapper.quit()
    else:
        frame.fusion_cancel_button.invoke()
        wait_for(root, lambda: not frame.is_generating)
        assert '取消' in frame.status_label.cget('text')
        assert frame.fusion_result is None
    worker.join(timeout=3)
    assert not worker.is_alive()


def test_fusion_cancellation_wins_over_queued_success(gui, fast_fusion):
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    frame.generate_button.invoke()
    # Deliberately withhold the event loop until the successful worker has queued delivery.
    frame._fusion_thread.join(timeout=5)
    assert not frame._fusion_thread.is_alive()
    frame.fusion_cancel_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert frame.fusion_result is None
    assert '取消' in frame.status_label.cget('text')


def test_fusion_worker_failure_allows_retry(gui, fast_fusion, monkeypatch):
    from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    errors = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *a, **k: errors.append(a))
    original = MaximumEntropyFusionGenerator.generate_portfolio
    def fail(*args, **kwargs):
        raise ValueError('controlled fusion failure')
    monkeypatch.setattr(MaximumEntropyFusionGenerator, 'generate_portfolio', fail)
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert len(errors) == 1 and 'controlled fusion failure' in errors[0][1]
    assert frame.fusion_result is None
    monkeypatch.setattr(MaximumEntropyFusionGenerator, 'generate_portfolio', original)
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert frame.fusion_result is not None


def test_fusion_empty_history_neutral_mode_and_fractional_count(gui, monkeypatch):
    root, wrapper, directory, _ = gui
    frame = wrapper.app.generation_tab
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    errors = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *a, **k: errors.append(a))
    frame.num_sets_var.set('2.5')
    frame.generate_button.invoke()
    assert errors and not frame.is_generating
    frame.num_sets_var.set(100)
    for weight in frame.fusion_controls.weight_vars:
        weight.set('0')
    (directory / 'ssq_history.json').write_text('{"data": []}')
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert frame.fusion_result.method == 'exact_uniform'
    assert len(frame.fusion_result.tickets) == 100
    assert not frame.fusion_result.snapshot.issues


def wait_for(root, predicate, timeout=10):
    """Run the real event loop, including cross-thread Tk dispatch, with a deadline."""
    deadline = time.monotonic() + timeout
    completed = []

    def poll():
        if predicate():
            completed.append(True)
            root.quit()
        elif time.monotonic() >= deadline:
            root.quit()
        else:
            root.after(10, poll)

    root.after(0, poll)
    root.mainloop()
    assert completed, "Timed out waiting for the GUI operation"


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def button(widget, text):
    return next(w for w in descendants(widget)
                if w.winfo_class() == 'TButton' and w.cget('text') == text)


@pytest.fixture
def gui(tmp_path, monkeypatch):
    # Real file format and separate histories for both supported lotteries.
    for lottery in ('ssq', 'dlt'):
        rows = []
        for i in range(1, 13):
            row = dict(draw_num=f'2026{i:03d}', draw_date=f'2026-01-{i:02d}',
                       sales=100000000, prize_pool=1000000000)
            if lottery == 'ssq':
                row.update(red_numbers=[1, 7, 12, 18, 25, 33], blue_number=i)
            else:
                row.update(front_numbers=[1, 8, 16, 24, 35], back_numbers=[1, i + 1 if i < 12 else 12])
            rows.append(row)
        (tmp_path / f'{lottery}_history.json').write_text(
            json.dumps({'data': rows}), encoding='utf-8')

    def no_network(*args, **kwargs):
        pytest.fail('GUI tests must use local fixtures, not the network')

    monkeypatch.setattr('requests.sessions.Session.request', no_network)
    errors = []
    notices = []
    for name in ('showerror', 'showwarning'):
        monkeypatch.setattr(f'tkinter.messagebox.{name}', lambda *a, **k: errors.append(a))
    monkeypatch.setattr('tkinter.messagebox.showinfo', lambda *a, **k: notices.append(a))
    root = tk.Tk()
    root.report_callback_exception = lambda *args: errors.append(args)
    wrapper = None
    try:
        from src.gui.main_window import LotteryToolsGUI
        wrapper = LotteryToolsGUI(root=root, data_path=tmp_path)
        root.update()
        yield root, wrapper, tmp_path, notices
    finally:
        if wrapper is not None:
            wrapper.quit()
        else:
            root.destroy()
        assert not errors, f'Unexpected GUI errors/dialogs: {errors}'


def test_window_properties_and_current_tabs(gui):
    root, wrapper, _, _ = gui
    assert root.title() == '彩票工具集'
    assert root.winfo_viewable()
    assert root.winfo_width() >= 800 and root.winfo_height() >= 600
    assert root.minsize() == (800, 600)
    notebook = wrapper.app.notebook
    assert [notebook.tab(tab, 'text') for tab in notebook.tabs()] == [
        '双色球', '大乐透', '数据分析', '号码推荐', '号码评价']


def test_switch_all_current_tabs(gui):
    root, wrapper, _, _ = gui
    notebook = wrapper.app.notebook
    for tab in notebook.tabs():
        notebook.select(tab)
        root.update()
        assert notebook.select() == tab
        assert root.nametowidget(tab).winfo_viewable()


def test_history_display_uses_supplied_directory(gui):
    root, wrapper, directory, _ = gui
    app = wrapper.app
    manager = app.analysis_tab.data_manager
    for frame in (app.ssq_tab, app.dlt_tab, app.generation_tab, app.evaluation_tab):
        assert frame.data_manager is manager
    assert manager.data_path == directory
    for lottery in ('ssq', 'dlt'):
        app.analysis_tab.lottery_type_var.set(lottery)
        app.analysis_tab.load_data()
        root.update()
        tree = app.analysis_tab.data_tree
        assert len(tree.get_children()) == 12
        assert tree.set(tree.get_children()[0], 'draw_num') == '2026012'
        evaluator = getattr(app.evaluation_tab, f'{lottery}_evaluator')
        assert Path(evaluator.history_file) == directory / f'{lottery}_history.json'


def test_generate_numbers_with_real_button(gui):
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    wrapper.app.notebook.select(frame)
    frame.strategy_var.set('随机生成')
    frame.num_sets_var.set(2)
    for lottery, label, first_count, first_max, last_count, last_max in (
        ('ssq', '红球', 6, 33, 1, 16), ('dlt', '前区', 5, 35, 2, 12)
    ):
        frame.lottery_type_var.set(lottery)
        frame.generate_button.invoke()
        wait_for(root, lambda: not frame.is_generating)
        text = frame.result_text.get('1.0', 'end')
        lines = [line for line in text.splitlines() if line.startswith('第 ')]
        assert len(lines) == 2, text
        for line in lines:
            assert label in line
            first, last = line.split('|')
            nums = [int(n) for n in re.findall(r'\d+', first.split(':', 2)[-1])]
            tails = [int(n) for n in re.findall(r'\d+', last)]
            assert len(nums) == len(set(nums)) == first_count
            assert all(1 <= n <= first_max for n in nums)
            assert len(tails) == len(set(tails)) == last_count
            assert all(1 <= n <= last_max for n in tails)
        assert str(frame.generate_button['state']) == 'normal'


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
def test_evaluate_and_export_real_report(gui, monkeypatch, worker_guard, lottery):
    root, wrapper, directory, notices = gui
    frame = wrapper.app.evaluation_tab
    wrapper.app.notebook.select(frame)
    frame.lottery_type_var.set(lottery)
    frame._on_lottery_type_changed()
    if lottery == 'ssq':
        frame.ssq_red_entry.insert(0, '01 07 12 18 25 33')
        frame.ssq_blue_entry.insert(0, '06')
    else:
        frame.dlt_front_entry.insert(0, '01 08 16 24 35')
        frame.dlt_back_entry.insert(0, '03 11')
    button(frame, '评价号码').invoke()
    wait_for(root, lambda: frame.status_label.cget('text') == '✓ 评价完成')
    result = frame.current_result['result']
    assert frame.current_result['lottery_type'] == lottery
    assert frame.total_score_label.cget('text') == f"{result['total_score']:.6f}"
    assert -1 <= result['total_score'] <= .25
    assert set(frame.dimension_labels) == {'H','T','C','R','E','D'}
    assert 'K=1' in frame.rating_label.cget('text')
    reference=result['fusion']['random_reference']
    assert f"{reference['exceed_percent']:.1f}%" in frame.random_reference_label.cget('text')
    assert '2,000' in frame.random_reference_note.cget('text')
    root.update_idletasks()
    assert not frame.score_details_frame.winfo_ismapped()
    assert not frame.total_score_label.winfo_ismapped()
    headline=frame.random_reference_label.cget('text')
    frame.score_details_toggle.invoke(); root.update_idletasks()
    assert frame.score_details_frame.winfo_ismapped()
    assert frame.total_score_label.winfo_ismapped()
    assert frame.total_score_label.cget('text')==f"{result['total_score']:.6f}"
    frame.score_details_toggle.invoke(); root.update_idletasks()
    assert not frame.score_details_frame.winfo_ismapped()
    assert frame.random_reference_label.cget('text')==headline
    report_path = directory / 'evaluation.md'
    monkeypatch.setattr('tkinter.filedialog.asksaveasfilename', lambda **k: str(report_path))
    button(frame, '导出报告').invoke()
    report = report_path.read_text(encoding='utf-8')
    assert '# 彩票号码评价报告' in report
    if lottery == 'ssq':
        assert '**彩种**: 双色球' in report
        assert '**红球**: 01 07 12 18 25 33' in report
        assert '**蓝球**: 06' in report
    else:
        assert '**彩种**: 大乐透' in report
        assert '**前区**: 01 08 16 24 35' in report
        assert '**后区**: 03 11' in report
    assert '### 1. 频率分析' in report and '### 4. 历史对比' in report
    assert f"F={result['total_score']:.6f}" in report
    assert '/100' not in report
    from src.core.generators.fusion.result import FusionResult
    json_path = directory / 'evaluation.json'
    monkeypatch.setattr('tkinter.filedialog.asksaveasfilename', lambda **k: str(json_path))
    button(frame, '导出报告').invoke()
    saved = json.loads(json_path.read_text())
    assert saved['random_reference']==result['fusion']['random_reference']
    assert FusionResult.from_dict(saved).reevaluate()['F'] == pytest.approx(result['total_score'])
    assert notices and notices[-1][0] == '成功'


def test_evaluation_missing_reference_stays_unavailable_until_details_open(gui):
    root,wrapper,_,_=gui
    frame=wrapper.app.evaluation_tab
    wrapper.app.notebook.select(frame)
    result=frame.ssq_evaluator.evaluate([1,7,12,18,25,33],6,reference_config=None)
    frame._update_result_display(result); root.update_idletasks()
    assert frame.random_reference_label.cget('text')=='--'
    assert '未计算' in frame.random_reference_caption.cget('text')
    assert not frame.total_score_label.winfo_ismapped()
    frame.score_details_toggle.invoke(); root.update_idletasks()
    assert frame.total_score_label.winfo_ismapped()
    assert frame.total_score_label.cget('text')==f"{result['total_score']:.6f}"
    frame._clear_results(); root.update_idletasks()
    assert not frame.score_details_frame.winfo_ismapped()
    assert frame.random_reference_label.cget('text')=='--'


def test_new_evaluation_clears_previous_contributions_during_progress_and_failure(gui,worker_guard,monkeypatch):
    root,wrapper,_,_=gui
    frame=wrapper.app.evaluation_tab
    wrapper.app.notebook.select(frame)
    frame.ssq_red_entry.insert(0,'01 07 12 18 25 33'); frame.ssq_blue_entry.insert(0,'06')
    button(frame,'评价号码').invoke()
    wait_for(root,lambda:frame.current_result is not None)
    assert any(w['label'].cget('text')!='--' for w in frame.dimension_labels.values())
    Gate,_=worker_guard; gate=Gate()
    def delayed_failure(*args,**kwargs):
        gate.pause()
        raise ValueError('controlled detail failure')
    monkeypatch.setattr(frame.ssq_evaluator,'evaluate',delayed_failure)
    errors=[]
    monkeypatch.setattr('tkinter.messagebox.showerror',lambda *a,**k:errors.append(a))
    frame.ssq_blue_entry.delete(0,'end'); frame.ssq_blue_entry.insert(0,'08')
    button(frame,'评价号码').invoke()
    wait_for(root,gate.started.is_set)
    frame.score_details_toggle.invoke(); root.update_idletasks()
    assert frame.score_details_frame.winfo_ismapped()
    assert frame.total_score_label.cget('text')=='--'
    for widgets in frame.dimension_labels.values():
        assert widgets['label'].cget('text')=='--'
        assert widgets['progress']['value']==0
        assert widgets['icon'].cget('text')==''
    gate.release.set()
    wait_for(root,lambda:bool(errors))
    assert '失败' in frame.rating_label.cget('text')
    assert frame.current_result is None
    assert all(w['label'].cget('text')=='--' for w in frame.dimension_labels.values())


@pytest.mark.parametrize('close_window',[False,True])
def test_cancel_or_close_during_random_reference_phase(gui,monkeypatch,close_window):
    from dataclasses import replace
    from src.gui.fusion_controls import FusionControls
    from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator
    from src.core.generators.fusion.percentile import RandomReferenceConfig
    read=FusionControls.read_config
    monkeypatch.setattr(FusionControls,'read_config',lambda self:replace(read(self),steps=60,burn_in=10,chains=1,reference_samples=300))
    generate=MaximumEntropyFusionGenerator.generate_portfolio
    def prolonged_reference(self,*args,**kwargs):
        kwargs['reference_config']=RandomReferenceConfig(samples=100000,seed=32001)
        return generate(self,*args,**kwargs)
    monkeypatch.setattr(MaximumEntropyFusionGenerator,'generate_portfolio',prolonged_reference)
    root,wrapper,_,_=gui
    frame=wrapper.app.generation_tab
    frame.strategy_var.set('融合推荐'); frame._on_strategy_change()
    frame.generate_button.invoke()
    wait_for(root,lambda:'随机参照' in frame.status_label.cget('text'))
    thread=frame._fusion_thread
    assert thread.is_alive()
    if close_window:
        wrapper.quit()
    else:
        frame.fusion_cancel_button.invoke()
        wait_for(root,lambda:not frame.is_generating)
        assert frame.fusion_result is None
    thread.join(timeout=3)
    assert not thread.is_alive()


def test_evaluation_profile_and_lottery_frozen_during_worker(gui, worker_guard, monkeypatch):
    root,wrapper,_,_=gui
    frame=wrapper.app.evaluation_tab
    Gate,_=worker_guard
    gate=Gate()
    original=frame.ssq_evaluator.evaluate
    def delayed(*args,**kwargs):
        gate.pause()
        return original(*args,**kwargs)
    monkeypatch.setattr(frame.ssq_evaluator,'evaluate',delayed)
    frame.lottery_type_var.set('ssq'); frame._on_lottery_type_changed()
    frame.ssq_red_entry.insert(0,'01 07 12 18 25 33'); frame.ssq_blue_entry.insert(0,'06')
    frame.analysis_periods_var.set('5')
    frame.evaluation_weight_vars[0].set('1')
    for var in frame.evaluation_weight_vars[1:]: var.set('0')
    button(frame,'评价号码').invoke()
    wait_for(root,gate.started.is_set)
    frame.lottery_type_var.set('dlt'); frame._on_lottery_type_changed()
    frame.evaluation_weight_vars[0].set('0')
    frame.evaluation_weight_vars[1].set('1')
    gate.release.set()
    wait_for(root,lambda: frame.current_result is not None)
    result=frame.current_result['result']
    assert frame.current_result['lottery_type']=='ssq'
    assert result['fusion']['config']['weights']==(1.,0.,0.,0.,0.,0.)
    assert result['total_score']==pytest.approx(result['scores']['H'])
    assert len(result['fusion']['snapshot']['issues'])==5
    assert '【红球频率】' in frame.freq_missing_text.get('1.0','end')


def test_invalid_evaluation_weights_report_error_without_starting(gui,monkeypatch):
    _,wrapper,_,_=gui
    frame=wrapper.app.evaluation_tab
    frame.ssq_red_entry.insert(0,'01 07 12 18 25 33'); frame.ssq_blue_entry.insert(0,'06')
    frame.evaluation_weight_vars[0].set('nan')
    errors=[]
    monkeypatch.setattr('tkinter.messagebox.showerror',lambda *a,**k:errors.append(a))
    monkeypatch.setattr('tkinter.messagebox.showwarning',lambda *a,**k:errors.append(a))
    button(frame,'评价号码').invoke()
    assert errors and frame.current_result is None


@pytest.mark.parametrize('older_fails',[False,True])
def test_latest_evaluation_request_wins_over_late_delivery(gui,worker_guard,monkeypatch,older_fails):
    root,wrapper,_,_=gui
    frame=wrapper.app.evaluation_tab
    Gate,_=worker_guard; gate=Gate()
    original=frame.ssq_evaluator.evaluate
    def delayed(*args,**kwargs):
        if kwargs['snapshot'].requested_periods==5:
            gate.pause()
            if older_fails:
                raise ValueError('obsolete request failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(frame.ssq_evaluator,'evaluate',delayed)
    frame.ssq_red_entry.insert(0,'01 07 12 18 25 33'); frame.ssq_blue_entry.insert(0,'06')
    frame.analysis_periods_var.set('5'); button(frame,'评价号码').invoke()
    wait_for(root,gate.started.is_set)
    frame.analysis_periods_var.set('3'); button(frame,'评价号码').invoke()
    wait_for(root,lambda: frame.current_result is not None)
    current=frame.current_result
    assert current['result']['fusion']['snapshot']['requested_periods']==3
    gate.release.set()
    wait_for(root,lambda: not gate.thread.is_alive())
    root.after(150,root.quit); root.mainloop()
    assert frame.current_result is current


def test_destroy_cancels_polling_and_has_no_extra_windows(gui):
    root, wrapper, _, _ = gui
    from matplotlib import pyplot as plt
    assert plt.get_fignums() == [], 'Embedded charts must not open a pyplot Tk window'
    wrapper.app.notebook.destroy()
    callbacks = [str(root.tk.call('after', 'info', ident))
                 for ident in root.tk.call('after', 'info')]
    assert not any('_check_generation_queue' in c or '_check_update_queue' in c or '_check_evaluation_queue' in c for c in callbacks)
    # Keep the interpreter alive past a polling interval to expose stale callbacks.
    root.after(200, root.quit)
    root.mainloop()
    wrapper.quit()
    wrapper.quit()  # Window-manager close and explicit shutdown may both fire.


@pytest.fixture
def worker_guard(monkeypatch):
    """Observe forbidden Tk calls, and always release/join controlled real workers."""
    import threading
    owner = threading.get_ident()
    violations = []
    gates = []
    original_after = tk.Misc.after

    def observe_get(original):
        def get(variable):
            if threading.get_ident() != owner:
                violations.append('worker read a Tk variable')
            return original(variable)
        return get

    def after(widget, *args, **kwargs):
        if threading.get_ident() != owner:
            violations.append('worker called Tk.after')
        return original_after(widget, *args, **kwargs)

    for variable_type in (tk.Variable, tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar):
        monkeypatch.setattr(variable_type, 'get', observe_get(variable_type.get))
    monkeypatch.setattr(tk.Misc, 'after', after)
    monkeypatch.setattr(threading, 'excepthook', lambda event: violations.append(str(event.exc_value)))

    class Gate:
        def __init__(self):
            self.started = threading.Event()
            self.release = threading.Event()
            self.thread = None
            gates.append(self)

        def pause(self):
            self.thread = threading.current_thread()
            self.started.set()
            if not self.release.wait(10):
                raise TimeoutError('Test did not release worker')

    yield Gate, violations
    for gate in gates:
        gate.release.set()
        if gate.thread is not None:
            gate.thread.join(5)
            assert not gate.thread.is_alive(), 'Worker did not terminate'
    assert not violations, f'Unsafe worker behavior: {violations}'


def close_during_work(root, wrapper, gate, notices):
    wait_for(root, gate.started.is_set)
    assert gate.thread.is_alive() and not gate.release.is_set()
    started = time.monotonic()
    # Use the actual window-manager close callback while the worker is blocked.
    root.tk.call(root.protocol('WM_DELETE_WINDOW'))
    assert time.monotonic() - started < 1.5, 'Window close blocked on background work'
    with pytest.raises(tk.TclError, match='application has been destroyed'):
        root.winfo_exists()
    assert gate.thread.is_alive(), 'Worker was released before window destruction'
    gate.release.set()
    gate.thread.join(5)
    assert not gate.thread.is_alive(), 'Worker stayed blocked after the root closed'
    assert not notices, 'Closed window displayed a late completion dialog'
    wrapper.quit()


@pytest.mark.parametrize('strategy', ['统计优选', '去热门-适中', '最高评分（整注）'])
@pytest.mark.parametrize('outcome', ['success', 'error'])
def test_close_during_background_generation(gui, worker_guard, monkeypatch, strategy, outcome, capsys):
    import threading
    root, wrapper, _, notices = gui
    Gate, _ = worker_guard
    gate = Gate()
    frame = wrapper.app.generation_tab
    wrapper.app.notebook.select(frame)
    frame.strategy_var.set(strategy)
    frame.num_sets_var.set(1)
    run = threading.Thread.run

    def controlled_run(thread):
        if getattr(thread._target, '__self__', None) is frame:
            gate.pause()  # Hold before the worker can read any Tk settings.
        return run(thread)

    monkeypatch.setattr(threading.Thread, 'run', controlled_run)
    from src.core.generators import factory, smart_generator
    create = factory.create_generator
    smart_class = smart_generator.SmartNumberGenerator

    def local_create(kind, lottery):
        if outcome == 'error':
            raise ValueError('controlled generation failure')
        generator = create(kind, lottery)
        generator.data_manager = frame.data_manager
        return generator

    class LocalSmartGenerator(smart_class):
        def __init__(self, lottery):
            if outcome == 'error':
                raise ValueError('controlled generation failure')
            super().__init__(lottery)
            self.data_manager = frame.data_manager

    def local_search(**options):
        if outcome == 'error':
            raise ValueError('controlled search failure')
        return [dict(red_numbers=[1, 7, 12, 18, 25, 33], blue_number=6, total_score=70.0)]

    monkeypatch.setattr(factory, 'create_generator', local_create)
    monkeypatch.setattr(smart_generator, 'SmartNumberGenerator', LocalSmartGenerator)
    # Top-score search is expensive; lifecycle tests replace only that compute boundary.
    monkeypatch.setattr('scripts.find_top_ssq.find_top_ssq', local_search)
    frame.generate_button.invoke()
    assert frame.is_generating
    close_during_work(root, wrapper, gate, notices)
    assert 'Traceback' not in capsys.readouterr().err


@pytest.mark.parametrize('outcome', ['success', 'error'])
def test_close_during_background_update(gui, worker_guard, monkeypatch, outcome):
    root, wrapper, directory, notices = gui
    Gate, _ = worker_guard
    gate = Gate()
    frame = wrapper.app.analysis_tab
    wrapper.app.notebook.select(frame)
    record = dict(draw_num='2026013', draw_date='2026-01-13', red_numbers=[2, 8, 13, 19, 26, 32],
                  blue_number=13, sales=100000000, prize_pool=1000000000)

    def delayed_fetch(lottery):
        assert lottery == 'ssq'
        gate.pause()
        return [record] if outcome == 'success' else None

    # Keep the real update/merge/write path; replace only the online-fetch boundary.
    monkeypatch.setattr(frame.data_manager, '_fetch_online_data_as_list', delayed_fetch)
    frame.update_button.invoke()
    assert frame.is_updating
    close_during_work(root, wrapper, gate, notices)
    saved = json.loads((directory / 'ssq_history.json').read_text())['data']
    assert len(saved) == (13 if outcome == 'success' else 12)
    assert any(row['draw_num'] == '2026013' for row in saved) == (outcome == 'success')


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
@pytest.mark.parametrize('outcome', ['success', 'error'])
def test_close_during_background_evaluation(gui, worker_guard, monkeypatch, lottery, outcome):
    root, wrapper, _, notices = gui
    Gate, _ = worker_guard
    gate = Gate()
    frame = wrapper.app.evaluation_tab
    wrapper.app.notebook.select(frame)
    frame.lottery_type_var.set(lottery)
    frame._on_lottery_type_changed()
    if lottery == 'ssq':
        frame.ssq_red_entry.insert(0, '01 07 12 18 25 33')
        frame.ssq_blue_entry.insert(0, '06')
    else:
        frame.dlt_front_entry.insert(0, '01 08 16 24 35')
        frame.dlt_back_entry.insert(0, '03 11')
    evaluator = getattr(frame, f'{lottery}_evaluator')
    evaluate = evaluator.evaluate

    def delayed_evaluate(*args, **kwargs):
        gate.pause()
        if outcome == 'error':
            raise ValueError('controlled evaluation failure')
        return evaluate(*args, **kwargs)

    monkeypatch.setattr(evaluator, 'evaluate', delayed_evaluate)
    button(frame, '评价号码').invoke()
    close_during_work(root, wrapper, gate, notices)
    assert frame.current_result is None, 'Late worker result mutated a destroyed page'


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
def test_evaluation_failure_is_displayed_on_live_window(gui, monkeypatch, worker_guard, lottery):
    root, wrapper, _, _ = gui
    frame = wrapper.app.evaluation_tab
    dialogs = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *args: dialogs.append(args))

    def fail(*args, **kwargs):
        raise ValueError('controlled live evaluation failure')

    monkeypatch.setattr(getattr(frame, f'{lottery}_evaluator'), 'evaluate', fail)
    frame.lottery_type_var.set(lottery)
    frame._on_lottery_type_changed()
    if lottery == 'ssq':
        frame.ssq_red_entry.insert(0, '01 07 12 18 25 33')
        frame.ssq_blue_entry.insert(0, '06')
    else:
        frame.dlt_front_entry.insert(0, '01 08 16 24 35')
        frame.dlt_back_entry.insert(0, '03 11')
    button(frame, '评价号码').invoke()
    wait_for(root, lambda: bool(dialogs), timeout=3)
    assert frame.current_result is None
    assert 'controlled live evaluation failure' in frame.status_label.cget('text')
    assert len(dialogs) == 1 and 'controlled live evaluation failure' in dialogs[0][1]


@pytest.mark.parametrize('strategy', ['统计优选', '去热门-适中', '最高评分（整注）'])
def test_generation_failure_restores_live_controls(gui, monkeypatch, worker_guard, strategy):
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    dialogs = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *args: dialogs.append(args))

    def fail(*args, **kwargs):
        raise ValueError('controlled live generation failure')

    monkeypatch.setattr('src.core.generators.factory.create_generator', fail)
    monkeypatch.setattr('src.core.generators.smart_generator.SmartNumberGenerator', fail)
    monkeypatch.setattr('scripts.find_top_ssq.find_top_ssq', fail)
    frame.strategy_var.set(strategy)
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert len(dialogs) == 1 and 'controlled live generation failure' in dialogs[0][1]
    assert str(frame.generate_button['state']) == 'normal'
    # Error delivery must leave the poller and normal generation usable.
    frame.strategy_var.set('随机生成')
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert frame.result_text.get('1.0', 'end').count(' 注: 红球:') == 2
    assert len(dialogs) == 1


@pytest.mark.parametrize('strategy,variable,invalid,valid', [
    ('统计优选', 'filter_periods_var', '', 100),
    ('去热门-适中', 'max_overlap_var', 'bad', 4),
    ('最高评分（整注）', 'periods_var', '', 100),
    ('最高评分（整注）', 'pool_size_var', 'bad', 18),
    ('随机生成', 'num_sets_var', '', 2),
])
def test_invalid_generation_setting_can_be_corrected(gui, monkeypatch, strategy, variable, invalid, valid):
    root, wrapper, _, _ = gui
    frame = wrapper.app.generation_tab
    wrapper.app.notebook.select(frame)
    frame.strategy_var.set(strategy)
    frame.strategy_combo.event_generate('<<ComboboxSelected>>')
    setting = getattr(frame, variable)
    spinbox = next(w for w in descendants(frame)
                   if w.winfo_class() == 'TSpinbox' and str(w.cget('textvariable')) == str(setting))
    dialogs = []
    monkeypatch.setattr('tkinter.messagebox.showerror', lambda *args: dialogs.append(args))
    spinbox.delete(0, tk.END)
    if invalid:
        spinbox.insert(0, invalid)
    frame.generate_button.invoke()
    root.update()
    assert len(dialogs) == 1, 'Invalid settings must produce one visible error'
    assert not frame.is_generating
    assert str(frame.generate_button['state']) == 'normal'
    setting.set(valid)
    frame.strategy_var.set('随机生成')
    frame.generate_button.invoke()
    wait_for(root, lambda: not frame.is_generating)
    assert frame.result_text.get('1.0', 'end').count(' 注: 红球:') == 2
    assert len(dialogs) == 1
