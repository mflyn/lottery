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
from src.gui.fusion_controls import FusionGenerationMixin
from src.core.generators.fusion.config import FusionConfig

if TYPE_CHECKING:
    from src.core.data_manager import LotteryDataManager
    from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame

class GenerationFrame(FusionGenerationMixin, ttk.Frame):
    """号码推荐功能框架"""
    def __init__(self, master: tk.Widget, data_manager: 'LotteryDataManager', analyzer=None, evaluation_frame: Optional['NumberEvaluationFrame']=None, **kwargs):
        """初始化号码推荐框架

        Args:
            master: 父窗口
            data_manager: 数据管理器
            analyzer: 分析器（已废弃，保留用于向后兼容）
            evaluation_frame: 号码评价页实例，用于读取评分配置
        """
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.analyzer = analyzer  # 保留用于向后兼容，但不再使用
        self.evaluation_frame = evaluation_frame  # 可选：号码评价页实例，用于读取评分配置
        self.generation_queue = queue.Queue()
        self.is_generating = False
        self._poll_id = None

        self.create_widgets()
        self._init_fusion()
        self._check_generation_queue()

    def create_widgets(self):
        """创建界面组件"""
        # --- 顶部配置区域 ---
        config_frame = ttk.LabelFrame(self, text="生成选项")
        self.config_frame = config_frame
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
            "混合模式": "hybrid_anti_popular",
            "最高评分（整注）": "top_scored",
            "融合推荐": "fusion"
        }
        # 搜索参数（仅对“最高评分（整注）”策略生效）
        self.periods_label = ttk.Label(config_frame, text="统计期数:")
        self.periods_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.periods_var = tk.IntVar(value=100)
        self.periods_spinbox = ttk.Spinbox(config_frame, from_=10, to=500, textvariable=self.periods_var, width=6)
        self.periods_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self.pool_size_label = ttk.Label(config_frame, text="候选池(红):")
        self.pool_size_label.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.pool_size_var = tk.IntVar(value=18)
        self.pool_size_spinbox = ttk.Spinbox(config_frame, from_=10, to=30, textvariable=self.pool_size_var, width=6)
        self.pool_size_spinbox.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        # 默认隐藏搜索参数（只在"最高评分（整注）"策略时显示）
        self._hide_search_params()

        self.strategy_var = tk.StringVar(value="统计优选") # 默认统计优选
        self.strategy_combo = ttk.Combobox(config_frame, textvariable=self.strategy_var, values=list(self.strategy_map.keys()), state="readonly", width=15)
        self.strategy_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        self.strategy_combo.bind("<<ComboboxSelected>>", self._on_strategy_change)

        # 评分参数显示区域（从评价页联动）
        self.scoring_info_label = ttk.Label(config_frame, text="", foreground='blue', font=('', 9))
        self.scoring_info_label.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="w")

        # --- 历史过滤设置 ---
        filter_frame = ttk.LabelFrame(config_frame, text="历史重复过滤")
        self.filter_frame = filter_frame
        filter_frame.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

        # 启用开关
        self.history_filter_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filter_frame,
            text="启用历史过滤",
            variable=self.history_filter_enabled_var,
            command=self._on_history_filter_toggle
        ).grid(row=0, column=0, padx=5, pady=2, sticky="w")

        # 检查期数
        ttk.Label(filter_frame, text="检查期数:").grid(row=0, column=1, padx=(15, 5), pady=2, sticky="w")
        self.filter_periods_var = tk.IntVar(value=100)
        self.filter_periods_spinbox = ttk.Spinbox(
            filter_frame, from_=30, to=500,
            textvariable=self.filter_periods_var, width=6
        )
        self.filter_periods_spinbox.grid(row=0, column=2, padx=5, pady=2, sticky="w")

        # 最大重复数
        ttk.Label(filter_frame, text="最大重复:").grid(row=0, column=3, padx=(15, 5), pady=2, sticky="w")
        self.max_overlap_var = tk.IntVar(value=4)
        self.max_overlap_spinbox = ttk.Spinbox(
            filter_frame, from_=2, to=5,
            textvariable=self.max_overlap_var, width=4
        )
        self.max_overlap_spinbox.grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # 提示文字
        self.filter_hint_label = ttk.Label(
            filter_frame,
            text="避免推荐号码与历史开奖重复过多",
            foreground='gray',
            font=('', 8)
        )
        self.filter_hint_label.grid(row=1, column=0, columnspan=5, padx=5, pady=(0, 2), sticky="w")

        # 生成按钮
        self.generate_button = ttk.Button(config_frame, text="生成号码", command=self.generate_numbers)
        self.generate_button.grid(row=6, column=0, columnspan=4, pady=10)

        # 进度/状态提示
        self.status_label = ttk.Label(config_frame, text="", foreground='green')
        self.status_label.grid(row=7, column=0, columnspan=4, pady=(0, 5))

        # --- 结果显示区域 ---
        result_frame = ttk.LabelFrame(self, text="推荐号码")
        self.result_frame = result_frame
        result_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.result_text = tk.Text(result_frame, wrap="word", height=15, state="disabled")
        self.result_text.pack(padx=5, pady=5, fill="both", expand=True)

    def _on_lottery_type_change(self):
        """切换彩票类型时的处理（例如，清空结果）"""
        self.clear_results()
        # 更新候选池标签文字
        self._update_pool_size_label()
        # 更新历史过滤的最大重复数默认值
        self._update_max_overlap_default()
        print(f"切换到彩票类型: {self.lottery_type_var.get()}")

    def _on_history_filter_toggle(self):
        """历史过滤开关切换"""
        enabled = self.history_filter_enabled_var.get()
        state = 'normal' if enabled else 'disabled'
        self.filter_periods_spinbox.config(state=state)
        self.max_overlap_spinbox.config(state=state)

    def _update_max_overlap_default(self):
        """根据彩票类型更新最大重复数默认值"""
        lottery_type = self.lottery_type_var.get()
        if lottery_type == 'ssq':
            self.max_overlap_var.set(4)  # SSQ红球6个，允许重复4个
        else:
            self.max_overlap_var.set(3)  # DLT前区5个，允许重复3个

    def _get_history_filter_config(self):
        """获取历史过滤配置"""
        return {
            'enabled': self.history_filter_enabled_var.get(),
            'check_periods': self.filter_periods_var.get(),
            'max_overlap': self.max_overlap_var.get()
        }

    def _on_strategy_change(self, event=None):
        """策略改变时更新评分参数显示和搜索参数可见性"""
        strategy = self.strategy_map.get(self.strategy_var.get())
        self._sync_fusion_visibility()
        if strategy == "top_scored":
            self._update_scoring_info_display()
            self._show_search_params()
        else:
            self.scoring_info_label.config(text="")
            self._hide_search_params()

    def _update_scoring_info_display(self):
        """更新评分参数显示（从评价页读取）"""
        self.scoring_info_label.config(text='按评价页六项权重计算单注融合 F；候选池内排序。')

    def _show_search_params(self):
        """显示搜索参数控件"""
        self.periods_label.grid()
        self.periods_spinbox.grid()
        self.pool_size_label.grid()
        self.pool_size_spinbox.grid()
        # 更新候选池标签文字
        self._update_pool_size_label()

    def _hide_search_params(self):
        """隐藏搜索参数控件"""
        self.periods_label.grid_remove()
        self.periods_spinbox.grid_remove()
        self.pool_size_label.grid_remove()
        self.pool_size_spinbox.grid_remove()

    def _update_pool_size_label(self):
        """根据彩票类型更新候选池标签文字"""
        lottery_type = self.lottery_type_var.get()
        if lottery_type == 'ssq':
            label_text = "候选池(红):"
        elif lottery_type == 'dlt':
            label_text = "候选池(前区):"
        else:
            label_text = "候选池:"
        self.pool_size_label.config(text=label_text)

    def clear_results(self):
        """清空结果显示区域"""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state="disabled")
        self._clear_fusion_result()

    def generate_numbers(self):
        """根据选定策略生成号码"""
        if self.is_generating:
            messagebox.showwarning("请稍候", "正在生成号码中，请勿重复操作。")
            return

        try:
            lottery_type = self.lottery_type_var.get()
            num_sets = self.num_sets_var.get()
            strategy_display_name = self.strategy_var.get()
            strategy = self.strategy_map.get(strategy_display_name, "random")
            fusion_request = self._read_fusion_request(lottery_type) if strategy == 'fusion' else None
            if fusion_request:
                num_sets = fusion_request[0]

            # Tk variables belong to the UI thread. Workers receive plain snapshots so
            # they can finish safely even if the window is closed before they start.
            filter_config = None
            if strategy == "smart_recommend" or strategy in ["anti_popular_strict", "anti_popular_moderate", "anti_popular_light", "hybrid_anti_popular"]:
                filter_config = self._get_history_filter_config()
            search_config = None
            if strategy == "top_scored":
                search_config = {
                    'periods': int(self.periods_var.get()),
                    'pool_size': int(self.pool_size_var.get()),
                    'scoring': self._get_fusion_scoring_config(),
                    'history_file': str(self.data_manager.data_files[lottery_type]),
                }
        except (tk.TclError, ValueError, TypeError) as exc:
            messagebox.showerror("输入错误", f"请检查注数、期数及策略参数。\n{exc}")
            return

        self.clear_results()
        self.is_generating = True
        self.generate_button.config(text="生成中...", state=tk.DISABLED)

        # 更新状态提示
        if strategy == "top_scored":
            self.status_label.config(text="正在搜索最高评分组合，请稍候...", foreground='orange')
        else:
            self.status_label.config(text="正在生成号码...", foreground='green')

        self.master.update_idletasks()

        display_text = f"正在为【{self.data_manager.LOTTERY_TYPES[lottery_type]}】生成 {num_sets} 注号码...\n"
        display_text += f"使用策略: {strategy}\n\n"
        self.result_text.config(state="normal")
        self.result_text.insert("1.0", display_text)
        self.result_text.config(state="disabled")

        if strategy == 'fusion':
            self._start_fusion(fusion_request)
        elif strategy == "smart_recommend":
            generation_thread = threading.Thread(target=self._background_smart_generation, args=(lottery_type, num_sets, filter_config), daemon=True)
            generation_thread.start()
        elif strategy in ["anti_popular_strict", "anti_popular_moderate", "anti_popular_light", "hybrid_anti_popular"]:
            # 去热门策略使用线程处理（可能较慢）
            generation_thread = threading.Thread(target=self._background_anti_popular_generation, args=(lottery_type, num_sets, strategy, filter_config), daemon=True)
            generation_thread.start()
        elif strategy == "top_scored":
            # 最高评分策略可能耗时，单独线程运行
            generation_thread = threading.Thread(target=self._background_top_scored_generation, args=(lottery_type, num_sets, search_config), daemon=True)
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

    def _background_smart_generation(self, lottery_type, num_sets, filter_config):
        generated_sets = []
        error_msg = None
        try:
            # ------------------- 算法替换开始 -------------------
            # 1. 导入我们自己的生成器工厂
            from src.core.generators.factory import create_generator

            # 2. 创建我们全新的'smart'精英生成器
            smart_generator = create_generator('smart', lottery_type)

            # 3. 配置历史过滤（如果启用）
            if filter_config['enabled']:
                # 设置过滤配置
                max_overlap_key = 'max_red_overlap' if lottery_type == 'ssq' else 'max_front_overlap'
                smart_generator.set_history_filter_config(
                    enabled=True,
                    check_periods=filter_config['check_periods'],
                    **{max_overlap_key: filter_config['max_overlap']}
                )
                print(f"📋 历史过滤已启用: 检查{filter_config['check_periods']}期, 最大重复{filter_config['max_overlap']}个")
            else:
                smart_generator.set_history_filter_enabled(False)
                print("📋 历史过滤已禁用")

            # 4. 调用生成方法, 这将触发后台的"精英选拔"过程
            #    (后台日志会打印"正在进行..."信息)
            elite_numbers = smart_generator.generate_recommended(
                count=num_sets,
                enable_history_filter=filter_config['enabled']
            )

            # 5. 将新算法的输出格式适配到GUI期望的格式
            for num_obj in elite_numbers:
                if lottery_type == 'ssq':
                    generated_sets.append({'red': num_obj.red, 'blue': num_obj.blue})
                elif lottery_type == 'dlt':
                    generated_sets.append({'front': num_obj.front, 'back': num_obj.back})
            # ------------------- 算法替换结束 -------------------

        except Exception as e:
            error_msg = str(e)

        self.generation_queue.put((generated_sets, error_msg, lottery_type, "smart_recommend"))

    def _background_anti_popular_generation(self, lottery_type, num_sets, strategy, filter_config):
        """去热门策略生成"""
        generated_sets = []
        error_msg = None
        try:
            from src.core.generators.smart_generator import SmartNumberGenerator

            # 创建智能生成器
            generator = SmartNumberGenerator(lottery_type)

            # 配置历史过滤
            if filter_config['enabled']:
                max_overlap_key = 'max_red_overlap' if lottery_type == 'ssq' else 'max_front_overlap'
                generator.set_history_filter_config(
                    enabled=True,
                    check_periods=filter_config['check_periods'],
                    **{max_overlap_key: filter_config['max_overlap']}
                )

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

            generated_sets = self._convert_lottery_numbers_for_display(lottery_type, elite_numbers)

        except Exception as e:
            error_msg = str(e)

        self.generation_queue.put((generated_sets, error_msg, lottery_type, strategy))


    def _convert_lottery_numbers_for_display(self, lottery_type, numbers):
        """将 LotteryNumber 对象列表转换为 GUI 可展示的字典结构"""
        converted = []
        for num in numbers or []:
            entry = {}
            if lottery_type == 'ssq':
                red = list(getattr(num, 'red', []))
                if not red and hasattr(num, 'numbers'):
                    red = list(getattr(num, 'numbers', [])[:-1])
                blue = getattr(num, 'blue', None)
                if blue is None and hasattr(num, 'numbers'):
                    seq = list(getattr(num, 'numbers', []))
                    if seq:
                        blue = seq[-1]
                if red:
                    entry['red'] = sorted(int(n) for n in red)
                if blue is not None:
                    entry['blue'] = int(blue)
            elif lottery_type == 'dlt':
                front = list(getattr(num, 'front', []))
                back = list(getattr(num, 'back', []))
                if (not front or not back) and hasattr(num, 'numbers'):
                    seq = list(getattr(num, 'numbers', []))
                    if len(seq) >= 7:
                        front = seq[:-2]
                        back = seq[-2:]
                if front:
                    entry['front'] = sorted(int(n) for n in front)
                if back:
                    entry['back'] = sorted(int(n) for n in back)
            else:
                entry['numbers'] = list(getattr(num, 'numbers', []))

            score = getattr(num, 'score', None)
            if isinstance(score, (int, float)) and score not in (0, 0.0):
                entry['score'] = score

            if entry:
                converted.append(entry)
        return converted


    def _get_fusion_scoring_config(self):
        periods=int(self.periods_var.get())
        if self.evaluation_frame is not None:
            return self.evaluation_frame.get_fusion_config(periods)
        return FusionConfig(history_periods=periods)

    def _background_top_scored_generation(self, lottery_type, num_sets, search_config):
        """最高评分（整注）策略：调用剪枝搜索返回评分最高的整注组合"""
        generated_sets = []
        error_msg = None
        try:
            periods = search_config['periods']
            pool_size = search_config['pool_size']

            if lottery_type == 'ssq':
                # 双色球
                from scripts.find_top_ssq import find_top_ssq
                
                cfg = search_config['scoring']
                
                results = find_top_ssq(
                    top_k=int(num_sets),
                    periods=periods,
                    pool_size=pool_size,
                    out_path=None,
                    config=cfg,
                    history_file=search_config['history_file'],
                )

                for item in results[:int(num_sets)]:
                    generated_sets.append({
                        'red': item['red_numbers'],
                        'blue': item['blue_number'],
                        'score': item.get('total_score'),
                        'random_reference': item.get('random_reference')
                    })
            
            elif lottery_type == 'dlt':
                # 大乐透
                from scripts.find_top_dlt import find_top_dlt
                
                results = find_top_dlt(
                    top_k=int(num_sets),
                    periods=periods,
                    pool_size=pool_size,
                    out_path=None,
                    config=search_config['scoring'],
                    history_file=search_config['history_file'],
                )

                for item in results[:int(num_sets)]:
                    generated_sets.append({
                        'front': item['front_numbers'],
                        'back': item['back_numbers'],
                        'score': item.get('total_score'),
                        'random_reference': item.get('random_reference')
                    })
            
            else:
                raise ValueError(f"最高评分策略不支持彩票类型: {lottery_type}")

        except Exception as e:
            error_msg = str(e)

        self.generation_queue.put((generated_sets, error_msg, lottery_type, "top_scored"))




    def _check_generation_queue(self):
        self._poll_id = None
        self._poll_fusion_progress()
        try:
            message = self.generation_queue.get_nowait()
            if isinstance(message, dict) and message.get('kind') == 'fusion':
                self._finish_fusion(message)
                return
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
                        formatted_nums = f"红球: {' '.join(f'{n:02d}' for n in red_display)} | 蓝球: {blue_display:02d}"
                        if isinstance(nums, dict) and 'score' in nums and nums['score'] is not None:
                            formatted_nums += f" | 融合 F: {nums['score']:.6f}"
                    elif lottery_type == 'dlt':
                        front_display = sorted([int(n) for n in nums['front']])
                        back_display = sorted([int(n) for n in nums['back']])
                        formatted_nums = f"前区: {' '.join(f'{n:02d}' for n in front_display)} | 后区: {' '.join(f'{n:02d}' for n in back_display)}"
                        if nums.get('score') is not None:
                            formatted_nums += f" | 融合 F: {nums['score']:.6f}"
                    else:
                        formatted_nums = str(nums)
                    if isinstance(nums,dict) and nums.get('random_reference') is not None:
                        formatted_nums += f" | 严格超过约 {nums['random_reference']['exceed_percent']:.1f}% 随机单注"
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
            if self.winfo_exists():
                self._poll_id = self.after(100, self._check_generation_queue)

    def destroy(self):
        self._fusion_stop.set()
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        super().destroy()

    def _finalize_generation_ui(self):
        self.generate_button.config(text="生成号码", state=tk.NORMAL)
        self.is_generating = False
        self.status_label.config(text="生成完成", foreground='green')

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
