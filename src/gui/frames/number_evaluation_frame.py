#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
号码评价GUI框架
提供双色球和大乐透号码评价功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import random
from datetime import datetime
from typing import Dict, List, Any

from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator


class NumberEvaluationFrame(ttk.Frame):
    """号码评价框架"""
    
    def __init__(self, master, data_manager=None):
        """初始化号码评价框架
        
        Args:
            master: 父窗口
            data_manager: 数据管理器（可选）
        """
        super().__init__(master)
        self.data_manager = data_manager
        
        # 创建评价器
        try:
            self.ssq_evaluator = SSQNumberEvaluator()
            self.dlt_evaluator = DLTNumberEvaluator()
        except Exception as e:
            messagebox.showerror("初始化错误", f"评价器初始化失败: {str(e)}")
            self.ssq_evaluator = None
            self.dlt_evaluator = None
        
        # 当前评价结果
        self.current_result = None
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 彩种选择
        self._create_lottery_type_selector(main_container)
        
        # 2. 号码输入
        self._create_number_input_area(main_container)
        
        # 3. 评价结果
        self._create_result_display_area(main_container)
        
        # 4. 详细分析
        self._create_detail_analysis_area(main_container)
        
        # 5. 操作按钮
        self._create_action_buttons(main_container)
    
    def _create_lottery_type_selector(self, parent):
        """创建彩种选择器"""
        frame = ttk.LabelFrame(parent, text="彩种选择", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.lottery_type_var = tk.StringVar(value='ssq')
        
        ttk.Radiobutton(
            frame, 
            text="双色球 (6红+1蓝)", 
            variable=self.lottery_type_var, 
            value='ssq',
            command=self._on_lottery_type_changed
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Radiobutton(
            frame, 
            text="大乐透 (5前+2后)", 
            variable=self.lottery_type_var, 
            value='dlt',
            command=self._on_lottery_type_changed
        ).pack(side=tk.LEFT, padx=20)
    
    def _create_number_input_area(self, parent):
        """创建号码输入区"""
        frame = ttk.LabelFrame(parent, text="号码输入", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # 双色球输入框架
        self.ssq_input_frame = ttk.Frame(frame)
        
        # 红球输入
        red_frame = ttk.Frame(self.ssq_input_frame)
        red_frame.pack(fill=tk.X, pady=5)
        ttk.Label(red_frame, text="红球:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.ssq_red_entry = ttk.Entry(red_frame, width=50)
        self.ssq_red_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(red_frame, text="(6个号码，空格分隔，如: 03 09 16 17 24 33)", 
                 foreground='gray').pack(side=tk.LEFT)
        
        # 蓝球输入
        blue_frame = ttk.Frame(self.ssq_input_frame)
        blue_frame.pack(fill=tk.X, pady=5)
        ttk.Label(blue_frame, text="蓝球:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.ssq_blue_entry = ttk.Entry(blue_frame, width=10)
        self.ssq_blue_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(blue_frame, text="(1个号码，如: 15)", 
                 foreground='gray').pack(side=tk.LEFT)
        
        # 大乐透输入框架
        self.dlt_input_frame = ttk.Frame(frame)
        
        # 前区输入
        front_frame = ttk.Frame(self.dlt_input_frame)
        front_frame.pack(fill=tk.X, pady=5)
        ttk.Label(front_frame, text="前区:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.dlt_front_entry = ttk.Entry(front_frame, width=50)
        self.dlt_front_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(front_frame, text="(5个号码，空格分隔，如: 01 05 12 23 35)", 
                 foreground='gray').pack(side=tk.LEFT)
        
        # 后区输入
        back_frame = ttk.Frame(self.dlt_input_frame)
        back_frame.pack(fill=tk.X, pady=5)
        ttk.Label(back_frame, text="后区:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.dlt_back_entry = ttk.Entry(back_frame, width=20)
        self.dlt_back_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(back_frame, text="(2个号码，空格分隔，如: 03 11)", 
                 foreground='gray').pack(side=tk.LEFT)
        
        # 默认显示双色球输入
        self.ssq_input_frame.pack(fill=tk.X)
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="清空", command=self._clear_input, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="随机生成", command=self._random_numbers, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="评价号码", command=self._evaluate_numbers, width=15).pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(btn_frame, text="", foreground='blue')
        self.status_label.pack(side=tk.LEFT, padx=20)
    
    def _create_result_display_area(self, parent):
        """创建结果显示区"""
        frame = ttk.LabelFrame(parent, text="评价结果", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左侧：综合得分
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(left_frame, text="综合得分", font=('Arial', 12, 'bold')).pack()
        
        score_frame = ttk.Frame(left_frame)
        score_frame.pack(pady=10)
        
        self.total_score_label = ttk.Label(
            score_frame, 
            text="--", 
            font=('Arial', 48, 'bold'), 
            foreground='#28a745'
        )
        self.total_score_label.pack()
        
        ttk.Label(score_frame, text="/100", font=('Arial', 16)).pack()
        
        self.rating_label = ttk.Label(left_frame, text="", font=('Arial', 14))
        self.rating_label.pack()
        
        self.stars_label = ttk.Label(left_frame, text="", font=('Arial', 20))
        self.stars_label.pack()
        
        # 右侧：各维度得分
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        ttk.Label(right_frame, text="各维度得分", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        self.dimension_labels = {}
        dimensions = [
            ('频率得分', 'frequency'),
            ('遗漏得分', 'missing'),
            ('模式得分', 'pattern'),
            ('独特性得分', 'uniqueness')
        ]
        
        for dim_name, dim_key in dimensions:
            dim_frame = ttk.Frame(right_frame)
            dim_frame.pack(fill=tk.X, pady=3)
            
            ttk.Label(dim_frame, text=f"{dim_name}:", width=12, font=('Arial', 10)).pack(side=tk.LEFT)
            
            # 进度条
            progress = ttk.Progressbar(dim_frame, length=200, mode='determinate')
            progress.pack(side=tk.LEFT, padx=5)
            
            # 分数标签
            label = ttk.Label(dim_frame, text="--", width=15, font=('Arial', 10, 'bold'))
            label.pack(side=tk.LEFT, padx=5)
            
            # 图标标签
            icon_label = ttk.Label(dim_frame, text="", font=('Arial', 12))
            icon_label.pack(side=tk.LEFT)
            
            self.dimension_labels[dim_key] = {
                'progress': progress,
                'label': label,
                'icon': icon_label
            }
    
    def _create_detail_analysis_area(self, parent):
        """创建详细分析区"""
        frame = ttk.LabelFrame(parent, text="详细分析", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建标签页
        self.detail_notebook = ttk.Notebook(frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 各个分析标签页
        self.freq_text = self._create_text_tab(self.detail_notebook, "频率分析")
        self.missing_text = self._create_text_tab(self.detail_notebook, "遗漏分析")
        self.pattern_text = self._create_text_tab(self.detail_notebook, "模式分析")
        self.historical_text = self._create_text_tab(self.detail_notebook, "历史对比")
        self.suggestion_text = self._create_text_tab(self.detail_notebook, "专家建议")
    
    def _create_text_tab(self, notebook, title):
        """创建文本标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10), 
                      padx=10, pady=10, relief=tk.FLAT, bg='#f8f9fa')
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
        
        # 设置为只读
        text.configure(state=tk.DISABLED)
        
        return text
    
    def _create_action_buttons(self, parent):
        """创建操作按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X)
        
        ttk.Button(frame, text="导出报告", command=self._export_report, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="保存号码", command=self._save_numbers, width=15).pack(side=tk.LEFT, padx=5)
        
        # 右侧提示
        ttk.Label(frame, text="⚠️ 本评价仅基于历史统计，不代表中奖概率 | 理性购彩，量力而行", 
                 foreground='gray', font=('Arial', 9)).pack(side=tk.RIGHT, padx=10)
    
    def _on_lottery_type_changed(self):
        """彩种切换"""
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            self.dlt_input_frame.pack_forget()
            self.ssq_input_frame.pack(fill=tk.X)
        else:
            self.ssq_input_frame.pack_forget()
            self.dlt_input_frame.pack(fill=tk.X)
        
        # 清空结果
        self._clear_results()
    
    def _clear_input(self):
        """清空输入"""
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            self.ssq_red_entry.delete(0, tk.END)
            self.ssq_blue_entry.delete(0, tk.END)
        else:
            self.dlt_front_entry.delete(0, tk.END)
            self.dlt_back_entry.delete(0, tk.END)
        
        self.status_label.config(text="")
    
    def _random_numbers(self):
        """随机生成号码"""
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            # 双色球：6红+1蓝
            red = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)
            
            self.ssq_red_entry.delete(0, tk.END)
            self.ssq_red_entry.insert(0, ' '.join(f'{n:02d}' for n in red))
            
            self.ssq_blue_entry.delete(0, tk.END)
            self.ssq_blue_entry.insert(0, f'{blue:02d}')
        else:
            # 大乐透：5前+2后
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            
            self.dlt_front_entry.delete(0, tk.END)
            self.dlt_front_entry.insert(0, ' '.join(f'{n:02d}' for n in front))
            
            self.dlt_back_entry.delete(0, tk.END)
            self.dlt_back_entry.insert(0, ' '.join(f'{n:02d}' for n in back))
        
        self.status_label.config(text="✓ 已生成随机号码", foreground='green')

    def _evaluate_numbers(self):
        """评价号码"""
        try:
            lottery_type = self.lottery_type_var.get()

            if lottery_type == 'ssq':
                self._evaluate_ssq()
            else:
                self._evaluate_dlt()

        except ValueError as e:
            messagebox.showwarning("输入错误", str(e))
        except Exception as e:
            messagebox.showerror("评价失败", f"评价过程中出现错误:\n{str(e)}")

    def _evaluate_ssq(self):
        """评价双色球号码"""
        # 获取输入
        red_text = self.ssq_red_entry.get().strip()
        blue_text = self.ssq_blue_entry.get().strip()

        if not red_text or not blue_text:
            raise ValueError("请输入完整的号码")

        # 解析号码
        try:
            red_numbers = [int(x) for x in red_text.split()]
            blue_number = int(blue_text)
        except ValueError:
            raise ValueError("请输入有效的数字")

        # 验证
        if len(red_numbers) != 6:
            raise ValueError("红球必须是6个号码")

        if len(set(red_numbers)) != 6:
            raise ValueError("红球号码不能重复")

        if not all(1 <= n <= 33 for n in red_numbers):
            raise ValueError("红球号码范围: 01-33")

        if not (1 <= blue_number <= 16):
            raise ValueError("蓝球号码范围: 01-16")

        # 检查评价器
        if self.ssq_evaluator is None:
            raise Exception("双色球评价器未初始化")

        # 异步评价
        self._evaluate_async('ssq', red_numbers, blue_number)

    def _evaluate_dlt(self):
        """评价大乐透号码"""
        # 获取输入
        front_text = self.dlt_front_entry.get().strip()
        back_text = self.dlt_back_entry.get().strip()

        if not front_text or not back_text:
            raise ValueError("请输入完整的号码")

        # 解析号码
        try:
            front_numbers = [int(x) for x in front_text.split()]
            back_numbers = [int(x) for x in back_text.split()]
        except ValueError:
            raise ValueError("请输入有效的数字")

        # 验证
        if len(front_numbers) != 5:
            raise ValueError("前区必须是5个号码")

        if len(back_numbers) != 2:
            raise ValueError("后区必须是2个号码")

        if len(set(front_numbers)) != 5:
            raise ValueError("前区号码不能重复")

        if len(set(back_numbers)) != 2:
            raise ValueError("后区号码不能重复")

        if not all(1 <= n <= 35 for n in front_numbers):
            raise ValueError("前区号码范围: 01-35")

        if not all(1 <= n <= 12 for n in back_numbers):
            raise ValueError("后区号码范围: 01-12")

        # 检查评价器
        if self.dlt_evaluator is None:
            raise Exception("大乐透评价器未初始化")

        # 异步评价
        self._evaluate_async('dlt', front_numbers, back_numbers)

    def _evaluate_async(self, lottery_type, *numbers):
        """异步评价号码"""
        # 显示进度
        self.status_label.config(text="⏳ 正在评价中...", foreground='blue')
        self.total_score_label.config(text="--")
        self.rating_label.config(text="评价中...")
        self.stars_label.config(text="")

        # 清空详细分析
        self._clear_detail_texts()

        def do_evaluate():
            try:
                # 调用评价器
                if lottery_type == 'ssq':
                    result = self.ssq_evaluator.evaluate(*numbers)
                else:
                    result = self.dlt_evaluator.evaluate(*numbers)

                # 保存结果
                self.current_result = {
                    'lottery_type': lottery_type,
                    'numbers': numbers,
                    'result': result,
                    'timestamp': datetime.now()
                }

                # 更新UI（必须在主线程）
                self.after(0, lambda: self._update_result_display(result))
                self.after(0, lambda: self.status_label.config(text="✓ 评价完成", foreground='green'))

            except Exception as e:
                self.after(0, lambda: self.status_label.config(text=f"✗ 评价失败: {str(e)}", foreground='red'))
                self.after(0, lambda: messagebox.showerror("评价失败", f"评价过程中出现错误:\n{str(e)}"))

        # 启动线程
        thread = threading.Thread(target=do_evaluate, daemon=True)
        thread.start()

    def _update_result_display(self, result: Dict[str, Any]):
        """更新结果显示"""
        # 更新综合得分
        total_score = result['total_score']
        self.total_score_label.config(text=f"{total_score:.1f}")

        # 根据得分设置颜色
        if total_score >= 90:
            color = '#28a745'  # 绿色
        elif total_score >= 80:
            color = '#007bff'  # 蓝色
        elif total_score >= 70:
            color = '#ffc107'  # 黄色
        elif total_score >= 60:
            color = '#fd7e14'  # 橙色
        else:
            color = '#dc3545'  # 红色

        self.total_score_label.config(foreground=color)

        # 更新评级和星级
        self.rating_label.config(text=result['rating'])
        self.stars_label.config(text=result['stars'])

        # 更新各维度得分
        scores = result['scores']
        for dim_key, widgets in self.dimension_labels.items():
            score = scores[dim_key]

            # 更新进度条
            widgets['progress']['value'] = score

            # 更新分数标签
            widgets['label'].config(text=f"{score:.1f}/100")

            # 更新图标
            icon = self._get_score_icon(score)
            widgets['icon'].config(text=icon)

        # 更新详细分析
        self._update_detail_analysis(result)

    def _get_score_icon(self, score: float) -> str:
        """根据得分获取图标"""
        if score >= 90:
            return '✅'
        elif score >= 80:
            return '✅'
        elif score >= 70:
            return '✓'
        elif score >= 60:
            return '⚠️'
        else:
            return '❌'

    def _update_detail_analysis(self, result: Dict[str, Any]):
        """更新详细分析"""
        lottery_type = self.lottery_type_var.get()

        # 1. 频率分析
        freq_text = self._format_frequency_analysis(result['frequency'], lottery_type)
        self._set_text_content(self.freq_text, freq_text)

        # 2. 遗漏分析
        missing_text = self._format_missing_analysis(result['missing'], lottery_type)
        self._set_text_content(self.missing_text, missing_text)

        # 3. 模式分析
        pattern_text = self._format_pattern_analysis(result['pattern'], lottery_type)
        self._set_text_content(self.pattern_text, pattern_text)

        # 4. 历史对比
        historical_text = self._format_historical_analysis(result['historical'])
        self._set_text_content(self.historical_text, historical_text)

        # 5. 专家建议
        suggestion_text = self._format_suggestions(result['suggestions'])
        self._set_text_content(self.suggestion_text, suggestion_text)

    def _format_frequency_analysis(self, freq_data: Dict, lottery_type: str) -> str:
        """格式化频率分析"""
        lines = []
        lines.append("=" * 80)
        lines.append("频率分析（基于最近100期）")
        lines.append("=" * 80)
        lines.append("")

        if lottery_type == 'ssq':
            # 双色球
            lines.append("【红球频率】")
            lines.append("-" * 80)
            for detail in freq_data['red_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"出现 {detail['frequency']:2d} 次 "
                    f"(理论 {detail['theoretical']:.1f} 次, "
                    f"偏差 {detail['deviation']:+.1f}%) - "
                    f"{detail['classification']}"
                )

            lines.append("")
            lines.append("【蓝球频率】")
            lines.append("-" * 80)
            detail = freq_data['blue_detail']
            lines.append(
                f"  {detail['icon']} 号码 {detail['number']:02d}: "
                f"出现 {detail['frequency']:2d} 次 "
                f"(理论 {detail['theoretical']:.1f} 次, "
                f"偏差 {detail['deviation']:+.1f}%) - "
                f"{detail['classification']}"
            )
        else:
            # 大乐透
            lines.append("【前区频率】")
            lines.append("-" * 80)
            for detail in freq_data['front_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"出现 {detail['frequency']:2d} 次 "
                    f"(理论 {detail['theoretical']:.1f} 次, "
                    f"偏差 {detail['deviation']:+.1f}%) - "
                    f"{detail['classification']}"
                )

            lines.append("")
            lines.append("【后区频率】")
            lines.append("-" * 80)
            for detail in freq_data['back_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"出现 {detail['frequency']:2d} 次 "
                    f"(理论 {detail['theoretical']:.1f} 次, "
                    f"偏差 {detail['deviation']:+.1f}%) - "
                    f"{detail['classification']}"
                )

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_missing_analysis(self, missing_data: Dict, lottery_type: str) -> str:
        """格式化遗漏分析"""
        lines = []
        lines.append("=" * 80)
        lines.append("遗漏分析（当前遗漏期数）")
        lines.append("=" * 80)
        lines.append("")

        if lottery_type == 'ssq':
            # 双色球
            lines.append("【红球遗漏】")
            lines.append("-" * 80)
            for detail in missing_data['red_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"遗漏 {detail['missing']:3d} 期 - "
                    f"{detail['classification']}"
                )

            avg_missing = sum(d['missing'] for d in missing_data['red_details']) / len(missing_data['red_details'])
            lines.append(f"\n  平均遗漏: {avg_missing:.1f} 期")

            lines.append("")
            lines.append("【蓝球遗漏】")
            lines.append("-" * 80)
            detail = missing_data['blue_detail']
            lines.append(
                f"  {detail['icon']} 号码 {detail['number']:02d}: "
                f"遗漏 {detail['missing']:3d} 期 - "
                f"{detail['classification']}"
            )
        else:
            # 大乐透
            lines.append("【前区遗漏】")
            lines.append("-" * 80)
            for detail in missing_data['front_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"遗漏 {detail['missing']:3d} 期 - "
                    f"{detail['classification']}"
                )

            avg_missing = sum(d['missing'] for d in missing_data['front_details']) / len(missing_data['front_details'])
            lines.append(f"\n  平均遗漏: {avg_missing:.1f} 期")

            lines.append("")
            lines.append("【后区遗漏】")
            lines.append("-" * 80)
            for detail in missing_data['back_details']:
                lines.append(
                    f"  {detail['icon']} 号码 {detail['number']:02d}: "
                    f"遗漏 {detail['missing']:3d} 期 - "
                    f"{detail['classification']}"
                )

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_pattern_analysis(self, pattern_data: Dict, lottery_type: str) -> str:
        """格式化模式分析"""
        lines = []
        lines.append("=" * 80)
        lines.append("模式分析")
        lines.append("=" * 80)
        lines.append("")

        if lottery_type == 'ssq':
            # 双色球
            lines.append("【红球模式】")
            lines.append("-" * 80)

            # 奇偶比
            odd_even = pattern_data['odd_even']
            lines.append(f"\n• 奇偶比: {odd_even['ratio']}")
            lines.append(f"  {odd_even['icon']} {odd_even['rating']}")

            # 大小比
            big_small = pattern_data['big_small']
            lines.append(f"\n• 大小比: {big_small['ratio']}")
            lines.append(f"  {big_small['icon']} {big_small['rating']}")

            # 区间分布
            zone = pattern_data['zone']
            lines.append(f"\n• 区间分布: {zone['distribution']}")
            lines.append(f"  (区间1: 01-11, 区间2: 12-22, 区间3: 23-33)")
            lines.append(f"  {zone['icon']} {zone['rating']}")

            # 连号
            consecutive = pattern_data['consecutive']
            lines.append(f"\n• 连号: {consecutive['count']} 组")
            if consecutive['pairs']:
                for pair in consecutive['pairs']:
                    lines.append(f"  - {pair[0]:02d}-{pair[1]:02d}")
            lines.append(f"  {consecutive['icon']} {consecutive['rating']}")

            # 和值
            sum_val = pattern_data['sum']
            lines.append(f"\n• 和值: {sum_val['value']}")
            lines.append(f"  {sum_val['icon']} {sum_val['rating']}")

            # 跨度
            span = pattern_data['span']
            lines.append(f"\n• 跨度: {span['value']}")
            lines.append(f"  {span['icon']} {span['rating']}")

            # AC值
            ac = pattern_data['ac_value']
            lines.append(f"\n• AC值: {ac['value']}")
            lines.append(f"  {ac['icon']} {ac['rating']}")
        else:
            # 大乐透
            front = pattern_data['front']

            lines.append("【前区模式】")
            lines.append("-" * 80)

            # 奇偶比
            lines.append(f"\n• 奇偶比: {front['odd_even']['ratio']}")
            lines.append(f"  {front['odd_even']['icon']} {front['odd_even']['rating']}")

            # 大小比
            lines.append(f"\n• 大小比: {front['big_small']['ratio']}")
            lines.append(f"  {front['big_small']['icon']} {front['big_small']['rating']}")

            # 区间分布
            lines.append(f"\n• 区间分布: {front['zone']['distribution']}")
            lines.append(f"  (区间1: 01-12, 区间2: 13-24, 区间3: 25-35)")
            lines.append(f"  {front['zone']['icon']} {front['zone']['rating']}")

            # 连号
            lines.append(f"\n• 连号: {front['consecutive']['count']} 组")
            if front['consecutive']['pairs']:
                for pair in front['consecutive']['pairs']:
                    lines.append(f"  - {pair[0]:02d}-{pair[1]:02d}")
            lines.append(f"  {front['consecutive']['icon']} {front['consecutive']['rating']}")

            # 和值
            lines.append(f"\n• 和值: {front['sum']['value']}")
            lines.append(f"  {front['sum']['icon']} {front['sum']['rating']}")

            # 跨度
            lines.append(f"\n• 跨度: {front['span']['value']}")
            lines.append(f"  {front['span']['icon']} {front['span']['rating']}")

            # AC值
            lines.append(f"\n• AC值: {front['ac_value']['value']}")
            lines.append(f"  {front['ac_value']['icon']} {front['ac_value']['rating']}")

            # 后区
            back = pattern_data['back']
            lines.append("")
            lines.append("【后区模式】")
            lines.append("-" * 80)
            lines.append(f"\n• 奇偶比: {back['odd_even']['ratio']}")
            lines.append(f"  {back['odd_even']['icon']} {back['odd_even']['rating']}")

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_historical_analysis(self, historical_data: Dict) -> str:
        """格式化历史对比"""
        lines = []
        lines.append("=" * 80)
        lines.append("历史对比")
        lines.append("=" * 80)
        lines.append("")

        # 完全匹配
        if historical_data['exact_match']:
            lines.append(f"⚠️  警告: 这注号码在历史上完全出现过！")
            lines.append(f"   期号: {historical_data['exact_match_period']}")
            lines.append("")
        else:
            lines.append("✅ 这注号码从未完全出现过")
            lines.append("")

        # 匹配统计
        lines.append("【匹配统计】")
        lines.append("-" * 80)

        if 'max_red_match' in historical_data:
            # 双色球
            lines.append(f"• 红球最大匹配数: {historical_data['max_red_match']} 个")
            if historical_data['max_match_period']:
                lines.append(f"  期号: {historical_data['max_match_period']}")
            lines.append(f"• 红球平均匹配数: {historical_data['avg_red_match']:.2f} 个")
            lines.append(f"• 蓝球历史出现: {historical_data['blue_appearance']} 次")
        else:
            # 大乐透
            lines.append(f"• 前区最大匹配数: {historical_data['max_front_match']} 个")
            lines.append(f"• 后区最大匹配数: {historical_data['max_back_match']} 个")
            lines.append(f"• 总最大匹配数: {historical_data['max_total_match']} 个")
            if historical_data['max_match_period']:
                lines.append(f"  期号: {historical_data['max_match_period']}")
            lines.append(f"• 前区平均匹配数: {historical_data['avg_front_match']:.2f} 个")
            lines.append(f"• 后区平均匹配数: {historical_data['avg_back_match']:.2f} 个")

        lines.append("")
        lines.append("【独特性评价】")
        lines.append("-" * 80)
        lines.append(f"{historical_data['icon']} {historical_data['rating']}")

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_suggestions(self, suggestions: List[str]) -> str:
        """格式化专家建议"""
        lines = []
        lines.append("=" * 80)
        lines.append("专家建议")
        lines.append("=" * 80)
        lines.append("")

        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"{i}. {suggestion}")

        lines.append("")
        lines.append("=" * 80)
        lines.append("⚠️  重要提醒:")
        lines.append("=" * 80)
        lines.append("• 本评价仅基于历史统计数据，不代表中奖概率")
        lines.append("• 每期开奖都是独立随机事件，过往数据不影响未来结果")
        lines.append("• 彩票是娱乐方式，不是投资手段")
        lines.append("• 理性购彩，量力而行")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _set_text_content(self, text_widget, content: str):
        """设置文本框内容"""
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', content)
        text_widget.configure(state=tk.DISABLED)

    def _clear_results(self):
        """清空结果显示"""
        self.total_score_label.config(text="--", foreground='#28a745')
        self.rating_label.config(text="")
        self.stars_label.config(text="")

        for widgets in self.dimension_labels.values():
            widgets['progress']['value'] = 0
            widgets['label'].config(text="--")
            widgets['icon'].config(text="")

        self._clear_detail_texts()
        self.current_result = None

    def _clear_detail_texts(self):
        """清空详细分析文本"""
        for text_widget in [self.freq_text, self.missing_text, self.pattern_text,
                           self.historical_text, self.suggestion_text]:
            self._set_text_content(text_widget, "")

    def _export_report(self):
        """导出评价报告"""
        if self.current_result is None:
            messagebox.showinfo("提示", "请先评价号码")
            return

        try:
            # 选择保存路径
            filename = filedialog.asksaveasfilename(
                title="导出评价报告",
                defaultextension=".md",
                filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"号码评价报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

            if not filename:
                return

            # 生成报告内容
            report = self._generate_report()

            # 保存文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)

            messagebox.showinfo("成功", f"报告已导出到:\n{filename}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告时出现错误:\n{str(e)}")

    def _generate_report(self) -> str:
        """生成评价报告"""
        result = self.current_result
        lottery_type = result['lottery_type']
        numbers = result['numbers']
        eval_result = result['result']
        timestamp = result['timestamp']

        lines = []
        lines.append("# 彩票号码评价报告")
        lines.append("")
        lines.append(f"**生成时间**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 待评价号码
        lines.append("## 待评价号码")
        lines.append("")
        if lottery_type == 'ssq':
            lines.append(f"**彩种**: 双色球")
            lines.append(f"**红球**: {' '.join(f'{n:02d}' for n in numbers[0])}")
            lines.append(f"**蓝球**: {numbers[1]:02d}")
        else:
            lines.append(f"**彩种**: 大乐透")
            lines.append(f"**前区**: {' '.join(f'{n:02d}' for n in numbers[0])}")
            lines.append(f"**后区**: {' '.join(f'{n:02d}' for n in numbers[1])}")
        lines.append("")

        # 综合评分
        lines.append("## 综合评分")
        lines.append("")
        lines.append(f"**总分**: {eval_result['total_score']:.1f}/100")
        lines.append(f"**评级**: {eval_result['rating']} {eval_result['stars']}")
        lines.append("")

        # 各维度得分
        lines.append("### 各维度得分")
        lines.append("")
        scores = eval_result['scores']
        lines.append(f"- **频率得分**: {scores['frequency']:.1f}/100")
        lines.append(f"- **遗漏得分**: {scores['missing']:.1f}/100")
        lines.append(f"- **模式得分**: {scores['pattern']:.1f}/100")
        lines.append(f"- **独特性得分**: {scores['uniqueness']:.1f}/100")
        lines.append("")

        # 详细分析
        lines.append("## 详细分析")
        lines.append("")

        lines.append("### 1. 频率分析")
        lines.append("```")
        lines.append(self._format_frequency_analysis(eval_result['frequency'], lottery_type))
        lines.append("```")
        lines.append("")

        lines.append("### 2. 遗漏分析")
        lines.append("```")
        lines.append(self._format_missing_analysis(eval_result['missing'], lottery_type))
        lines.append("```")
        lines.append("")

        lines.append("### 3. 模式分析")
        lines.append("```")
        lines.append(self._format_pattern_analysis(eval_result['pattern'], lottery_type))
        lines.append("```")
        lines.append("")

        lines.append("### 4. 历史对比")
        lines.append("```")
        lines.append(self._format_historical_analysis(eval_result['historical']))
        lines.append("```")
        lines.append("")

        lines.append("### 5. 专家建议")
        lines.append("")
        for i, suggestion in enumerate(eval_result['suggestions'], 1):
            lines.append(f"{i}. {suggestion}")
        lines.append("")

        # 免责声明
        lines.append("---")
        lines.append("")
        lines.append("## ⚠️ 重要提醒")
        lines.append("")
        lines.append("- 本评价仅基于历史统计数据，不代表中奖概率")
        lines.append("- 每期开奖都是独立随机事件，过往数据不影响未来结果")
        lines.append("- 彩票是娱乐方式，不是投资手段")
        lines.append("- 理性购彩，量力而行")
        lines.append("")

        return "\n".join(lines)

    def _save_numbers(self):
        """保存号码到收藏"""
        if self.current_result is None:
            messagebox.showinfo("提示", "请先评价号码")
            return

        # TODO: 实现保存到收藏功能
        messagebox.showinfo("提示", "保存功能开发中...\n\n您可以使用\"导出报告\"功能保存评价结果。")

