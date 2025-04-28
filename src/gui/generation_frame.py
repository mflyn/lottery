# src/gui/generation_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional
import pandas as pd
from src.core.analyzers import FrequencyAnalyzer
from src.core.number_generator import generate_random_numbers, generate_hot_cold_numbers

if TYPE_CHECKING:
    from src.core.data_manager import LotteryDataManager
    from src.core.analyzer import LotteryAnalyzer

class GenerationFrame(ttk.Frame):
    """号码推荐功能框架"""
    def __init__(self, master: tk.Widget, data_manager: 'LotteryDataManager', analyzer: 'LotteryAnalyzer', **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.analyzer = analyzer

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # --- 顶部配置区域 ---
        config_frame = ttk.LabelFrame(self, text="生成选项")
        config_frame.pack(padx=10, pady=(10, 5), fill="x")

        # 彩票类型选择
        ttk.Label(config_frame, text="选择彩票类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lottery_type_var = tk.StringVar(value='ssq') # 默认双色球
        ssq_radio = ttk.Radiobutton(config_frame, text="双色球", variable=self.lottery_type_var, value='ssq', command=self._on_lottery_type_change)
        dlt_radio = ttk.Radiobutton(config_frame, text="大乐透", variable=self.lottery_type_var, value='dlt', command=self._on_lottery_type_change)
        ssq_radio.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        dlt_radio.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # 生成数量
        ttk.Label(config_frame, text="生成注数:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.num_sets_var = tk.IntVar(value=5) # 默认生成5注
        num_sets_spinbox = ttk.Spinbox(config_frame, from_=1, to=100, textvariable=self.num_sets_var, width=5)
        num_sets_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 生成策略 (后续添加)
        ttk.Label(config_frame, text="生成策略:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.strategy_var = tk.StringVar(value="random") # 默认随机
        strategy_combo = ttk.Combobox(config_frame, textvariable=self.strategy_var, values=["random", "hot_cold", "custom"], state="readonly") # 示例策略
        strategy_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        # TODO: 实现不同策略

        # 生成按钮
        generate_button = ttk.Button(config_frame, text="生成号码", command=self.generate_numbers)
        generate_button.grid(row=3, column=0, columnspan=3, pady=10)

        # --- 结果显示区域 ---
        result_frame = ttk.LabelFrame(self, text="推荐号码")
        result_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.result_text = tk.Text(result_frame, wrap="word", height=15, state="disabled")
        self.result_text.pack(padx=5, pady=5, fill="both", expand=True)

    def _on_lottery_type_change(self):
        """切换彩票类型时的处理（例如，清空结果）"""
        self.clear_results()
        # 后续可能需要根据彩票类型调整策略选项等
        print(f"切换到彩票类型: {self.lottery_type_var.get()}")

    def clear_results(self):
        """清空结果显示区域"""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state="disabled")

    def generate_numbers(self):
        """根据选定策略生成号码"""
        self.clear_results()
        lottery_type = self.lottery_type_var.get()
        num_sets = self.num_sets_var.get()
        strategy = self.strategy_var.get()

        # 占位符：显示生成信息
        display_text = f"正在为【{self.data_manager.LOTTERY_TYPES[lottery_type]}】生成 {num_sets} 注号码...\n"
        display_text += f"使用策略: {strategy}\n\n"

        # --- 调用核心生成逻辑 ---
        # TODO: 在 analyzer 中实现号码生成逻辑，并调用
        generated_sets = [] # 这里应该是调用 analyzer 返回的结果
        # 示例：仅生成随机号码
        if strategy == "random":
            # from src.core.number_generator import generate_random_numbers # 不再需要临时导入
            generated_sets = generate_random_numbers(lottery_type, num_sets)

        elif strategy == "hot_cold":
            # 1. 获取历史数据
            history_data = self.data_manager.get_history_data(lottery_type)
            if history_data.empty or len(history_data) < 10: # 简单检查，至少需要少量数据
                messagebox.showerror("错误", f"历史数据不足 ({len(history_data)} 条)，无法执行冷热分析。请先更新数据。")
                return

            # 2. 预处理数据 (类似 DataAnalysisFrame)
            processed_data = self._preprocess_data_for_analysis(history_data.copy(), lottery_type)
            if processed_data is None:
                messagebox.showerror("错误", "准备分析数据时出错。")
                return

            # 3. 执行频率分析
            try:
                freq_analyzer = FrequencyAnalyzer(lottery_type)
                freq_results = freq_analyzer.analyze(processed_data)
                if not freq_results or not any(area in freq_results for area in ['red', 'blue', 'front', 'back']): # 再次检查结果是否有效
                    messagebox.showerror("错误", "频率分析未能生成有效结果。")
                    return

            except Exception as e:
                messagebox.showerror("分析错误", f"执行频率分析时出错: {e}")
                return

            # 4. 调用冷热生成器
            generated_sets = generate_hot_cold_numbers(lottery_type, num_sets, freq_results)
            if not generated_sets:
                # 生成函数内部会打印错误，这里给用户一个通用提示
                messagebox.showerror("生成失败", "未能根据冷热策略生成号码，请检查控制台输出。")
                # 不提前 return，让后续代码显示"未能生成号码"

        else:
            messagebox.showwarning("提示", f"策略 '{strategy}' 尚未实现。")
            return # 提前返回

        if generated_sets:
            for i, nums in enumerate(generated_sets):
                # 格式化号码显示
                if lottery_type == 'ssq':
                    # 将 numpy int 转换为 python int
                    red_display = sorted([int(n) for n in nums['red']])
                    blue_display = int(nums['blue']) # 蓝球也是 numpy int
                    formatted_nums = f"红球: {red_display} | 蓝球: {blue_display}"
                elif lottery_type == 'dlt':
                    # 将 numpy int 转换为 python int
                    front_display = sorted([int(n) for n in nums['front']])
                    back_display = sorted([int(n) for n in nums['back']])
                    formatted_nums = f"前区: {front_display} | 后区: {back_display}"
                else:
                    formatted_nums = str(nums) # 备用
                display_text += f"第 {i+1} 注: {formatted_nums}\n"
        else:
            display_text += "未能生成号码。\n"
        # --- 结束调用 ---

        self.result_text.config(state="normal")
        self.result_text.insert("1.0", display_text)
        self.result_text.config(state="disabled")

    def _preprocess_data_for_analysis(self, df: pd.DataFrame, lottery_type: str) -> Optional[pd.DataFrame]:
        """验证和准备用于分析的数据 (从 DataAnalysisFrame 借鉴并简化)"""
        try:
            required_num_cols = []
            if lottery_type == 'ssq':
                required_num_cols = ['red_numbers', 'blue_number']
            elif lottery_type == 'dlt':
                required_num_cols = ['front_numbers', 'back_numbers']
            else:
                print(f"错误：未知的彩票类型 {lottery_type}")
                return None

            missing_cols = [col for col in required_num_cols if col not in df.columns]
            if missing_cols:
                print(f"错误：数据缺少必需的号码列: {missing_cols}")
                return None

            # 确保蓝球/后区是列表（简化处理，假设 dlt 已经是列表）
            if lottery_type == 'ssq' and 'blue_number' in df.columns:
                if not pd.api.types.is_list_like(df['blue_number'].iloc[0]):
                    df.loc[:, 'blue_numbers'] = df['blue_number'].apply(lambda x: [x] if pd.notna(x) else [])
                    df = df.drop(columns=['blue_number']) # 删除旧列
                elif 'blue_numbers' not in df.columns: # 如果已经是 list 但列名不对
                    df = df.rename(columns={'blue_number': 'blue_numbers'})

            # 确认最终需要的号码列存在
            final_cols = []
            if lottery_type == 'ssq': final_cols = ['red_numbers', 'blue_numbers']
            elif lottery_type == 'dlt': final_cols = ['front_numbers', 'back_numbers']

            if not all(col in df.columns for col in final_cols):
                print(f"错误：预处理后缺少最终号码列: {final_cols}, 实际: {list(df.columns)}")
                return None

            return df

        except Exception as e:
            print(f"预处理数据时出错: {e}")
            return None 