import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import TYPE_CHECKING
from ..core.features.feature_storage import FeatureStorage
from ..core.features.feature_engineering import FeatureEngineering
from src.core.feature_engineer import FeatureEngineer

if TYPE_CHECKING:
    # 避免循环导入
    pass

class FeatureEngineeringFrame(ttk.Frame):
    """特征工程界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.fe = FeatureEngineering()
        self.feature_storage = FeatureStorage()
        self.features_df = None
        self.data_manager = None
        self.feature_engineer = None
        self.engineered_data = pd.DataFrame()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主分割窗口
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # === 左侧控制面板 ===
        control_frame = ttk.LabelFrame(self.paned_window, text="特征工程控制")
        self.paned_window.add(control_frame)

        # 1. 特征生成部分
        gen_frame = ttk.LabelFrame(control_frame, text="特征生成")
        gen_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            gen_frame,
            text="生成基础特征",
            command=self._generate_basic_features
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            gen_frame,
            text="生成高级特征",
            command=self._generate_advanced_features
        ).pack(fill=tk.X, padx=5, pady=2)

        # 2. 特征处理部分
        process_frame = ttk.LabelFrame(control_frame, text="特征处理")
        process_frame.pack(fill=tk.X, padx=5, pady=5)

        # 特征选择
        select_frame = ttk.Frame(process_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(select_frame, text="选择方法:").pack(side=tk.LEFT)
        self.select_method = ttk.Combobox(
            select_frame, 
            values=['mutual_info', 'f_classif'],
            state='readonly',
            width=15
        )
        self.select_method.set('mutual_info')
        self.select_method.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(select_frame, text="特征数:").pack(side=tk.LEFT)
        self.k_var = ttk.Entry(select_frame, width=5)
        self.k_var.insert(0, "10")
        self.k_var.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            process_frame,
            text="执行特征选择",
            command=self._select_features
        ).pack(fill=tk.X, padx=5, pady=2)

        # 特征标准化
        scale_frame = ttk.Frame(process_frame)
        scale_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(scale_frame, text="标准化方法:").pack(side=tk.LEFT)
        self.scaler_type = ttk.Combobox(
            scale_frame,
            values=['standard', 'minmax'],
            state='readonly',
            width=15
        )
        self.scaler_type.set('standard')
        self.scaler_type.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            process_frame,
            text="执行标准化",
            command=self._scale_features
        ).pack(fill=tk.X, padx=5, pady=2)

        # 降维处理
        dim_frame = ttk.Frame(process_frame)
        dim_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(dim_frame, text="PCA组件数:").pack(side=tk.LEFT)
        self.n_components = ttk.Entry(dim_frame, width=5)
        self.n_components.insert(0, "0.95")
        self.n_components.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            process_frame,
            text="执行降维",
            command=self._reduce_dimensions
        ).pack(fill=tk.X, padx=5, pady=2)

        # 3. 特征存储部分
        storage_frame = ttk.LabelFrame(control_frame, text="特征存储")
        storage_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(storage_frame, text="特征集名称:").pack(anchor=tk.W, padx=5)
        self.feature_set_name = ttk.Entry(storage_frame)
        self.feature_set_name.pack(fill=tk.X, padx=5, pady=2)
        
        btn_frame = ttk.Frame(storage_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            btn_frame,
            text="保存特征",
            command=self._save_features
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="加载特征",
            command=self._load_features
        ).pack(side=tk.LEFT, padx=2)
        
        self.feature_sets = ttk.Combobox(
            storage_frame,
            values=self.feature_storage.list_feature_sets(),
            state="readonly"
        )
        self.feature_sets.pack(fill=tk.X, padx=5, pady=2)

        # === 右侧信息显示区域 ===
        info_frame = ttk.LabelFrame(self.paned_window, text="特征信息")
        self.paned_window.add(info_frame)

        # 创建notebook用于显示不同类型的信息
        self.info_notebook = ttk.Notebook(info_frame)
        self.info_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 基本信息标签页
        self.basic_info_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(self.basic_info_frame, text="基本信息")

        self.info_text = tk.Text(self.basic_info_frame, wrap=tk.WORD,
                                bg='#f8f9fa', fg='#212529', insertbackground='#212529')
        self.info_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.basic_info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.configure(yscrollcommand=scrollbar.set)

        # 特征重要性标签页
        self.importance_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(self.importance_frame, text="特征重要性")

        # 相关性矩阵标签页
        self.correlation_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(self.correlation_frame, text="相关性矩阵")

    def _generate_basic_features(self):
        """生成基础特征"""
        try:
            data = self._get_data()
            self.features_df = self.fe.generate_basic_features(data)
            self._update_info("基础特征生成完成")
            self._show_feature_info()
        except Exception as e:
            messagebox.showerror("错误", f"生成基础特征失败: {str(e)}")

    def _generate_advanced_features(self):
        """生成高级特征"""
        if self.features_df is None:
            messagebox.showwarning("警告", "请先生成基础特征")
            return
            
        try:
            self.features_df = self.fe.generate_advanced_features(self.features_df)
            self._update_info("高级特征生成完成")
            self._show_feature_info()
            self._show_correlation_matrix()
        except Exception as e:
            messagebox.showerror("错误", f"生成高级特征失败: {str(e)}")

    def _select_features(self):
        """执行特征选择"""
        if self.features_df is None:
            messagebox.showwarning("警告", "请先生成特征")
            return
            
        try:
            k = int(self.k_var.get())
            method = self.select_method.get()
            
            target = self._get_target()
            
            self.features_df = self.fe.select_features(
                self.features_df, 
                target,
                method=method,
                k=k
            )
            
            self._update_info("特征选择完成")
            self._show_feature_importance()
        except Exception as e:
            messagebox.showerror("错误", f"特征选择失败: {str(e)}")

    def _scale_features(self):
        """执行特征标准化"""
        if self.features_df is None:
            messagebox.showwarning("警告", "请先生成特征")
            return
            
        try:
            self.features_df = self.fe.scale_features(self.features_df)
            self._update_info("特征标准化完成")
            self._show_feature_info()
        except Exception as e:
            messagebox.showerror("错误", f"特征标准化失败: {str(e)}")

    def _reduce_dimensions(self):
        """执行降维"""
        if self.features_df is None:
            messagebox.showwarning("警告", "请先生成特征")
            return
            
        try:
            n_components = float(self.n_components.get())
            self.features_df = self.fe.reduce_dimensions(self.features_df, n_components)
            self._update_info("降维处理完成")
            self._show_feature_info()
        except Exception as e:
            messagebox.showerror("错误", f"降维处理失败: {str(e)}")

    def _save_features(self):
        """保存特征集"""
        if self.features_df is None:
            messagebox.showwarning("警告", "没有可保存的特征")
            return
            
        try:
            name = self.feature_set_name.get()
            if not name:
                messagebox.showwarning("警告", "请输入特征集名称")
                return
                
            file_path = self.feature_storage.save_features(self.features_df, name)
            self.feature_sets['values'] = self.feature_storage.list_feature_sets()
            messagebox.showinfo("成功", f"特征集已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存特征失败: {str(e)}")

    def _load_features(self):
        """加载特征集"""
        try:
            name = self.feature_sets.get()
            if not name:
                messagebox.showwarning("警告", "请选择要加载的特征集")
                return
                
            self.features_df = self.feature_storage.load_features(name)
            self._update_info("特征集加载完成")
            self._show_feature_info()
        except Exception as e:
            messagebox.showerror("错误", f"加载特征失败: {str(e)}")

    def _show_feature_info(self):
        """显示特征信息"""
        if self.features_df is not None:
            info = "特征集信息:\n"
            info += f"特征数量: {len(self.features_df.columns)}\n"
            info += f"样本数量: {len(self.features_df)}\n"
            info += "\n特征列表:\n"
            for col in self.features_df.columns:
                info += f"- {col}\n"
                
            info += "\n基本统计信息:\n"
            info += self.features_df.describe().to_string()
            
            self._update_info(info)

    def _show_feature_importance(self):
        """显示特征重要性图表"""
        if not hasattr(self.fe, 'feature_scores'):
            return
            
        # 清除旧图表
        for widget in self.importance_frame.winfo_children():
            widget.destroy()

        # 创建新图表
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        importance_dict = self.fe.get_feature_importance()
        features = list(importance_dict.keys())
        scores = list(importance_dict.values())
        
        y_pos = range(len(features))
        ax.barh(y_pos, scores)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features)
        ax.set_xlabel('重要性分数')
        ax.set_title('特征重要性排序')
        
        canvas = FigureCanvasTkAgg(fig, master=self.importance_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _show_correlation_matrix(self):
        """显示相关性矩阵热力图"""
        if self.features_df is None:
            return
            
        # 清除旧图表
        for widget in self.correlation_frame.winfo_children():
            widget.destroy()

        # 创建新图表
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        corr_matrix = self.features_df.corr()
        im = ax.imshow(corr_matrix, cmap='coolwarm')
        
        # 添加颜色条
        fig.colorbar(im)
        
        # 设置标签
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr_matrix.columns)
        
        ax.set_title('特征相关性矩阵')
        
        canvas = FigureCanvasTkAgg(fig, master=self.correlation_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_data_manager(self, data_manager):
        """设置数据管理器"""
        self.data_manager = data_manager

    def notify_data_updated(self):
        """数据更新通知"""
        self.features_df = None
        self._update_info("数据已更新，请重新生成特征")

    def _get_data(self) -> pd.DataFrame:
        """获取数据"""
        if not hasattr(self, 'data_manager'):
            raise RuntimeError("数据管理器未设置")
        return self.data_manager.get_history_data()

    def _get_target(self) -> pd.Series:
        """获取目标变量"""
        data = self._get_data()
        target = data['winning_numbers'].shift(-1)
        return target.dropna()

    def _update_info(self, message: str):
        """更新信息显示"""
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert(tk.END, message)

    def _on_lottery_type_change(self):
        """切换彩票类型时的处理"""
        self.feature_engineer = FeatureEngineer(self.lottery_type_var.get())
        # 清空旧数据和表格
        self.engineered_data = pd.DataFrame()
        self.display_data_in_table(self.engineered_data)
        # 可以选择加载原始数据作为预览
        # raw_data = self.data_manager.get_history_data(self.lottery_type_var.get())
        # self.display_data_in_table(raw_data)

    def run_feature_engineering(self):
        """执行特征工程计算"""
        lottery_type = self.lottery_type_var.get()
        features_to_gen = [key for key, var in self.feature_vars.items() if var.get()]

        if not features_to_gen:
            messagebox.showwarning("提示", "请至少选择一个要生成的特征。")
            return

        if not self.feature_engineer:
            messagebox.showerror("错误", "特征引擎未初始化。")
            return

        # 1. 加载原始数据
        raw_data = self.data_manager.get_history_data(lottery_type)
        if raw_data.empty:
            messagebox.showerror("错误", f"无法加载 {lottery_type} 的历史数据。请先更新。")
            return

        # 2. TODO: 数据预处理 (确保号码列是列表等)
        # 暂时假设 data_manager 返回的数据格式已经大致正确
        # 需要特别注意 SSQ 的 blue_number -> blue_numbers (list)
        if lottery_type == 'ssq' and 'blue_number' in raw_data.columns:
             if not pd.api.types.is_list_like(raw_data['blue_number'].iloc[0]):
                 raw_data.loc[:, 'blue_numbers'] = raw_data['blue_number'].apply(lambda x: [x] if pd.notna(x) else [])
                 raw_data = raw_data.drop(columns=['blue_number'])
             elif 'blue_numbers' not in raw_data.columns:
                 raw_data = raw_data.rename(columns={'blue_number': 'blue_numbers'})
        # 确认最终需要的列存在
        required_cols = self.feature_engineer._get_number_columns()
        if not required_cols or not all(col in raw_data.columns for col in required_cols.values()):
             missing = [col for col in required_cols.values() if col not in raw_data.columns] if required_cols else []
             messagebox.showerror("错误", f"预处理失败，缺少号码列: {missing}")
             return

        # 3. 生成特征
        try:
            self.engineered_data = self.feature_engineer.generate_features(raw_data, features_to_gen)
            self.display_data_in_table(self.engineered_data)
            messagebox.showinfo("成功", f"已生成特征数据，共 {len(self.engineered_data)} 条记录。")
        except Exception as e:
            messagebox.showerror("生成失败", f"生成特征时发生错误: {e}")
            print(f"详细错误: {e}")
            import traceback
            traceback.print_exc() # 打印详细 traceback

    def display_data_in_table(self, df: pd.DataFrame):
        """将带有特征的 DataFrame 显示在 Treeview 中"""
        # 清空旧数据
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        if df.empty:
            self.data_tree["columns"] = []
            self.data_tree.heading("#0", text="无数据")
            return

        # 设置列 (包括原始列和新特征列)
        columns_to_display = list(df.columns)
        # 可以选择性隐藏原始号码列表列，如果太长
        # columns_to_display = [c for c in df.columns if '_numbers' not in c and '_number' not in c] + \
        #                      [c for c in df.columns if c not in [cc for cc in df.columns if '_numbers' not in cc and '_number' not in cc]]


        self.data_tree["columns"] = columns_to_display
        self.data_tree.heading("#0", text="", anchor=tk.W)
        self.data_tree.column("#0", width=0, stretch=tk.NO)

        # 定义部分列的中文名（可选）
        column_mapping = {
            'draw_num': '期号', 'draw_date': '开奖日期', 'prize_pool': '奖池', 'sales': '销量',
            'red_sum': '红和值', 'front_sum': '前和值',
            'red_odd_even_ratio': '红奇偶比', 'blue_odd_even_ratio': '蓝奇偶比',
            'front_odd_even_ratio': '前奇偶比', 'back_odd_even_ratio': '后奇偶比',
            'red_big_small_ratio': '红大小比', 'blue_big_small_ratio': '蓝大小比',
            'front_big_small_ratio': '前大小比', 'back_big_small_ratio': '后大小比',
            'red_numbers': '红球', 'blue_numbers': '蓝球',
            'front_numbers': '前区', 'back_numbers': '后区'
        }

        for col_id in columns_to_display:
            col_name = column_mapping.get(col_id, col_id) # 使用映射或原始ID
            self.data_tree.heading(col_id, text=col_name, anchor=tk.W)
            # 简单设置宽度
            width = 80
            if 'ratio' in col_id:
                width = 60
            elif 'sum' in col_id:
                width = 60
            elif 'date' in col_id:
                width = 100
            elif 'numbers' in col_id:
                width = 120 # 号码列宽一点
            self.data_tree.column(col_id, anchor=tk.W, width=width, stretch=tk.YES) # 允许列伸缩

        # 插入数据
        for index, row in df.iterrows():
            display_values = []
            for col_id in columns_to_display:
                value = row[col_id]
                if isinstance(value, list):
                    # 对号码列表进行格式化
                    display_values.append(' '.join(map(str, value)))
                elif pd.isna(value):
                    display_values.append('')
                else:
                    display_values.append(str(value))
            self.data_tree.insert("", tk.END, values=display_values)
