# src/gui/generation_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional
import pandas as pd
import threading
import queue
from src.core.analyzers import FrequencyAnalyzer
from src.core.number_generator import generate_random_numbers, generate_hot_cold_numbers
from src.core.smart_recommender import SmartRecommender

if TYPE_CHECKING:
    from src.core.data_manager import LotteryDataManager
    from src.core.analyzer import LotteryAnalyzer

class GenerationFrame(ttk.Frame):
    """号码推荐功能框架"""
    def __init__(self, master: tk.Widget, data_manager: 'LotteryDataManager', analyzer: 'LotteryAnalyzer', **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.analyzer = analyzer
        self.generation_queue = queue.Queue()
        self.is_generating = False

        self.create_widgets()
        self._check_generation_queue()

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
        self.num_sets_var = tk.IntVar(value=2) # 默认生成2注
        num_sets_spinbox = ttk.Spinbox(config_frame, from_=1, to=100, textvariable=self.num_sets_var, width=5)
        num_sets_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 生成策略
        ttk.Label(config_frame, text="生成策略:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.strategy_map = {
            "统计优选": "smart_recommend",
            "随机生成": "random",
            "冷热号推荐": "hot_cold",
            "去热门-严格": "anti_popular_strict",
            "去热门-适中": "anti_popular_moderate",
            "去热门-轻度": "anti_popular_light",
            "混合模式": "hybrid_anti_popular"
        }
        self.strategy_var = tk.StringVar(value="统计优选") # 默认统计优选
        self.strategy_combo = ttk.Combobox(config_frame, textvariable=self.strategy_var, values=list(self.strategy_map.keys()), state="readonly", width=15)
        self.strategy_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 生成按钮
        self.generate_button = ttk.Button(config_frame, text="生成号码", command=self.generate_numbers)
        self.generate_button.grid(row=3, column=0, columnspan=3, pady=10)

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
        if self.is_generating:
            messagebox.showwarning("请稍候", "正在生成号码中，请勿重复操作。")
            return

        self.clear_results()
        lottery_type = self.lottery_type_var.get()
        num_sets = self.num_sets_var.get()
        strategy_display_name = self.strategy_var.get()
        strategy = self.strategy_map.get(strategy_display_name, "random")

        self.is_generating = True
        self.generate_button.config(text="生成中...", state=tk.DISABLED)
        self.master.update_idletasks()

        display_text = f"正在为【{self.data_manager.LOTTERY_TYPES[lottery_type]}】生成 {num_sets} 注号码...\n"
        display_text += f"使用策略: {strategy}\n\n"
        self.result_text.config(state="normal")
        self.result_text.insert("1.0", display_text)
        self.result_text.config(state="disabled")

        if strategy == "smart_recommend":
            generation_thread = threading.Thread(target=self._background_smart_generation, args=(lottery_type, num_sets), daemon=True)
            generation_thread.start()
        elif strategy in ["anti_popular_strict", "anti_popular_moderate", "anti_popular_light", "hybrid_anti_popular"]:
            # 去热门策略使用线程处理（可能较慢）
            generation_thread = threading.Thread(target=self._background_anti_popular_generation, args=(lottery_type, num_sets, strategy), daemon=True)
            generation_thread.start()
        else:
            # For other strategies, run them directly as they are faster
            self._background_generation(lottery_type, num_sets, strategy)

    def _background_generation(self, lottery_type, num_sets, strategy):
        generated_sets = []
        error_msg = None
        try:
            if strategy == "random":
                generated_sets = generate_random_numbers(lottery_type, num_sets)
            elif strategy == "hot_cold":
                history_data = self.data_manager.get_history_data(lottery_type)
                if history_data.empty or len(history_data) < 50: # 简单检查，至少需要少量数据
                    raise ValueError(f"历史数据不足 ({len(history_data)} 条)，无法执行冷热分析。请先更新数据。")
                
                processed_data = self._preprocess_data_for_analysis(history_data.copy(), lottery_type)
                if processed_data is None:
                    raise ValueError("准备分析数据时出错。")

                freq_analyzer = FrequencyAnalyzer(lottery_type)
                freq_results = freq_analyzer.analyze(processed_data)
                
                if not freq_results or not freq_results.get('success', False):
                    raise ValueError("频率分析未能生成有效结果。")
                
                generated_sets = generate_hot_cold_numbers(lottery_type, num_sets, freq_results)

        except Exception as e:
            error_msg = str(e)
        
        self.generation_queue.put((generated_sets, error_msg, lottery_type, strategy))

    def _background_smart_generation(self, lottery_type, num_sets):
        generated_sets = []
        error_msg = None
        try:
            # ------------------- 算法替换开始 -------------------
            # 1. 导入我们自己的生成器工厂
            from src.core.generators.factory import create_generator
            
            # 2. 创建我们全新的'smart'精英生成器
            smart_generator = create_generator('smart', lottery_type)
            
            # 3. 调用生成方法, 这将触发后台的"精英选拔"过程
            #    (后台日志会打印"正在进行..."信息)
            elite_numbers = smart_generator.generate(count=num_sets)
            
            # 4. 将新算法的输出格式适配到GUI期望的格式
            for num_obj in elite_numbers:
                if lottery_type == 'ssq':
                    generated_sets.append({'red': num_obj.red, 'blue': num_obj.blue})
                elif lottery_type == 'dlt':
                    generated_sets.append({'front': num_obj.front, 'back': num_obj.back})
            # ------------------- 算法替换结束 -------------------

        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()

        self.generation_queue.put((generated_sets, error_msg, lottery_type, "smart_recommend"))

    def _background_anti_popular_generation(self, lottery_type, num_sets, strategy):
        """去热门策略生成"""
        generated_sets = []
        error_msg = None
        try:
            from src.core.generators.smart_generator import SmartNumberGenerator

            # 创建智能生成器
            generator = SmartNumberGenerator(lottery_type)

            # 根据策略设置模式
            if strategy == "anti_popular_strict":
                mode = 'strict'
            elif strategy == "anti_popular_moderate":
                mode = 'moderate'
            elif strategy == "anti_popular_light":
                mode = 'light'
            else:  # hybrid_anti_popular
                mode = 'moderate'

            # 生成号码
            if strategy == "hybrid_anti_popular":
                # 混合模式：50%去热门 + 50%统计优选
                generator.set_anti_popular_config(enabled=True, mode=mode)
                elite_numbers = generator.generate_hybrid(num_sets, anti_popular_ratio=0.5)
            else:
                # 纯去热门模式
                generator.set_anti_popular_config(enabled=True, mode=mode)
                elite_numbers = generator.generate_anti_popular(num_sets)

            # 转换格式
            for num_obj in elite_numbers:
                if lottery_type == 'ssq':
                    generated_sets.append({'red': num_obj.red, 'blue': num_obj.blue})
                elif lottery_type == 'dlt':
                    generated_sets.append({'front': num_obj.front, 'back': num_obj.back})

        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback.print_exc()

        self.generation_queue.put((generated_sets, error_msg, lottery_type, strategy))

    def _check_generation_queue(self):
        try:
            message = self.generation_queue.get_nowait()
            generated_sets, error_msg, lottery_type, strategy = message

            if error_msg:
                messagebox.showerror("生成错误", error_msg)
                self._finalize_generation_ui()
                return

            display_text = f"为【{self.data_manager.LOTTERY_TYPES[lottery_type]}】生成 {len(generated_sets)} 注号码...\n"
            display_text += f"使用策略: {strategy}\n\n"

            if generated_sets:
                for i, nums in enumerate(generated_sets):
                    if lottery_type == 'ssq':
                        red_display = sorted([int(n) for n in nums['red']])
                        blue_display = int(nums['blue'])
                        formatted_nums = f"红球: {red_display} | 蓝球: {blue_display}"
                    elif lottery_type == 'dlt':
                        front_display = sorted([int(n) for n in nums['front']])
                        back_display = sorted([int(n) for n in nums['back']])
                        formatted_nums = f"前区: {front_display} | 后区: {back_display}"
                    else:
                        formatted_nums = str(nums)
                    display_text += f"第 {i+1} 注: {formatted_nums}\n"
            else:
                display_text += "未能生成号码。\n"

            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", display_text)
            self.result_text.config(state="disabled")

            self._finalize_generation_ui()

        except queue.Empty:
            pass
        finally:
            self.master.after(100, self._check_generation_queue)

    def _finalize_generation_ui(self):
        self.generate_button.config(text="生成号码", state=tk.NORMAL)
        self.is_generating = False

    def _preprocess_data_for_analysis(self, df: pd.DataFrame, lottery_type: str) -> Optional[pd.DataFrame]:
        """验证和准备用于分析的数据 (从 DataAnalysisFrame 借鉴并简化)"""
        try:
            required_num_cols = []
            if lottery_type == 'ssq':
                required_num_cols = ['red_numbers', 'blue_number']
            elif lottery_type == 'dlt':
                required_num_cols = ['front_numbers', 'back_numbers']
            else:
                return None

            missing_cols = [col for col in required_num_cols if col not in df.columns]
            if missing_cols:
                return None

            if lottery_type == 'ssq' and 'blue_number' in df.columns:
                sample_blue = df['blue_number'].iloc[0] if len(df) > 0 else None
                if not pd.api.types.is_list_like(sample_blue):
                    df.loc[:, 'blue_numbers'] = df['blue_number'].apply(lambda x: [x] if pd.notna(x) else [])
                    df = df.drop(columns=['blue_number'])
                elif 'blue_numbers' not in df.columns:
                    df = df.rename(columns={'blue_number': 'blue_numbers'})

            final_cols = []
            if lottery_type == 'ssq':
                final_cols = ['red_numbers', 'blue_numbers']
            elif lottery_type == 'dlt':
                final_cols = ['front_numbers', 'back_numbers']
            
            if not all(col in df.columns for col in final_cols):
                return None

            return df

        except Exception as e:
            print(f"[GUI预处理] 预处理数据时出错: {e}")
            return None 