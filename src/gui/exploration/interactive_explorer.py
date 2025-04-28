import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns
import pandas as pd
from typing import Dict, Any, Optional

class InteractiveDataExplorer(ttk.Frame):
    """交互式数据探索界面"""
    
    def __init__(self, master, data: pd.DataFrame):
        super().__init__(master)
        # 添加数据验证
        if not isinstance(data, pd.DataFrame) or data.empty:
            raise ValueError("Invalid or empty data provided")
            
        # 添加数据预处理
        self.data = self._preprocess_data(data)
        # 添加数据缓存机制
        self._data_cache = {}
        self.current_view = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI布局"""
        # 创建左右分栏
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        self.control_frame = self.create_control_panel()
        self.paned.add(self.control_frame)
        
        # 右侧显示区域
        self.display_frame = self.create_display_area()
        self.paned.add(self.display_frame)
        
    def create_control_panel(self) -> ttk.Frame:
        """创建控制面板"""
        frame = ttk.Frame(self.paned, width=200)
        
        # 1. 视图选择
        view_frame = ttk.LabelFrame(frame, text="视图类型")
        view_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.view_var = tk.StringVar(value="频率分布")
        views = ["频率分布", "时间趋势", "相关性分析", "号码分布", "统计摘要"]
        for view in views:
            ttk.Radiobutton(
                view_frame,
                text=view,
                value=view,
                variable=self.view_var,
                command=self.update_view
            ).pack(anchor=tk.W, padx=5, pady=2)
        
        # 2. 数据过滤
        filter_frame = ttk.LabelFrame(frame, text="数据过滤")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 日期范围
        ttk.Label(filter_frame, text="日期范围:").pack(anchor=tk.W, padx=5)
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, padx=5)
        
        self.date_from = ttk.Entry(date_frame, width=10)
        self.date_from.pack(side=tk.LEFT, padx=2)
        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)
        self.date_to = ttk.Entry(date_frame, width=10)
        self.date_to.pack(side=tk.LEFT, padx=2)
        
        # 号码范围
        ttk.Label(filter_frame, text="号码范围:").pack(anchor=tk.W, padx=5)
        num_frame = ttk.Frame(filter_frame)
        num_frame.pack(fill=tk.X, padx=5)
        
        self.num_from = ttk.Entry(num_frame, width=10)
        self.num_from.pack(side=tk.LEFT, padx=2)
        ttk.Label(num_frame, text="-").pack(side=tk.LEFT)
        self.num_to = ttk.Entry(num_frame, width=10)
        self.num_to.pack(side=tk.LEFT, padx=2)
        
        # 应用过滤按钮
        ttk.Button(
            filter_frame,
            text="应用过滤",
            command=self.apply_filters
        ).pack(pady=5)
        
        # 3. 图表设置
        chart_frame = ttk.LabelFrame(frame, text="图表设置")
        chart_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 图表样式
        ttk.Label(chart_frame, text="样式主题:").pack(anchor=tk.W, padx=5)
        self.style_var = tk.StringVar(value="default")
        style_combo = ttk.Combobox(
            chart_frame,
            textvariable=self.style_var,
            values=["default", "whitegrid", "darkgrid", "white", "dark"],
            state="readonly"
        )
        style_combo.pack(fill=tk.X, padx=5, pady=2)
        style_combo.bind("<<ComboboxSelected>>", self.update_chart_style)
        
        # 图表配置
        chart_config_frame = ttk.LabelFrame(frame, text="图表配置")
        chart_config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 图表大小
        size_frame = ttk.Frame(chart_config_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(size_frame, text="图表大小:").pack(side=tk.LEFT)
        self.fig_width = ttk.Entry(size_frame, width=5)
        self.fig_width.insert(0, "10")
        self.fig_width.pack(side=tk.LEFT, padx=2)
        ttk.Label(size_frame, text="x").pack(side=tk.LEFT)
        self.fig_height = ttk.Entry(size_frame, width=5)
        self.fig_height.insert(0, "6")
        self.fig_height.pack(side=tk.LEFT, padx=2)
        
        # 颜色主题
        color_frame = ttk.Frame(chart_config_frame)
        color_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(color_frame, text="颜色主题:").pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value="default")
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=["default", "deep", "muted", "pastel", "bright", "dark"],
            state="readonly"
        )
        color_combo.pack(side=tk.LEFT, padx=2)
        color_combo.bind("<<ComboboxSelected>>", self.update_chart_style)
        
        # 应用按钮
        ttk.Button(
            chart_config_frame,
            text="应用配置",
            command=self.apply_chart_config
        ).pack(pady=5)
        
        # 4. 数据导出
        export_frame = ttk.LabelFrame(frame, text="数据导出")
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            export_frame,
            text="导出数据",
            command=self.export_data
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            export_frame,
            text="导出图表",
            command=self.export_chart
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        return frame
        
    def create_display_area(self) -> ttk.Frame:
        """创建显示区域"""
        frame = ttk.Frame(self.paned)
        
        # 添加统计信息面板
        stats_frame = ttk.LabelFrame(frame, text="数据统计")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, width=50)
        self.stats_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建图表区域
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加matplotlib工具栏
        self.toolbar = NavigationToolbar2Tk(self.canvas, frame)
        self.toolbar.update()
        
        # 创建数据表格和分页控件
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加垂直滚动条
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 添加水平滚动条
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        hsb.pack(fill=tk.X)
        self.tree.configure(xscrollcommand=hsb.set)
        
        # 分页控件
        page_frame = ttk.Frame(frame)
        page_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(page_frame, text="<<", command=lambda: self.change_page("first")).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_frame, text="<", command=lambda: self.change_page("prev")).pack(side=tk.LEFT, padx=2)
        self.page_var = tk.StringVar(value="1/1")
        ttk.Label(page_frame, textvariable=self.page_var).pack(side=tk.LEFT, padx=10)
        ttk.Button(page_frame, text=">", command=lambda: self.change_page("next")).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_frame, text=">>", command=lambda: self.change_page("last")).pack(side=tk.LEFT, padx=2)
        
        return frame
        
    def update_view(self):
        """更新数据视图"""
        view_type = self.view_var.get()
        self.ax.clear()
        
        try:
            if view_type == "频率分布":
                self.plot_frequency_distribution()
            elif view_type == "时间趋势":
                self.plot_time_trend()
            elif view_type == "相关性分析":
                self.plot_correlation()
            elif view_type == "号码分布":
                self.plot_number_distribution()
            elif view_type == "统计摘要":
                self.plot_summary_stats()
                
            self.canvas.draw()
            self.update_data_table()
            
        except Exception as e:
            self.show_error(f"更新视图失败: {str(e)}")
            
    def apply_filters(self):
        """应用数据过滤"""
        try:
            filtered_data = self.data.copy()
            
            # 应用日期过滤
            if self.date_from.get() and self.date_to.get():
                filtered_data = filtered_data[
                    (filtered_data['date'] >= self.date_from.get()) &
                    (filtered_data['date'] <= self.date_to.get())
                ]
                
            # 应用号码过滤
            if self.num_from.get() and self.num_to.get():
                num_from = int(self.num_from.get())
                num_to = int(self.num_to.get())
                filtered_data = filtered_data[
                    (filtered_data >= num_from) & (filtered_data <= num_to)
                ]
                
            self.data = filtered_data
            self.update_view()
            
        except Exception as e:
            self.show_error(f"应用过滤失败: {str(e)}")
            
    def update_chart_style(self, event=None):
        """更新图表样式"""
        style = self.style_var.get()
        sns.set_style(style)
        self.update_view()
        
    def plot_frequency_distribution(self):
        """完善频率分布图"""
        # 添加更多可配置选项
        bins = int(self.bins_var.get()) if hasattr(self, 'bins_var') else 30
        kde = self.kde_var.get() if hasattr(self, 'kde_var') else True
        
        sns.histplot(
            data=self.data,
            bins=bins,
            kde=kde,
            ax=self.ax
        )
        self.ax.set_title("号码频率分布")
        
    def plot_time_trend(self):
        """绘制时间趋势图"""
        self.data.plot(kind='line', ax=self.ax)
        self.ax.set_title("开奖号码时间趋势")
        
    def plot_correlation(self):
        """绘制相关性分析图"""
        sns.heatmap(self.data.corr(), ax=self.ax, annot=True)
        self.ax.set_title("号码相关性分析")
        
    def plot_number_distribution(self):
        """绘制号码分布图"""
        sns.boxplot(data=self.data, ax=self.ax)
        self.ax.set_title("号码分布情况")
        
    def plot_summary_stats(self):
        """绘制统计摘要"""
        stats = self.data.describe()
        self.ax.axis('off')
        self.ax.table(
            cellText=stats.values,
            rowLabels=stats.index,
            colLabels=stats.columns,
            loc='center'
        )
        self.ax.set_title("统计摘要")
        
    def update_data_table(self):
        """更新数据表格"""
        # 清空现有数据
        self.tree.delete(*self.tree.get_children())
        
        # 设置列
        columns = list(self.data.columns)
        self.tree["columns"] = columns
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 分页显示数据
        page_size = 50
        start_idx = (self.current_page - 1) * page_size
        end_idx = start_idx + page_size
        
        for idx, row in self.data.iloc[start_idx:end_idx].iterrows():
            self.tree.insert("", "end", values=list(row))
            
        # 更新总页数
        total_pages = (len(self.data) + page_size - 1) // page_size
        self.page_var.set(f"{self.current_page}/{total_pages}")
        
    def show_error(self, message: str):
        """显示错误消息"""
        tk.messagebox.showerror("错误", message)

    def export_data(self):
        """完善数据导出功能"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("JSON files", "*.json")
                ]
            )
            if file_path:
                if file_path.endswith('.csv'):
                    self.data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.data.to_excel(file_path, index=False)
                elif file_path.endswith('.json'):
                    self.data.to_json(file_path, orient='records')
                    
        except Exception as e:
            self.show_error(f"导出数据失败: {str(e)}")

    def export_chart(self):
        """导出图表为图片"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                tk.messagebox.showinfo("成功", "图表导出成功！")
            except Exception as e:
                self.show_error(f"导出图表失败: {str(e)}")

    def change_page(self, action: str):
        """切换数据表格分页"""
        current_page = int(self.page_var.get().split('/')[0])
        total_pages = int(self.page_var.get().split('/')[1])
        
        if action == "first":
            new_page = 1
        elif action == "prev":
            new_page = max(1, current_page - 1)
        elif action == "next":
            new_page = min(total_pages, current_page + 1)
        else:  # last
            new_page = total_pages
            
        self.current_page = new_page
        self.update_data_table()
        self.page_var.set(f"{new_page}/{total_pages}")

    def apply_chart_config(self):
        """应用图表配置"""
        try:
            # 更新图表大小
            width = float(self.fig_width.get())
            height = float(self.fig_height.get())
            self.fig.set_size_inches(width, height)
            
            # 更新颜色主题
            sns.set_palette(self.color_var.get())
            
            # 重新绘制
            self.update_view()
            
        except Exception as e:
            self.show_error(f"应用图表配置失败: {str(e)}")

    def update_stats(self):
        """完善统计信息更新"""
        stats = {
            "数据总量": len(self.data),
            "数值列": len(self.data.select_dtypes(include=['number']).columns),
            "分类列": len(self.data.select_dtypes(include=['object']).columns),
            "时间列": len(self.data.select_dtypes(include=['datetime']).columns),
            "缺失值": self.data.isnull().sum().sum(),
            "数据范围": f"{self.data.min().min()} - {self.data.max().max()}",
            "更新时间": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 处理缺失值
        data = data.fillna(method='ffill')
        # 转换日期列
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        return data

    def add_advanced_features(self):
        """添加高级功能"""
        # 1. 数据分析配置面板
        analysis_frame = ttk.LabelFrame(self.control_frame, text="分析配置")
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加聚合方式选择
        ttk.Label(analysis_frame, text="聚合方式:").pack(anchor=tk.W, padx=5)
        self.agg_var = tk.StringVar(value="mean")
        ttk.Combobox(
            analysis_frame,
            textvariable=self.agg_var,
            values=["mean", "sum", "count", "median", "min", "max"],
            state="readonly"
        ).pack(fill=tk.X, padx=5, pady=2)
        
        # 2. 图表交互增强
        # 添加缩放、平移、选择等功能
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.display_frame)
        self.toolbar.update()
        
        # 3. 数据筛选增强
        filter_frame = ttk.LabelFrame(self.control_frame, text="高级筛选")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加条件筛选
        ttk.Label(filter_frame, text="条件筛选:").pack(anchor=tk.W, padx=5)
        self.filter_condition = ttk.Entry(filter_frame)
        self.filter_condition.pack(fill=tk.X, padx=5, pady=2)
        
        # 4. 导出功能增强
        export_frame = ttk.LabelFrame(self.control_frame, text="导出选项")
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加导出格式选择
        self.export_format = tk.StringVar(value="csv")
        ttk.Radiobutton(
            export_frame,
            text="CSV",
            value="csv",
            variable=self.export_format
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            export_frame,
            text="Excel",
            value="excel",
            variable=self.export_format
        ).pack(side=tk.LEFT, padx=5)
        
        # 5. 添加数据分析报告生成功能
        ttk.Button(
            self.control_frame,
            text="生成分析报告",
            command=self.generate_report
        ).pack(pady=5)
