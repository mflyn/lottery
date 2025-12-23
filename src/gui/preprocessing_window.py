import tkinter as tk
from tkinter import ttk, messagebox
from ..core.preprocessing.data_preprocessor import DataPreprocessor

class PreprocessingWindow(tk.Toplevel):
    """数据预处理窗口"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.preprocessor = DataPreprocessor()
        
        self.title("数据预处理")
        self.geometry("800x600")
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # === 预处理配置选项卡 ===
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="预处理配置")
        
        # 特征选择区域
        feature_frame = ttk.LabelFrame(config_frame, text="特征选择")
        feature_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 分类特征选择
        ttk.Label(feature_frame, text="分类特征:").pack(anchor=tk.W, padx=5)
        self.cat_features = tk.Listbox(feature_frame, selectmode=tk.MULTIPLE, height=4)
        self.cat_features.pack(fill=tk.X, padx=5, pady=2)
        
        # 数值特征选择
        ttk.Label(feature_frame, text="数值特征:").pack(anchor=tk.W, padx=5)
        self.num_features = tk.Listbox(feature_frame, selectmode=tk.MULTIPLE, height=4)
        self.num_features.pack(fill=tk.X, padx=5, pady=2)
        
        # 预处理选项
        options_frame = ttk.LabelFrame(config_frame, text="预处理选项")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 清洗选项
        self.clean_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="执行数据清洗",
            variable=self.clean_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # 缩放选项
        self.scale_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="特征缩放",
            variable=self.scale_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # === 预处理结果选项卡 ===
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="预处理结果")
        
        # 结果显示区域
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=20,
                                   bg='#f8f9fa', fg='#212529', insertbackground='#212529')
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="开始预处理",
            command=self.run_preprocessing
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="保存结果",
            command=self.save_results
        ).pack(side=tk.RIGHT, padx=5)
        
        # 初始化特征列表
        self.update_feature_lists()
        
    def update_feature_lists(self):
        """更新特征列表"""
        try:
            df = self.data_manager.get_data()
            if df is not None:
                # 清空列表
                self.cat_features.delete(0, tk.END)
                self.num_features.delete(0, tk.END)
                
                # 添加所有列
                for col in df.columns:
                    if df[col].dtype in ['object', 'category']:
                        self.cat_features.insert(tk.END, col)
                    elif df[col].dtype in ['int64', 'float64']:
                        self.num_features.insert(tk.END, col)
        except Exception as e:
            messagebox.showerror("错误", f"更新特征列表失败: {str(e)}")
            
    def run_preprocessing(self):
        """执行预处理"""
        try:
            # 获取选择的特征
            cat_cols = [self.cat_features.get(i) for i in self.cat_features.curselection()]
            num_cols = [self.num_features.get(i) for i in self.num_features.curselection()]
            
            # 获取原始数据
            df = self.data_manager.get_data()
            if df is None:
                messagebox.showerror("错误", "没有可用的数据")
                return
                
            # 执行预处理
            processed_data = self.preprocessor.preprocess_data(
                df,
                categorical_columns=cat_cols,
                numerical_columns=num_cols
            )
            
            # 获取预处理报告
            summary = self.preprocessor.get_preprocessing_summary(df, processed_data)
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "预处理完成!\n\n")
            self.result_text.insert(tk.END, f"原始数据形状: {summary['original_shape']}\n")
            self.result_text.insert(tk.END, f"处理后数据形状: {summary['processed_shape']}\n\n")
            self.result_text.insert(tk.END, "数据质量报告:\n")
            self.result_text.insert(tk.END, str(summary['cleaning_report']))
            
            # 保存处理后的数据
            self.processed_data = processed_data
            
        except Exception as e:
            messagebox.showerror("错误", f"预处理失败: {str(e)}")
            
    def save_results(self):
        """保存预处理结果"""
        try:
            if hasattr(self, 'processed_data'):
                self.data_manager.update_data(self.processed_data)
                messagebox.showinfo("成功", "预处理结果已保存")
            else:
                messagebox.showerror("错误", "没有可用的预处理结果")
        except Exception as e:
            messagebox.showerror("错误", f"保存结果失败: {str(e)}")