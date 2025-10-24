import tkinter as tk
from tkinter import ttk, messagebox
from src.core.strategy.number_generator import EnhancedNumberGenerator
from src.core.generators.base_generator import RandomGenerator
from src.core.generators.smart_generator import SmartNumberGenerator
from src.core.data_manager import LotteryDataManager
from src.core.models import SSQNumber

class NumberGeneratorFrame(ttk.Frame):
    """号码生成器界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = LotteryDataManager()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 彩种选择
        lottery_frame = ttk.LabelFrame(main_frame, text="彩种选择")
        lottery_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lottery_type = tk.StringVar(value="dlt")
        ttk.Radiobutton(
            lottery_frame,
            text="大乐透",
            variable=self.lottery_type,
            value="dlt",
            command=self._on_lottery_changed
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            lottery_frame,
            text="双色球",
            variable=self.lottery_type,
            value="ssq",
            command=self._on_lottery_changed
        ).pack(side=tk.LEFT, padx=10)
        
        # 生成参数设置
        params_frame = ttk.LabelFrame(main_frame, text="生成参数")
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 生成注数
        count_frame = ttk.Frame(params_frame)
        count_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(count_frame, text="生成注数:").pack(side=tk.LEFT)
        self.count_var = tk.StringVar(value="2")
        ttk.Entry(count_frame, textvariable=self.count_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 生成策略
        strategy_frame = ttk.Frame(params_frame)
        strategy_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(strategy_frame, text="生成策略:").pack(side=tk.LEFT)

        # 扩展策略选项 - (显示名称, 内部标识)
        self.strategies = [
            ("完全随机", "random"),
            ("平衡分布", "balanced"),
            ("热门号码", "hot"),
            ("冷门号码", "cold"),
            ("智能推荐", "smart"),
            ("去热门-严格", "anti_popular_strict"),
            ("去热门-适中", "anti_popular_moderate"),
            ("去热门-轻度", "anti_popular_light"),
            ("混合模式", "hybrid_anti_popular"),
            ("模式识别", "pattern"),
            ("频率分析", "frequency"),
            ("混合策略", "hybrid"),
            ("进化算法", "evolutionary"),
            ("最高评分（整注）", "top_scored")
        ]

        # 创建显示名称到内部标识的映射
        self.strategy_name_to_id = {name: id for name, id in self.strategies}
        self.strategy_id_to_name = {id: name for name, id in self.strategies}

        # 使用下拉框，显示中文名称
        self.strategy_display_var = tk.StringVar(value="完全随机")
        self.strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.strategy_display_var,
            values=[s[0] for s in self.strategies],  # 显示中文名称
            state='readonly',
            width=20
        )
        self.strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 添加高级参数框架
        advanced_frame = ttk.LabelFrame(params_frame, text="高级参数")
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 历史权重
        weight_frame = ttk.Frame(advanced_frame)
        weight_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(weight_frame, text="历史权重:").pack(side=tk.LEFT)
        self.history_weight = tk.StringVar(value="0.5")
        ttk.Entry(
            weight_frame,
            textvariable=self.history_weight,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        # 模式权重
        pattern_frame = ttk.Frame(advanced_frame)
        pattern_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(pattern_frame, text="模式权重:").pack(side=tk.LEFT)
        self.pattern_weight = tk.StringVar(value="0.3")
        ttk.Entry(
            pattern_frame,
            textvariable=self.pattern_weight,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        # 控制按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(
            btn_frame,
            text="生成号码",
            command=self._generate_numbers
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="清空结果",
            command=self._clear_results
        ).pack(side=tk.LEFT, padx=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(main_frame, text="生成结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建结果表格
        columns = ('序号', '号码', '评分')
        self.result_tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        # 设置列
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            result_frame,
            orient=tk.VERTICAL,
            command=self.result_tree.yview
        )
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _on_lottery_changed(self):
        """彩种改变时的处理"""
        self._clear_results()
        
    def _generate_numbers(self):
        """生成号码"""
        try:
            count = int(self.count_var.get())
            lottery_type = self.lottery_type.get()
            # 从显示名称获取内部标识
            strategy_display = self.strategy_display_var.get()
            strategy = self.strategy_name_to_id.get(strategy_display, "random")
            
            # 获取历史数据
            history_data = self.data_manager.get_recent_draws(100)
            
            if strategy in ['random']:
                # 使用基础随机生成器
                generator = RandomGenerator(lottery_type)
                numbers = [generator.generate_single(strategy=strategy) for _ in range(count)]

            elif strategy in ['balanced', 'hot', 'cold', 'smart']:
                # 使用改进的智能生成器
                generator = SmartNumberGenerator(lottery_type)

                # 根据策略调整算法配置
                if strategy == 'hot':
                    # 频率优先配置
                    generator.set_blue_algorithm_config(
                        method='enhanced',
                        weights={'frequency': 0.6, 'missing': 0.2, 'trend': 0.1, 'pattern': 0.05, 'random': 0.05}
                    )
                elif strategy == 'cold':
                    # 遗漏优先配置
                    generator.set_blue_algorithm_config(
                        method='enhanced',
                        weights={'frequency': 0.2, 'missing': 0.6, 'trend': 0.1, 'pattern': 0.05, 'random': 0.05}
                    )
                elif strategy == 'balanced':
                    # 平衡配置
                    generator.set_blue_algorithm_config(method='ensemble')

                # 生成号码
                smart_numbers = generator.generate_recommended(count)

            elif strategy in ['anti_popular_strict', 'anti_popular_moderate', 'anti_popular_light']:
                # 去热门模式
                generator = SmartNumberGenerator(lottery_type)

                # 根据策略设置模式
                if strategy == 'anti_popular_strict':
                    mode = 'strict'
                elif strategy == 'anti_popular_moderate':
                    mode = 'moderate'
                else:
                    mode = 'light'

                generator.set_anti_popular_config(enabled=True, mode=mode)
                smart_numbers = generator.generate_anti_popular(count)

            elif strategy == 'hybrid_anti_popular':
                # 混合模式：50%去热门 + 50%统计优选
                generator = SmartNumberGenerator(lottery_type)
                generator.set_anti_popular_config(enabled=True, mode='moderate')
                smart_numbers = generator.generate_hybrid(count, anti_popular_ratio=0.5)
                numbers = []
                for num in smart_numbers:
                    if lottery_type == 'ssq':
                        numbers.append({'red': num.red, 'blue': num.blue})
                    elif lottery_type == 'dlt':
                        numbers.append({'front': num.front, 'back': num.back})
            else:
                # 使用增强型生成器
                generator = EnhancedNumberGenerator(
                    lottery_type=lottery_type,
                    history_data=history_data
                )

                # 获取高级参数
                params = {
                    'history_weight': float(self.history_weight.get()),
                    'pattern_weight': float(self.pattern_weight.get())
                }

                # 生成号码
                numbers = generator.generate_with_strategy(
                    strategy=strategy,
                    count=count,
                    **params
                )
            
            # 清空现有结果
            self._clear_results()
            
            # 显示结果
            for i, number in enumerate(numbers, 1):
                if lottery_type == 'dlt':
                    number_str = (
                        f"前区: {' '.join(f'{n:02d}' for n in sorted(number.front))} "
                        f"后区: {' '.join(f'{n:02d}' for n in sorted(number.back))}"
                    )
                else:  # ssq
                    number_str = (
                        f"红球: {' '.join(f'{n:02d}' for n in sorted(number.red))} "
                        f"蓝球: {number.blue:02d}"
                    )
                
                self.result_tree.insert('', 'end', values=(
                    i,
                    number_str,
                    f"{getattr(number, 'score', 0):.2f}"
                ))
                
        except Exception as e:
            messagebox.showerror("错误", f"生成号码失败: {str(e)}")
            
    def _clear_results(self):
        """清空结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
