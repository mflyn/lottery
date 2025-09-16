import tkinter as tk
from tkinter import ttk, messagebox
from ..controllers.feature_engineering_controller import FeatureEngineeringController

class FeatureEngineeringFrame(ttk.Frame):
    """特征工程界面"""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # 初始化控制器
        self.controller = FeatureEngineeringController()
        
        # 注册回调函数
        self.controller.register_callback('on_feature_generated', self._on_feature_generated)
        self.controller.register_callback('on_feature_selected', self._on_feature_selected)
        self.controller.register_callback('on_error', self._on_error)
        
        # 存储数据
        self.features_df = None
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 彩票类型选择
        lottery_frame = ttk.LabelFrame(self, text="彩票类型")
        lottery_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lottery_type = tk.StringVar(value="ssq")
        ttk.Radiobutton(lottery_frame, text="双色球", variable=self.lottery_type, value="ssq").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(lottery_frame, text="大乐透", variable=self.lottery_type, value="dlt").pack(side=tk.LEFT, padx=5)
        
        # 特征生成
        generate_frame = ttk.LabelFrame(self, text="特征生成")
        generate_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(generate_frame, text="期数:").grid(row=0, column=0, padx=5, pady=5)
        self.periods_var = tk.IntVar(value=100)
        ttk.Entry(generate_frame, textvariable=self.periods_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(generate_frame, text="生成特征", command=self._generate_features).grid(row=0, column=2, padx=5, pady=5)
        
        # 特征选择
        select_frame = ttk.LabelFrame(self, text="特征选择")
        select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(select_frame, text="目标变量:").grid(row=0, column=0, padx=5, pady=5)
        self.target_var = tk.StringVar(value="blue")
        ttk.Entry(select_frame, textvariable=self.target_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(select_frame, text="方法:").grid(row=1, column=0, padx=5, pady=5)
        self.method_var = tk.StringVar(value="mutual_info")
        ttk.Combobox(select_frame, textvariable=self.method_var, values=["mutual_info", "f_classif"]).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(select_frame, text="特征数量:").grid(row=2, column=0, padx=5, pady=5)
        self.k_var = tk.IntVar(value=10)
        ttk.Entry(select_frame, textvariable=self.k_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(select_frame, text="选择特征", command=self._select_features).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(self, text="结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _generate_features(self):
        """生成特征"""
        # 初始化控制器
        lottery_type = self.lottery_type.get()
        if not self.controller.initialize(lottery_type):
            return
            
        # 获取期数
        try:
            periods = self.periods_var.get()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的期数")
            return
            
        # 生成特征
        self.controller.generate_features(periods)
        
    def _select_features(self):
        """选择特征"""
        if self.features_df is None:
            messagebox.showwarning("警告", "请先生成特征")
            return
            
        # 获取参数
        target_name = self.target_var.get()
        method = self.method_var.get()
        
        try:
            k = self.k_var.get()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的特征数量")
            return
            
        # 获取目标变量
        if target_name not in self.raw_data.columns:
            messagebox.showerror("错误", f"目标变量 {target_name} 不存在")
            return
            
        target = self.raw_data[target_name]
        
        # 选择特征
        self.controller.select_features(self.features_df, target, method, k)
        
    def _on_feature_generated(self, result):
        """特征生成完成回调"""
        if not result:
            return
            
        self.features_df = result['normalized_features']
        self.raw_data = result.get('raw_data')
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"特征生成完成，共 {len(self.features_df.columns)} 个特征\n\n")
        
        # 显示前5行数据
        self.result_text.insert(tk.END, "特征预览:\n")
        self.result_text.insert(tk.END, str(self.features_df.head()))
        
    def _on_feature_selected(self, selected_features):
        """特征选择完成回调"""
        if selected_features is None:
            return
            
        self.features_df = selected_features
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"特征选择完成，选择了 {len(selected_features.columns)} 个特征\n\n")
        
        # 显示特征重要性
        importance = self.controller.get_feature_importance_report()
        if importance is not None:
            self.result_text.insert(tk.END, "特征重要性:\n")
            self.result_text.insert(tk.END, str(importance))
        
    def _on_error(self, error_message):
        """错误回调"""
        messagebox.showerror("错误", error_message)