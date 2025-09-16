import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
from src.core.ssq_analyzer import SSQAnalyzer

class AnalysisTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.analyzer = SSQAnalyzer()
        self._setup_ui()
        
    def _setup_ui(self):
        # 创建控制面板
        control_frame = ttk.LabelFrame(self, text="分析控制")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 日期范围选择
        ttk.Label(control_frame, text="日期范围:").pack(anchor=tk.W, padx=5)
        self.date_from = ttk.Entry(control_frame, width=10)
        self.date_from.pack(anchor=tk.W, padx=5)
        self.date_to = ttk.Entry(control_frame, width=10)
        self.date_to.pack(anchor=tk.W, padx=5)
        
        # 号码范围选择
        ttk.Label(control_frame, text="号码范围:").pack(anchor=tk.W, padx=5)
        self.num_from = ttk.Entry(control_frame, width=10)
        self.num_from.pack(anchor=tk.W, padx=5)
        self.num_to = ttk.Entry(control_frame, width=10)
        self.num_to.pack(anchor=tk.W, padx=5)
        
        # 分析按钮
        ttk.Button(
            control_frame,
            text="执行分析",
            command=self._run_analysis
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        # 创建图表区域
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def _run_analysis(self):
        """执行分析并显示结果"""
        try:
            date_range = None
            if self.date_from.get() and self.date_to.get():
                date_range = (self.date_from.get(), self.date_to.get())
                
            number_range = None
            if self.num_from.get() and self.num_to.get():
                number_range = (int(self.num_from.get()), int(self.num_to.get()))
                
            # 获取数据
            data = self.analyzer.data_fetcher.fetch_history(100)
            
            # 执行分析
            results = self.analyzer.explore_data(
                data,
                date_range=date_range,
                number_range=number_range
            )
            
            # 更新图表显示
            self._update_charts(results)
            
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {str(e)}")
            
    def _update_charts(self, results: Dict):
        """更新图表显示"""
        self.ax.clear()
        
        # 绘制频率分布
        sns.barplot(
            x=list(results['frequency']['red_numbers'].keys()),
            y=list(results['frequency']['red_numbers'].values()),
            ax=self.ax
        )
        self.ax.set_title("红球号码频率分布")
        self.canvas.draw()

class AdvancedAnalysisTab(ttk.Frame):
    """高级数据分析标签页"""
    
    def __init__(self, master):
        super().__init__(master)
        self.init_ui()
        
    def init_ui(self):
        # 创建左侧控制面板
        control_frame = ttk.LabelFrame(self, text="分析控制")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 添加高级筛选
        filter_frame = ttk.LabelFrame(control_frame, text="高级筛选")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 数值范围筛选
        ttk.Label(filter_frame, text="号码范围:").pack(anchor=tk.W)
        range_frame = ttk.Frame(filter_frame)
        range_frame.pack(fill=tk.X, padx=5)
        
        self.min_num = ttk.Entry(range_frame, width=5)
        self.min_num.pack(side=tk.LEFT)
        ttk.Label(range_frame, text=" - ").pack(side=tk.LEFT)
        self.max_num = ttk.Entry(range_frame, width=5)
        self.max_num.pack(side=tk.LEFT)
        
        # 特征选择
        feature_frame = ttk.LabelFrame(control_frame, text="特征选择")
        feature_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.features = ['红球频率', '蓝球频率', '号码间隔', '历史热度']
        self.feature_vars = {}
        for feature in self.features:
            var = tk.BooleanVar(value=True)
            self.feature_vars[feature] = var
            ttk.Checkbutton(
                feature_frame,
                text=feature,
                variable=var,
                command=self.update_analysis
            ).pack(anchor=tk.W)
        
        # 分析维度
        dimension_frame = ttk.LabelFrame(control_frame, text="分析维度")
        dimension_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dimension_var = tk.StringVar(value="期号")
        dimensions = ["期号", "日期", "月份", "星期"]
        for dim in dimensions:
            ttk.Radiobutton(
                dimension_frame,
                text=dim,
                value=dim,
                variable=self.dimension_var,
                command=self.update_analysis
            ).pack(anchor=tk.W)
        
        # 创建右侧显示区域
        display_frame = ttk.Frame(self)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(display_frame, text="数据预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(preview_frame, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
    
    def update_analysis(self):
        """更新分析结果"""
        # 获取选中的特征
        selected_features = [
            feature for feature, var in self.feature_vars.items()
            if var.get()
        ]
        
        # 获取分析维度
        dimension = self.dimension_var.get()
        
        # 获取号码范围
        try:
            min_num = int(self.min_num.get()) if self.min_num.get() else None
            max_num = int(self.max_num.get()) if self.max_num.get() else None
        except ValueError:
            min_num = None
            max_num = None
        
        # 更新显示
        self.update_preview(selected_features, dimension, min_num, max_num)
    
    def update_preview(self, features, dimension, min_num, max_num):
        """更新数据预览"""
        # 这里实现数据预览更新逻辑
        pass
