import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatisticalAnalysisFrame(ttk.Frame):
    """统计分析框架"""
    
    def __init__(self, master, data_manager):
        super().__init__(master)
        self.data_manager = data_manager
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 控制面板
        control_frame = ttk.LabelFrame(self, text="分析控制")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 选择彩种
        lottery_frame = ttk.Frame(control_frame)
        lottery_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lottery_frame, text="彩种:").pack(side=tk.LEFT, padx=5)
        self.lottery_var = tk.StringVar(value="dlt")
        ttk.Radiobutton(
            lottery_frame, text="大乐透", 
            variable=self.lottery_var, value="dlt"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            lottery_frame, text="双色球", 
            variable=self.lottery_var, value="ssq"
        ).pack(side=tk.LEFT, padx=5)
        
        # 分析维度选择
        dimension_frame = ttk.Frame(control_frame)
        dimension_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dimension_frame, text="分析维度:").pack(side=tk.LEFT, padx=5)
        self.dimension_var = tk.StringVar(value="frequency")
        dimensions = [
            ("号码频率", "frequency"),
            ("奇偶比例", "odd_even"),
            ("区间分布", "interval"),
            ("和值分析", "sum"),
            ("遗漏分析", "missing")
        ]
        for text, value in dimensions:
            ttk.Radiobutton(
                dimension_frame, text=text,
                variable=self.dimension_var, value=value
            ).pack(side=tk.LEFT, padx=5)
        
        # 图表区域
        self.figure = plt.Figure(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定更新事件
        self.lottery_var.trace('w', lambda *args: self._update_analysis())
        self.dimension_var.trace('w', lambda *args: self._update_analysis())
        
    def _update_analysis(self):
        """更新分析结果"""
        lottery_type = self.lottery_var.get()
        dimension = self.dimension_var.get()
        
        # 获取数据
        data = self.data_manager.get_lottery_data(lottery_type)
        
        # 清除现有图表
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 根据维度绘制不同的图表
        if dimension == "frequency":
            self._plot_frequency_analysis(ax, data, lottery_type)
        elif dimension == "odd_even":
            self._plot_odd_even_analysis(ax, data, lottery_type)
        elif dimension == "interval":
            self._plot_interval_analysis(ax, data, lottery_type)
        elif dimension == "sum":
            self._plot_sum_analysis(ax, data, lottery_type)
        elif dimension == "missing":
            self._plot_missing_analysis(ax, data, lottery_type)
            
        self.canvas.draw()