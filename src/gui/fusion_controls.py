"""Fusion-only controls and lifecycle; workers communicate through plain queues."""
import json
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.core.generators.fusion.config import FusionConfig, FusionCancelled
from src.core.generators.fusion.history import FusionHistorySnapshot
from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator


class FusionControls(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='融合参数')
        self.periods_var = tk.StringVar(value='180')
        self.temperature_var = tk.StringVar(value='0.15')
        self.seed_var = tk.StringVar(value='')
        for i,(label,var) in enumerate([('历史期数',self.periods_var),('随机性 τ',self.temperature_var),('种子（可留空）',self.seed_var)]):
            ttk.Label(self,text=label).grid(row=0,column=i*2,padx=4,pady=4)
            ttk.Entry(self,textvariable=var,width=12).grid(row=0,column=i*2+1,padx=4,pady=4)
        ttk.Label(self,text='历史新颖度作为软偏好；τ 越大越接近均匀随机。',foreground='gray').grid(row=1,column=0,columnspan=6,sticky='w',padx=4)
        self.advanced_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self,text='高级权重',variable=self.advanced_var,command=self._toggle_advanced).grid(row=2,column=0,columnspan=6,sticky='w')
        self.advanced = ttk.Frame(self)
        self.advanced.grid(row=3,column=0,columnspan=6,sticky='ew')
        labels = ('历史倾向 H','形态 T','去热门 C','历史新颖度 R','探索覆盖 E','近似重复 D')
        self.weight_vars = []
        for i,(label,value) in enumerate(zip(labels,FusionConfig().weights)):
            variable = tk.StringVar(value=f'{value:g}')
            self.weight_vars.append(variable)
            ttk.Label(self.advanced,text=label).grid(row=i//3,column=(i%3)*2,padx=4)
            ttk.Entry(self.advanced,textvariable=variable,width=8).grid(row=i//3,column=(i%3)*2+1,padx=4,pady=2)
        self.advanced.grid_remove()

    def _toggle_advanced(self):
        self.advanced.grid() if self.advanced_var.get() else self.advanced.grid_remove()

    def read_config(self):
        seed = self.seed_var.get().strip()
        return FusionConfig(history_periods=int(self.periods_var.get()),
                            temperature=float(self.temperature_var.get()),
                            seed=int(seed) if seed else None,
                            weights=tuple(float(v.get()) for v in self.weight_vars))


def run_fusion_request(result_queue, progress_queue, request_id, count, snapshot, config, stop):
    """No Tk objects or mutable data-manager references cross this boundary."""
    def progress(done, total, phase='sampling'):
        try:
            progress_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            progress_queue.put_nowait((request_id,phase,done,total))
        except queue.Full:
            pass
    result, error, cancelled = None, None, False
    try:
        result = MaximumEntropyFusionGenerator(snapshot.lottery_type).generate_portfolio(
            count,snapshot,config,stop,progress,
            reference_progress=lambda done,total:progress(done,total,'reference'))
    except FusionCancelled:
        cancelled = True
    except Exception as exc:
        error = str(exc)
    result_queue.put({'kind': 'fusion', 'request_id': request_id, 'result': result,
                      'error': error, 'cancelled': cancelled or stop.is_set()})


class FusionGenerationMixin:
    def _init_fusion(self):
        self.fusion_result = None
        self._fusion_running = False
        self._fusion_request_id = 0
        self._fusion_thread = None
        self._fusion_stop = threading.Event()
        self._fusion_progress = queue.Queue(maxsize=1)
        self.fusion_controls = FusionControls(self.config_frame)
        self.fusion_controls.grid(row=5,column=0,columnspan=4,padx=5,pady=5,sticky='ew')
        self.fusion_controls.grid_remove()
        self.fusion_toolbar = ttk.Frame(self.result_frame)
        self.fusion_toolbar.pack(before=self.result_text,fill='x',padx=5)
        self.fusion_cancel_button = ttk.Button(self.fusion_toolbar,text='取消生成',command=self._cancel_fusion,state='disabled')
        self.fusion_cancel_button.pack(side='left',padx=3)
        self.fusion_reevaluate_button = ttk.Button(self.fusion_toolbar,text='按原快照复算',command=self._reevaluate_fusion,state='disabled')
        self.fusion_reevaluate_button.pack(side='left',padx=3)
        self.fusion_export_button = ttk.Button(self.fusion_toolbar,text='导出融合结果',command=self._export_fusion,state='disabled')
        self.fusion_export_button.pack(side='left',padx=3)
        self.fusion_details_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.fusion_toolbar,text='查看 F 与贡献明细',variable=self.fusion_details_var,command=self._render_fusion_result).pack(side='left',padx=3)
        self.fusion_toolbar.pack_forget()

    def _sync_fusion_visibility(self):
        fusion = self.strategy_map.get(self.strategy_var.get()) == 'fusion'
        if fusion:
            self.filter_frame.grid_remove()
            self.fusion_controls.grid()
        else:
            self.fusion_controls.grid_remove()
            self.filter_frame.grid()
        if fusion or self._fusion_running or self.fusion_result is not None:
            self.fusion_toolbar.pack(before=self.result_text,fill='x',padx=5)
        else:
            self.fusion_toolbar.pack_forget()

    def _read_fusion_request(self, lottery_type):
        # IntVar.get truncates decimal Tcl values; validate the original text instead.
        raw = str(self.getvar(self.num_sets_var._name))
        if not raw.isdecimal() or not 1 <= int(raw) <= 100:
            raise ValueError('融合注数必须为1至100的整数')
        count = int(raw)
        config = self.fusion_controls.read_config()
        config.budget(count)
        data = self.data_manager.get_history_data(lottery_type)
        snapshot = FusionHistorySnapshot.from_data(lottery_type,data,config.history_periods)
        return count, snapshot, config

    def _start_fusion(self, request):
        self._fusion_request_id += 1
        self._fusion_stop = threading.Event()
        self._fusion_running = True
        self.fusion_cancel_button.config(state='normal')
        self._sync_fusion_visibility()
        self._fusion_thread = threading.Thread(
            target=run_fusion_request,
            args=(self.generation_queue,self._fusion_progress,self._fusion_request_id,*request,self._fusion_stop),
            daemon=True, name='lottery-fusion')
        self._fusion_thread.start()

    def _poll_fusion_progress(self):
        try:
            request_id,phase,done,total = self._fusion_progress.get_nowait()
        except queue.Empty:
            return
        if request_id == self._fusion_request_id and self._fusion_running and not self._fusion_stop.is_set():
            label='随机参照' if phase=='reference' else '融合采样'
            self.status_label.config(text=f'{label} {done}/{total}（{done/total:.0%}）',foreground='green')

    def _finish_fusion(self, message):
        if message['request_id'] != self._fusion_request_id:
            return
        self._fusion_running = False
        self.fusion_cancel_button.config(state='disabled')
        self._finalize_generation_ui()
        if message['cancelled'] or self._fusion_stop.is_set():
            self.status_label.config(text='融合生成已取消',foreground='gray')
        elif message['error']:
            self.status_label.config(text='融合生成失败',foreground='red')
            messagebox.showerror('生成错误',message['error'])
        else:
            self.fusion_result = message['result']
            self.fusion_export_button.config(state='normal')
            self.fusion_reevaluate_button.config(state='normal')
            self._render_fusion_result()
        self._sync_fusion_visibility()

    def _cancel_fusion(self):
        if self._fusion_running:
            self._fusion_stop.set()
            self.fusion_cancel_button.config(state='disabled')
            self.status_label.config(text='正在取消融合生成…',foreground='gray')

    def _clear_fusion_result(self):
        self.fusion_result = None
        self.fusion_export_button.config(state='disabled')
        self.fusion_reevaluate_button.config(state='disabled')

    def _render_fusion_result(self):
        if self.fusion_result is None:
            return
        text = self.fusion_result.to_markdown(details=self.fusion_details_var.get())
        self.result_text.config(state='normal')
        self.result_text.delete('1.0','end')
        self.result_text.insert('1.0',text)
        self.result_text.config(state='disabled')

    def _reevaluate_fusion(self):
        if self.fusion_result is None:
            return
        recomputed = self.fusion_result.reevaluate()
        if not math.isclose(recomputed['F'],self.fusion_result.score,abs_tol=1e-10):
            messagebox.showerror('复算错误','原快照复算与生成结果不一致')
            return
        self.status_label.config(text=f'原快照复算一致：F={recomputed["F"]:.6f}',foreground='green')

    def _export_fusion(self):
        if self.fusion_result is None:
            return
        path = filedialog.asksaveasfilename(title='导出融合结果',defaultextension='.json',
                filetypes=[('完整复现数据','*.json'),('Markdown报告','*.md')],
                initialfile=f'fusion-{self.fusion_result.snapshot.lottery_type}.json')
        if not path:
            return
        try:
            content = self.fusion_result.to_markdown() if path.lower().endswith(('.md','.txt')) else json.dumps(self.fusion_result.to_dict(),ensure_ascii=False,indent=2,allow_nan=False)
            with open(path,'w',encoding='utf-8') as stream:
                stream.write(content)
            messagebox.showinfo('导出完成',f'融合结果已导出到:\n{path}')
        except (OSError,ValueError) as exc:
            messagebox.showerror('导出失败',str(exc))
