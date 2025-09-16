#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球界面组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Set
from src.core.generators.base_generator import RandomGenerator, LotteryNumber
from src.core.validators.number_validator import NumberValidator
from src.core.ssq_analyzer import SSQAnalyzer

class SSQComplexBetFrame(ttk.Frame):
    """双色球复式投注界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.generator = RandomGenerator('ssq')
        self.selected_red = set()
        self.selected_blue = set()
        self.validator = NumberValidator('ssq')
        self.init_ui()
        
    def setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        
        # 普通按钮样式
        style.configure(
            "Ball.TButton",
            padding=5,
            width=6,
            font=("微软雅黑", 10)
        )
        
        # 选中的红球样式
        style.configure(
            "RedSelected.TButton",
            background="#ff4d4d",
            foreground="white",
            padding=5,
            width=6,
            font=("微软雅黑", 10, "bold")
        )
        
        # 选中的蓝球样式
        style.configure(
            "BlueSelected.TButton",
            background="#4d4dff",
            foreground="white",
            padding=5,
            width=6,
            font=("微软雅黑", 10, "bold")
        )
        
        # 标签框样式
        style.configure(
            "Title.TLabelframe",
            padding=10,
            font=("微软雅黑", 10)
        )
        
        # 结果文本框样式
        style.configure(
            "Result.TLabelframe",
            padding=10,
            font=("微软雅黑", 10)
        )
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 创建标题
        title = ttk.Label(
            main_frame,
            text="双色球复式投注",
            font=("微软雅黑", 14, "bold")
        )
        title.pack(pady=(0, 15))
        
        # 红球区域
        red_frame = ttk.LabelFrame(
            main_frame,
            text="红球号码（选6-20个）",
            style="Title.TLabelframe"
        )
        red_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建红球号码按钮网格
        red_grid = ttk.Frame(red_frame)
        red_grid.pack(padx=10, pady=10)
        
        self.red_buttons = {}
        for i in range(33):
            num = i + 1
            btn = ttk.Button(
                red_grid,
                text=str(num).zfill(2),
                style="Ball.TButton",
                command=lambda x=num: self.toggle_red_number(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=3, pady=3)
            self.red_buttons[num] = btn
            
        # 蓝球区域
        blue_frame = ttk.LabelFrame(
            main_frame,
            text="蓝球号码（选1-5个）",
            style="Title.TLabelframe"
        )
        blue_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建蓝球号码按钮网格
        blue_grid = ttk.Frame(blue_frame)
        blue_grid.pack(padx=10, pady=10)
        
        self.blue_buttons = {}
        for i in range(16):
            num = i + 1
            btn = ttk.Button(
                blue_grid,
                text=str(num).zfill(2),
                style="Ball.TButton",
                command=lambda x=num: self.toggle_blue_number(x)
            )
            row = i // 8
            col = i % 8
            btn.grid(row=row, column=col, padx=3, pady=3)
            self.blue_buttons[num] = btn
            
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # 左侧按钮组
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="机选红球",
            style="Ball.TButton",
            command=self.random_red
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            left_buttons,
            text="机选蓝球",
            style="Ball.TButton",
            command=self.random_blue
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            left_buttons,
            text="清空",
            style="Ball.TButton",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=5)
        
        # 右侧确定按钮
        ttk.Button(
            control_frame,
            text="确定",
            style="Ball.TButton",
            command=self.calculate
        ).pack(side=tk.RIGHT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(
            main_frame,
            text="投注信息",
            style="Result.TLabelframe"
        )
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.result_text = tk.Text(
            result_frame,
            height=4,
            font=("微软雅黑", 10),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.result_text.pack(fill=tk.X, padx=10, pady=10)
        
    def toggle_red_number(self, number: int):
        """切换红球号码选择状态"""
        if number in self.selected_red:
            self.selected_red.remove(number)
            self.red_buttons[number].configure(style='TButton')
        else:
            self.selected_red.add(number)
            self.red_buttons[number].configure(style='Selected.TButton')
        
        # 更新状态提示
        self.update_status_hint()

    def toggle_blue_number(self, number: int):
        """切换蓝球号码选中状态"""
        if number in self.selected_blue:
            self.selected_blue.remove(number)
            self.blue_buttons[number].configure(style="Ball.TButton")
        else:
            self.selected_blue.add(number)
            self.blue_buttons[number].configure(style="BlueSelected.TButton")
            
    def random_red(self):
        """机选红球号码"""
        # 清空当前选择
        self.selected_red.clear()
        for btn in self.red_buttons.values():
            btn.configure(style='TButton')
            
        # 生成新号码
        numbers = self.generator.generate_single()
        red_numbers = numbers['red']
        
        # 更新选择状态
        for num in red_numbers:
            self.selected_red.add(num)
            self.red_buttons[num].configure(style='Selected.TButton')
            
    def random_blue(self):
        """机选蓝球号码"""
        # 清空当前选择
        self.selected_blue.clear()
        for btn in self.blue_buttons.values():
            btn.configure(style='TButton')
            
        # 生成新号码
        numbers = self.generator.generate_single()
        blue_number = numbers['blue'][0]
        
        # 更新选择状态
        self.selected_blue.add(blue_number)
        self.blue_buttons[blue_number].configure(style='Selected.TButton')
        
    def random_all(self):
        """机选全部号码"""
        self.random_red()
        self.random_blue()
        
    def validate_numbers(self):
        """验证选择的号码"""
        number = LotteryNumber(
            red=sorted(list(self.selected_red)),
            blue=list(self.selected_blue)[0] if self.selected_blue else 0
        )
        results = self.validator.validate(number)
        
        if not results['valid']:
            error_msgs = []
            if not results['red_count']:
                error_msgs.append("需要选择6个红球号码")
            if not results['blue_range']:
                error_msgs.append("蓝球号码不在有效范围内")
            if not results['red_sum']:
                error_msgs.append("红球号码和不在合理范围内")
            if not results['duplicates']:
                error_msgs.append("红球存在重复号码")
                
            messagebox.showerror("验证失败", "\n".join(error_msgs))
            return False
        return True
        
    def clear_red(self):
        """清空红球选号"""
        for num in self.selected_red.copy():
            self.toggle_red_number(num)
            
    def clear_blue(self):
        """清空蓝球选号"""
        for num in self.selected_blue.copy():
            self.toggle_blue_number(num)
            
    def clear_all(self):
        """清空所有选号"""
        self.clear_red()
        self.clear_blue()
        self.result_text.delete('1.0', tk.END)
        
    def calculate(self):
        """计算投注信息"""
        if not self.validate_numbers():
            return
        
        # 计算注数和金额
        red_count = len(self.selected_red)
        blue_count = len(self.selected_blue)
        
        if self.lottery_type == 'ssq':
            bet_count = self._calculate_ssq_bets(red_count, blue_count)
        else:
            bet_count = self._calculate_dlt_bets(red_count, blue_count)
            
        amount = bet_count * 2  # 每注2元
        
        # 更新显示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, 
            f"红球: {sorted(list(self.selected_red))}\n"
            f"蓝球: {sorted(list(self.selected_blue))}\n"
            f"注数: {bet_count}\n"
            f"金额: {amount}元")

class SSQDantuoBetFrame:
    """双色球胆拖投注界面"""
    
    def __init__(self, parent):
        self.parent = parent
        # 红球选号
        self.selected_red_dan: Set[int] = set()  # 红球胆码
        self.selected_red_tuo: Set[int] = set()  # 红球拖码
        # 蓝球选号
        self.selected_blue: Set[int] = set()     # 蓝球号码
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 红球胆码区域
        red_dan_frame = ttk.LabelFrame(main_frame, text="红球胆码(最多5个)")
        red_dan_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建红球胆码按钮
        self.red_dan_buttons = {}
        for i in range(33):
            num = i + 1
            btn = ttk.Button(
                red_dan_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_red_dan(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.red_dan_buttons[num] = btn
            
        # 红球拖码区域
        red_tuo_frame = ttk.LabelFrame(main_frame, text="红球拖码")
        red_tuo_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建红球拖码按钮
        self.red_tuo_buttons = {}
        for i in range(33):
            num = i + 1
            btn = ttk.Button(
                red_tuo_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_red_tuo(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.red_tuo_buttons[num] = btn
            
        # 蓝球区域
        blue_frame = ttk.LabelFrame(main_frame, text="蓝球号码")
        blue_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建蓝球号码按钮
        self.blue_buttons = {}
        for i in range(16):
            num = i + 1
            btn = ttk.Button(
                blue_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_blue_number(x)
            )
            row = i // 8
            col = i % 8
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.blue_buttons[num] = btn
            
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加控制按钮
        ttk.Button(
            control_frame,
            text="机选红球",
            command=self.random_red
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="机选蓝球",
            command=self.random_blue
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="清空",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="确定",
            command=self.calculate
        ).pack(side=tk.RIGHT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="投注信息")
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.result_text = tk.Text(result_frame, height=3, width=50)
        self.result_text.pack(fill=tk.X, padx=5, pady=5)
        
    def toggle_red_dan(self, number: int):
        """切换红球胆码选中状态"""
        if number in self.selected_red_dan:
            self.selected_red_dan.remove(number)
            self.red_dan_buttons[number].configure(style='TButton')
        else:
            # 检查是否已经在拖码中选中
            if number in self.selected_red_tuo:
                return
            # 检查胆码数量是否超过限制
            if len(self.selected_red_dan) >= 5:
                messagebox.showwarning("提示", "红球胆码最多选择5个")
                return
            self.selected_red_dan.add(number)
            self.red_dan_buttons[number].configure(style='Selected.TButton')
            
    def toggle_red_tuo(self, number: int):
        """切换红球拖码选中状态"""
        if number in self.selected_red_tuo:
            self.selected_red_tuo.remove(number)
            self.red_tuo_buttons[number].configure(style='TButton')
        else:
            # 检查是否已经在胆码中选中
            if number in self.selected_red_dan:
                return
            self.selected_red_tuo.add(number)
            self.red_tuo_buttons[number].configure(style='Selected.TButton')
            
    def toggle_blue_number(self, number: int):
        """切换蓝球号码选中状态"""
        if number in self.selected_blue:
            self.selected_blue.remove(number)
            self.blue_buttons[number].configure(style='TButton')
        else:
            self.selected_blue.add(number)
            self.blue_buttons[number].configure(style='Selected.TButton')
            
    def random_red(self):
        """机选红球号码"""
        self.clear_red()
        import random
        # 随机选择胆码
        dan_count = random.randint(1, 5)
        dan_numbers = random.sample(range(1, 34), dan_count)
        for num in dan_numbers:
            self.toggle_red_dan(num)
        # 随机选择拖码
        available = set(range(1, 34)) - set(dan_numbers)
        tuo_count = random.randint(2, 6)
        tuo_numbers = random.sample(list(available), tuo_count)
        for num in tuo_numbers:
            self.toggle_red_tuo(num)
            
    def random_blue(self):
        """机选蓝球号码"""
        self.clear_blue()
        import random
        number = random.randint(1, 16)
        self.toggle_blue_number(number)
            
    def clear_red(self):
        """清空红球选号"""
        for num in self.selected_red_dan.copy():
            self.toggle_red_dan(num)
        for num in self.selected_red_tuo.copy():
            self.toggle_red_tuo(num)
            
    def clear_blue(self):
        """清空蓝球选号"""
        for num in self.selected_blue.copy():
            self.toggle_blue_number(num)
            
    def clear_all(self):
        """清空所有选号"""
        self.clear_red()
        self.clear_blue()
        self.result_text.delete('1.0', tk.END)
        
    def calculate(self):
        """计算投注信息"""
        dan_count = len(self.selected_red_dan)
        tuo_count = len(self.selected_red_tuo)
        
        # 验证胆码数量
        if dan_count == 0:
            messagebox.showwarning("提示", "至少选择1个胆码")
            return
        if dan_count > 5:
            messagebox.showwarning("提示", "最多选择5个胆码")
            return
            
        # 验证拖码数量
        if tuo_count == 0:
            messagebox.showwarning("提示", "至少选择1个拖码")
            return
            
        # 验证胆码+拖码总数
        total_red = dan_count + tuo_count
        if total_red < 7:
            messagebox.showwarning("提示", "胆码+拖码至少需要7个号码")
            return
            
        # 验证蓝球
        if len(self.selected_blue) == 0:
            messagebox.showwarning("提示", "至少选择1个蓝球")
            return
            
        # 计算注数和金额
        from itertools import combinations
        need_count = 6 - dan_count
        if need_count <= 0:
            total = 0
        else:
            total = len(list(combinations(self.selected_red_tuo, need_count)))
        total *= len(self.selected_blue)
        amount = total * 2
        
        # 显示结果
        result = "已选号码:\n"
        if self.selected_red_dan:
            result += f"红球胆码: {sorted(self.selected_red_dan)}\n"
        result += f"红球拖码: {sorted(self.selected_red_tuo)}\n"
        result += f"蓝球: {sorted(self.selected_blue)}\n"
        result += f"共{total}注, 金额{amount}元"
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', result)

class SSQHistoryFrame:
    """双色球开奖历史界面"""
    
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 期号选择
        ttk.Label(control_frame, text="期号:").pack(side=tk.LEFT, padx=5)
        self.issue_entry = ttk.Entry(control_frame, width=10)
        self.issue_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="查询",
            command=self.query_history
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="最近50期",
            command=lambda: self.query_history(50)
        ).pack(side=tk.LEFT, padx=5)
        
        # 历史数据表格
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ('期号', '开奖日期', '红球号码', '蓝球', '奖池(元)', '一等奖注数', '一等奖奖金')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 添加滚动条
        ysb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        # 放置表格和滚动条
        self.tree.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        
        # 配置grid权重
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 统计分析区域
        analysis_frame = ttk.LabelFrame(main_frame, text="统计分析")
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 红球出现频率
        red_freq_frame = ttk.Frame(analysis_frame)
        red_freq_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(red_freq_frame, text="红球出现频率:").pack(side=tk.LEFT)
        self.red_freq_text = tk.Text(red_freq_frame, height=2, width=50)
        self.red_freq_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 蓝球出现频率
        blue_freq_frame = ttk.Frame(analysis_frame)
        blue_freq_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(blue_freq_frame, text="蓝球出现频率:").pack(side=tk.LEFT)
        self.blue_freq_text = tk.Text(blue_freq_frame, height=2, width=50)
        self.blue_freq_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
    def query_history(self, count: int = None):
        """查询历史开奖数据"""
        try:
            # 获取数据
            analyzer = SSQAnalyzer()
            data = analyzer.data_fetcher.fetch_history(count)
            
            # 清空表格
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 更新表格
            for item in data:
                values = (
                    item['code'],
                    item['date'],
                    item['red'],
                    item['blue'],
                    item['poolmoney'],
                    item['prizegrades'][0]['typenum'],
                    item['prizegrades'][0]['typemoney']
                )
                self.tree.insert('', 'end', values=values)
                
            # 更新统计信息
            self.update_statistics(data)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取数据失败: {e}")
            
    def update_statistics(self, data: List[dict]):
        """更新统计信息"""
        # 分析频率
        analyzer = SSQAnalyzer()
        red_freq, blue_freq = analyzer.analyze_frequency(data)
        
        # 显示红球频率
        red_text = "红球出现次数(前10): "
        for num, count in sorted(red_freq.items(), key=lambda x: (-x[1], x[0]))[:10]:
            red_text += f"{num}({count}次) "
        self.red_freq_text.delete('1.0', tk.END)
        self.red_freq_text.insert('1.0', red_text)
        
        # 显示蓝球频率
        blue_text = "蓝球出现次数: "
        for num, count in sorted(blue_freq.items()):
            blue_text += f"{num}({count}次) "
        self.blue_freq_text.delete('1.0', tk.END)
        self.blue_freq_text.insert('1.0', blue_text)

class SSQWinningFrame:
    """双色球中奖计算界面"""
    
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 开奖号码输入区域
        winning_frame = ttk.LabelFrame(main_frame, text="开奖号码")
        winning_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 红球输入
        red_frame = ttk.Frame(winning_frame)
        red_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(red_frame, text="红球:").pack(side=tk.LEFT)
        self.red_entry = ttk.Entry(red_frame, width=30)
        self.red_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(red_frame, text="(用空格分隔)").pack(side=tk.LEFT)
        
        # 蓝球输入
        blue_frame = ttk.Frame(winning_frame)
        blue_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(blue_frame, text="蓝球:").pack(side=tk.LEFT)
        self.blue_entry = ttk.Entry(blue_frame, width=10)
        self.blue_entry.pack(side=tk.LEFT, padx=5)
        
        # 投注号码输入区域
        bet_frame = ttk.LabelFrame(main_frame, text="投注号码")
        bet_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 投注号码文本框
        self.bet_text = tk.Text(bet_frame, height=10)
        self.bet_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(bet_frame, text="每注号码占一行，红球用空格分隔，最后一个为蓝球").pack()
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="清空",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="计算",
            command=self.calculate
        ).pack(side=tk.RIGHT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="中奖结果")
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.result_text = tk.Text(result_frame, height=5)
        self.result_text.pack(fill=tk.X, padx=5, pady=5)
        
    def clear_all(self):
        """清空所有输入"""
        self.red_entry.delete(0, tk.END)
        self.blue_entry.delete(0, tk.END)
        self.bet_text.delete('1.0', tk.END)
        self.result_text.delete('1.0', tk.END)
        
    def calculate(self):
        """计算中奖结果"""
        try:
            # 获取开奖号码
            red_text = self.red_entry.get().strip()
            blue_text = self.blue_entry.get().strip()
            
            if not red_text or not blue_text:
                messagebox.showwarning("提示", "请输入开奖号码")
                return
                
            # 解析开奖号码
            winning_red = [int(x) for x in red_text.split()]
            winning_blue = int(blue_text)
            
            if len(winning_red) != 6:
                messagebox.showwarning("提示", "红球号码必须是6个")
                return
                
            # 获取投注号码
            bet_text = self.bet_text.get('1.0', tk.END).strip()
            if not bet_text:
                messagebox.showwarning("提示", "请输入投注号码")
                return
                
            # 解析投注号码
            bet_numbers = []
            for line in bet_text.split('\n'):
                if not line.strip():
                    continue
                numbers = [int(x) for x in line.split()]
                if len(numbers) != 7:
                    messagebox.showwarning("提示", "每注必须是6个红球+1个蓝球")
                    return
                bet_numbers.append((numbers[:6], numbers[6]))
                
            # 计算中奖
            analyzer = SSQAnalyzer()
            results = analyzer.check_prize(bet_numbers, (winning_red, winning_blue))
            
            # 显示结果
            if not results:
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', "未中奖")
                return
                
            # 显示中奖结果
            prize_names = {
                1: "一等奖",
                2: "二等奖",
                3: "三等奖",
                4: "四等奖",
                5: "五等奖",
                6: "六等奖"
            }
            
            result = "中奖结果:\n"
            for level, count in sorted(results):
                result += f"{prize_names[level]}: {count}注\n"
                
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', result)
            
        except ValueError:
            messagebox.showerror("错误", "号码格式错误")
        except Exception as e:
            messagebox.showerror("错误", f"计算出错: {e}")
