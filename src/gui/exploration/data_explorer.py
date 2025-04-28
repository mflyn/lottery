import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd
from typing import Dict, Any

class DataExplorer(ttk.Frame):
    def __init__(self, master, data: pd.DataFrame):
        super().__init__(master)
        self.data = data
        self.current_view = None
        self.filters = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI布局"""
        # 创建左侧控制面板
        self.control_panel = ttk.Frame(self)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建视图选择器
        self._create_view_selector()
        
        # 创建过滤器面板
        self._create_filter_panel()
        
        # 创建图表区域
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 初始化图表
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def _create_view_selector(self):
        """创建视图选择器"""
        view_frame = ttk.LabelFrame(self.control_panel, text="数据视图")
        view_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.view_types = {
            "频率分布": self._show_frequency_distribution,
            "时间趋势": self._show_time_trend,
            "相关性分析": self._show_correlation,
            "号码分布": self._show_number_distribution,
            "统计摘要": self._show_summary_stats
        }
        
        for view_name in self.view_types.keys():
            ttk.Radiobutton(
                view_frame, 
                text=view_name,
                value=view_name,
                command=lambda v=view_name: self._change_view(v)
            ).pack(anchor=tk.W, padx=5, pady=2)
            
    def _create_filter_panel(self):
        """创建过滤器面板"""
        filter_frame = ttk.LabelFrame(self.control_panel, text="数据过滤")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 日期范围过滤
        ttk.Label(filter_frame, text="日期范围:").pack(anchor=tk.W, padx=5)
        self.date_from = ttk.Entry(filter_frame, width=10)
        self.date_from.pack(anchor=tk.W, padx=5)
        self.date_to = ttk.Entry(filter_frame, width=10)
        self.date_to.pack(anchor=tk.W, padx=5)
        
        # 号码范围过滤
        ttk.Label(filter_frame, text="号码范围:").pack(anchor=tk.W, padx=5)
        self.num_from = ttk.Entry(filter_frame, width=10)
        self.num_from.pack(anchor=tk.W, padx=5)
        self.num_to = ttk.Entry(filter_frame, width=10)
        self.num_to.pack(anchor=tk.W, padx=5)
        
        # 应用过滤按钮
        ttk.Button(
            filter_frame,
            text="应用过滤",
            command=self._apply_filters
        ).pack(anchor=tk.W, padx=5, pady=5)
        
    def _change_view(self, view_name: str):
        """切换数据视图"""
        self.current_view = view_name
        self.ax.clear()
        self.view_types[view_name]()
        self.canvas.draw()
        
    def _apply_filters(self):
        """应用数据过滤"""
        filtered_data = self.data.copy()
        
        # 应用日期过滤
        if self.date_from.get() and self.date_to.get():
            filtered_data = filtered_data[
                (filtered_data['date'] >= self.date_from.get()) &
                (filtered_data['date'] <= self.date_to.get())
            ]
            
        # 应用号码范围过滤
        if self.num_from.get() and self.num_to.get():
            num_from = int(self.num_from.get())
            num_to = int(self.num_to.get())
            filtered_data = filtered_data[
                (filtered_data >= num_from) & (filtered_data <= num_to)
            ]
            
        self.data = filtered_data
        self._change_view(self.current_view)
        
    def _show_frequency_distribution(self):
        """显示频率分布"""
        sns.histplot(data=self.data, ax=self.ax)
        self.ax.set_title("号码频率分布")
        
    def _show_time_trend(self):
        """显示时间趋势"""
        self.data.plot(kind='line', ax=self.ax)
        self.ax.set_title("开奖号码时间趋势")
        
    def _show_correlation(self):
        """显示相关性分析"""
        sns.heatmap(self.data.corr(), ax=self.ax, annot=True)
        self.ax.set_title("号码相关性分析")
        
    def _show_number_distribution(self):
        """显示号码分布"""
        sns.boxplot(data=self.data, ax=self.ax)
        self.ax.set_title("号码分布情况")
        
    def _show_summary_stats(self):
        """显示统计摘要"""
        stats = self.data.describe()
        self.ax.axis('off')
        self.ax.table(
            cellText=stats.values,
            rowLabels=stats.index,
            colLabels=stats.columns,
            loc='center'
        )
        self.ax.set_title("统计摘要")