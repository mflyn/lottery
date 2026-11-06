"""Native fusion scoring widgets shared by evaluation display and its reports."""
import tkinter as tk
from tkinter import ttk

from src.core.generators.fusion.config import FACTOR_NAMES, FusionConfig

FACTOR_LABELS = ('历史倾向 H','形态成本 T','去热门成本 C','历史新颖度 R','探索覆盖 E','整注相似 D')


class FusionEvaluationMixin:
    def _create_scoring_settings_area(self,parent):
        frame=ttk.LabelFrame(parent,text='融合评价设置',padding=10)
        frame.pack(fill=tk.X,pady=(0,10))
        self.analysis_periods_var=tk.StringVar(value='180')
        row=ttk.Frame(frame); row.pack(fill='x')
        ttk.Label(row,text='统一历史范围:').pack(side='left')
        ttk.Combobox(row,textvariable=self.analysis_periods_var,
                     values=['30','50','100','180','200','500','全部'],width=10).pack(side='left',padx=8)
        ttk.Label(row,text='评分与统计详情使用同一快照',foreground='gray').pack(side='left')
        grid=ttk.Frame(frame); grid.pack(fill='x',pady=5)
        self.evaluation_weight_vars=[]
        for i,(label,value) in enumerate(zip(FACTOR_LABELS,FusionConfig().weights)):
            var=tk.StringVar(value=f'{value:g}')
            self.evaluation_weight_vars.append(var)
            ttk.Label(grid,text=label).grid(row=i//3,column=2*(i%3),padx=4,pady=3)
            ttk.Entry(grid,textvariable=var,width=8).grid(row=i//3,column=2*(i%3)+1,padx=4)
        ttk.Label(frame,text='非负权重自动归一化；原始效用和各项贡献可在评分详细信息中查看。',foreground='gray').pack(anchor='w')

    def get_fusion_config(self,periods=180):
        return FusionConfig(history_periods=periods or 180,
                            weights=tuple(float(v.get()) for v in self.evaluation_weight_vars))

    def _create_result_display_area(self,parent):
        frame=ttk.LabelFrame(parent,text='综合评价',padding=10)
        frame.pack(fill='x',pady=(0,10))
        ttk.Label(frame,text='随机参照百分位',font=('Arial',12,'bold')).pack(anchor='w')
        self.random_reference_label=ttk.Label(frame,text='--',font=('Arial',48,'bold'),foreground='#007bff')
        self.random_reference_label.pack(anchor='w',pady=(4,0))
        self.random_reference_caption=ttk.Label(frame,text='严格超过的随机参照比例',wraplength=650)
        self.random_reference_caption.pack(anchor='w')
        self.random_reference_note=ttk.Label(frame,text='',foreground='gray',wraplength=650)
        self.random_reference_note.pack(anchor='w',pady=(4,8))
        self.score_details_var=tk.BooleanVar(value=False)
        self.score_details_toggle=ttk.Checkbutton(frame,text='查看 F 与贡献明细',
                variable=self.score_details_var,command=self._toggle_score_details)
        self.score_details_toggle.pack(anchor='w')
        self.score_details_frame=ttk.LabelFrame(frame,text='评分详细信息',padding=8)
        left=ttk.Frame(self.score_details_frame); left.pack(side='left',padx=10)
        ttk.Label(left,text='原始效用 F',font=('Arial',11,'bold')).pack()
        self.total_score_label=ttk.Label(left,text='--',font=('Arial',18,'bold'),foreground='#007bff')
        self.total_score_label.pack(pady=8)
        self.rating_label=ttk.Label(left,text='单注 K=1，D=0')
        self.rating_label.pack()
        self.stars_label=ttk.Label(left,text='')  # Kept for lifecycle reset, not displayed.
        right=ttk.Frame(self.score_details_frame); right.pack(side='left',fill='both',expand=True,padx=10)
        ttk.Label(right,text='因素原值与有符号贡献',font=('Arial',11,'bold')).pack(anchor='w')
        self.dimension_labels={}
        for key,name in zip(FACTOR_NAMES,FACTOR_LABELS):
            row=ttk.Frame(right); row.pack(fill='x',pady=2)
            ttk.Label(row,text=name,width=14).pack(side='left')
            progress=ttk.Progressbar(row,length=100,mode='determinate')
            progress.pack(side='left',padx=4)
            label=ttk.Label(row,text='--',width=25); label.pack(side='left')
            icon=ttk.Label(row,text=''); icon.pack(side='left')
            self.dimension_labels[key]={'progress':progress,'label':label,'icon':icon}

    def _toggle_score_details(self):
        if self.score_details_var.get():
            self.score_details_frame.pack(fill='x',pady=(8,0))
        else:
            self.score_details_frame.pack_forget()

    def _reset_score_display(self,caption='严格超过的随机参照比例',detail_status=''):
        self.score_details_var.set(False)
        self._toggle_score_details()
        self.total_score_label.config(text='--',foreground='#007bff')
        self.random_reference_label.config(text='--')
        self.random_reference_caption.config(text=caption)
        self.random_reference_note.config(text='')
        self.rating_label.config(text=detail_status)
        self.stars_label.config(text='')
        for widgets in self.dimension_labels.values():
            widgets['progress']['value']=0
            widgets['label'].config(text='--')
            widgets['icon'].config(text='')

    def _update_result_display(self,result):
        self.total_score_label.config(text=f'{result["total_score"]:.6f}',foreground='#007bff')
        self.rating_label.config(text='单注融合效用（K=1，D=0）')
        self.stars_label.config(text='')
        reference=result['fusion'].get('random_reference')
        if reference is not None:
            low,high=reference['interval_95_percent']
            lottery={'ssq':'双色球','dlt':'大乐透'}[result['fusion']['lottery_type']]
            self.random_reference_label.config(text=f"约 {reference['exceed_percent']:.1f}%")
            self.random_reference_caption.config(text=f"严格超过的随机参照比例（{lottery}，每组{reference['count']}注）")
            self.random_reference_note.config(text=(
                f"参照 {reference['samples']:,} 组×{reference['count']}注；持平 {reference['tied_percent']:.1f}%\n"
                f"抽样95%区间 {low:.1f}%–{high:.1f}%"))
        else:
            self.random_reference_label.config(text='--')
            self.random_reference_caption.config(text='随机参照未计算；展开可查看原始效用 F')
            self.random_reference_note.config(text='')
        for key,widgets in self.dimension_labels.items():
            value=result['scores'][key]
            contribution=result['fusion']['contributions'][key]
            widgets['progress']['value']=((value+1)/2 if key=='H' else value)*100
            widgets['label'].config(text=f'{value:.4f} | 贡献 {contribution:+.4f}')
            widgets['icon'].config(text='奖励' if key=='H' else ('K=1不适用' if key=='D' else '成本'))
        self._update_detail_analysis(result)
