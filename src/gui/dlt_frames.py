#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透界面组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Set
from ..core.generators.base_generator import RandomGenerator, LotteryNumber
from src.core.validators.number_validator import NumberValidator

class DLTComplexBetFrame(ttk.Frame):
    """大乐透复式投注界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.generator = RandomGenerator('dlt')
        self.selected_front = set()
        self.selected_back = set()
        self.validator = NumberValidator('dlt')
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 前区号码区域
        front_frame = ttk.LabelFrame(main_frame, text="前区号码")
        front_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建前区号码按钮
        self.front_buttons = {}
        for i in range(35):
            num = i + 1
            btn = ttk.Button(
                front_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_front_number(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.front_buttons[num] = btn
            
        # 后区号码区域
        back_frame = ttk.LabelFrame(main_frame, text="后区号码")
        back_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建后区号码按钮
        self.back_buttons = {}
        for i in range(12):
            num = i + 1
            btn = ttk.Button(
                back_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_back_number(x)
            )
            row = i // 6
            col = i % 6
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.back_buttons[num] = btn
            
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加控制按钮
        ttk.Button(
            control_frame,
            text="机选前区",
            command=self.random_front
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="机选后区",
            command=self.random_back
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="机选全部",
            command=self.random_all
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
        
        # 添加状态提示标签
        self.status_label = ttk.Label(main_frame, text="已选: 前区0/5, 后区0/2")
        self.status_label.pack(side=tk.BOTTOM, pady=5)
        
    def toggle_front_number(self, number: int):
        """切换前区号码选择状态"""
        if number in self.selected_front:
            self.selected_front.remove(number)
            self.front_buttons[number].configure(style='TButton')
        else:
            self.selected_front.add(number)
            self.front_buttons[number].configure(style='Selected.TButton')
        
        # 更新状态提示
        self.update_status_hint()

    def toggle_back_number(self, number: int):
        """切换后区号码选中状态"""
        if number in self.selected_back:
            self.selected_back.remove(number)
            self.back_buttons[number].configure(style='TButton')
        else:
            self.selected_back.add(number)
            self.back_buttons[number].configure(style='Selected.TButton')
            
    def random_front(self):
        """机选前区号码"""
        # 清空当前选择
        self.selected_front.clear()
        for btn in self.front_buttons.values():
            btn.configure(style='TButton')
            
        # 生成新号码
        numbers = self.generator.generate_single()
        front_numbers = numbers['front']
        
        # 更新选择状态
        for num in front_numbers:
            self.selected_front.add(num)
            self.front_buttons[num].configure(style='Selected.TButton')
            
    def random_back(self):
        """机选后区号码"""
        # 清空当前选择
        self.selected_back.clear()
        for btn in self.back_buttons.values():
            btn.configure(style='TButton')
            
        # 生成新号码
        numbers = self.generator.generate_single()
        back_numbers = numbers['back']
        
        # 更新选择状态
        for num in back_numbers:
            self.selected_back.add(num)
            self.back_buttons[num].configure(style='Selected.TButton')
            
    def random_all(self):
        """机选全部号码"""
        self.random_front()
        self.random_back()
        
    def validate_selection(self) -> bool:
        """验证所选号码是否有效"""
        numbers = {
            'front': sorted(list(self.selected_front)),
            'back': sorted(list(self.selected_back))
        }
        return self.generator.validate_numbers(numbers)
        
    def clear_front(self):
        """清空前区选号"""
        for num in self.selected_front.copy():
            self.toggle_front_number(num)
            
    def clear_back(self):
        """清空后区选号"""
        for num in self.selected_back.copy():
            self.toggle_back_number(num)
            
    def clear_all(self):
        """清空所有选号"""
        self.clear_front()
        self.clear_back()
        self.result_text.delete('1.0', tk.END)
        
    def validate_numbers(self):
        """验证选择的号码"""
        number = LotteryNumber(
            front=sorted(list(self.selected_front)),
            back=sorted(list(self.selected_back))
        )
        results = self.validator.validate(number)
        
        if not results['valid']:
            error_msgs = []
            if not results['front_count']:
                error_msgs.append("前区需要选择5个号码")
            if not results['back_count']:
                error_msgs.append("后区需要选择2个号码")
            if not results['front_sum']:
                error_msgs.append("前区号码和不在合理范围内")
            if not results['back_sum']:
                error_msgs.append("后区号码和不在合理范围内")
            if not results['duplicates']:
                error_msgs.append("存在重复号码")
                
            messagebox.showerror("验证失败", "\n".join(error_msgs))
            return False
        return True
    
    def calculate(self):
        """计算投注信息"""
        if not self.validate_numbers():
            return
        
        # 计算注数和金额
        from itertools import combinations
        front_count = len(list(combinations(self.selected_front, 5)))
        back_count = len(list(combinations(self.selected_back, 2)))
        total = front_count * back_count
        amount = total * 2
        
        # 显示结果
        result = f"已选号码:\n"
        result += f"前区: {sorted(self.selected_front)}\n"
        result += f"后区: {sorted(self.selected_back)}\n"
        result += f"共{total}注, 金额{amount}元"
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', result)

class DLTDantuoBetFrame:
    """大乐透胆拖投注界面"""
    
    def __init__(self, parent):
        self.parent = parent
        # 前区选号
        self.selected_front_dan: Set[int] = set()  # 前区胆码
        self.selected_front_tuo: Set[int] = set()  # 前区拖码
        # 后区选号
        self.selected_back_dan: Set[int] = set()   # 后区胆码
        self.selected_back_tuo: Set[int] = set()   # 后区拖码
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 前区胆码区域
        front_dan_frame = ttk.LabelFrame(main_frame, text="前区胆码(最多4个)")
        front_dan_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建前区胆码按钮
        self.front_dan_buttons = {}
        for i in range(35):
            num = i + 1
            btn = ttk.Button(
                front_dan_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_front_dan(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.front_dan_buttons[num] = btn
            
        # 前区拖码区域
        front_tuo_frame = ttk.LabelFrame(main_frame, text="前区拖码")
        front_tuo_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建前区拖码按钮
        self.front_tuo_buttons = {}
        for i in range(35):
            num = i + 1
            btn = ttk.Button(
                front_tuo_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_front_tuo(x)
            )
            row = i // 7
            col = i % 7
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.front_tuo_buttons[num] = btn
            
        # 后区胆码区域
        back_dan_frame = ttk.LabelFrame(main_frame, text="后区胆码(最多1个)")
        back_dan_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建后区胆码按钮
        self.back_dan_buttons = {}
        for i in range(12):
            num = i + 1
            btn = ttk.Button(
                back_dan_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_back_dan(x)
            )
            row = i // 6
            col = i % 6
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.back_dan_buttons[num] = btn
            
        # 后区拖码区域
        back_tuo_frame = ttk.LabelFrame(main_frame, text="后区拖码")
        back_tuo_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建后区拖码按钮
        self.back_tuo_buttons = {}
        for i in range(12):
            num = i + 1
            btn = ttk.Button(
                back_tuo_frame,
                text=str(num).zfill(2),
                width=4,
                command=lambda x=num: self.toggle_back_tuo(x)
            )
            row = i // 6
            col = i % 6
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.back_tuo_buttons[num] = btn
            
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加控制按钮
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
        
        self.result_text = tk.Text(result_frame, height=4, width=50)
        self.result_text.pack(fill=tk.X, padx=5, pady=5)
        
    def toggle_front_dan(self, number: int):
        """切换前区胆码选中状态"""
        if number in self.selected_front_dan:
            self.selected_front_dan.remove(number)
            self.front_dan_buttons[number].configure(style='TButton')
            # 如果拖码区已选中该号码,则取消选中
            if number in self.selected_front_tuo:
                self.toggle_front_tuo(number)
        else:
            if len(self.selected_front_dan) >= 4:
                messagebox.showwarning("提示", "前区胆码最多选择4个")
                return
            if number in self.selected_front_tuo:
                messagebox.showwarning("提示", "该号码已在拖码区选中")
                return
            self.selected_front_dan.add(number)
            self.front_dan_buttons[number].configure(style='Selected.TButton')
            
    def toggle_front_tuo(self, number: int):
        """切换前区拖码选中状态"""
        if number in self.selected_front_tuo:
            self.selected_front_tuo.remove(number)
            self.front_tuo_buttons[number].configure(style='TButton')
        else:
            if number in self.selected_front_dan:
                messagebox.showwarning("提示", "该号码已在胆码区选中")
                return
            self.selected_front_tuo.add(number)
            self.front_tuo_buttons[number].configure(style='Selected.TButton')
            
    def toggle_back_dan(self, number: int):
        """切换后区胆码选中状态"""
        if number in self.selected_back_dan:
            self.selected_back_dan.remove(number)
            self.back_dan_buttons[number].configure(style='TButton')
            # 如果拖码区已选中该号码,则取消选中
            if number in self.selected_back_tuo:
                self.toggle_back_tuo(number)
        else:
            if len(self.selected_back_dan) >= 1:
                messagebox.showwarning("提示", "后区胆码最多选择1个")
                return
            if number in self.selected_back_tuo:
                messagebox.showwarning("提示", "该号码已在拖码区选中")
                return
            self.selected_back_dan.add(number)
            self.back_dan_buttons[number].configure(style='Selected.TButton')
            
    def toggle_back_tuo(self, number: int):
        """切换后区拖码选中状态"""
        if number in self.selected_back_tuo:
            self.selected_back_tuo.remove(number)
            self.back_tuo_buttons[number].configure(style='TButton')
        else:
            if number in self.selected_back_dan:
                messagebox.showwarning("提示", "该号码已在胆码区选中")
                return
            self.selected_back_tuo.add(number)
            self.back_tuo_buttons[number].configure(style='Selected.TButton')
            
    def clear_all(self):
        """清空所有选号"""
        # 清空前区胆码
        for num in self.selected_front_dan.copy():
            self.toggle_front_dan(num)
        # 清空前区拖码    
        for num in self.selected_front_tuo.copy():
            self.toggle_front_tuo(num)
        # 清空后区胆码
        for num in self.selected_back_dan.copy():
            self.toggle_back_dan(num)
        # 清空后区拖码
        for num in self.selected_back_tuo.copy():
            self.toggle_back_tuo(num)
        # 清空结果显示
        self.result_text.delete('1.0', tk.END)
        
    def calculate(self):
        """计算投注信息"""
        # 验证选号是否符合规则
        if len(self.selected_front_dan) + len(self.selected_front_tuo) < 5:
            messagebox.showwarning("提示", "前区号码不足5个")
            return
        if len(self.selected_back_dan) + len(self.selected_back_tuo) < 2:
            messagebox.showwarning("提示", "后区号码不足2个")
            return
            
        # 计算注数和金额
        from itertools import combinations
        
        # 计算前区注数
        front_need = 5 - len(self.selected_front_dan)
        front_count = len(list(combinations(self.selected_front_tuo, front_need)))
        
        # 计算后区注数
        back_need = 2 - len(self.selected_back_dan)
        back_count = len(list(combinations(self.selected_back_tuo, back_need)))
        
        # 计算总注数和金额
        total = front_count * back_count
        amount = total * 2
        
        # 显示结果
        result = f"已选号码:\n"
        result += f"前区胆码: {sorted(self.selected_front_dan)}\n"
        result += f"前区拖码: {sorted(self.selected_front_tuo)}\n"
        result += f"后区胆码: {sorted(self.selected_back_dan)}\n"
        result += f"后区拖码: {sorted(self.selected_back_tuo)}\n"
        result += f"共{total}注, 金额{amount}元"
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', result)

class DLTHistoryFrame:
    """大乐透开奖历史界面"""
    
    def __init__(self, parent):
        self.parent = parent
        self.page = 1
        self.page_size = 50
        self.total_pages = 1
        self.current_data = []
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 搜索区域
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="期号:").pack(side=tk.LEFT, padx=5)
        self.draw_num_var = tk.StringVar()
        ttk.Entry(
            search_frame,
            textvariable=self.draw_num_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(search_frame, text="日期:").pack(side=tk.LEFT, padx=5)
        self.date_var = tk.StringVar()
        ttk.Entry(
            search_frame,
            textvariable=self.date_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            search_frame,
            text="搜索",
            command=self.search_history
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            search_frame,
            text="刷新",
            command=self.refresh_data
        ).pack(side=tk.LEFT, padx=5)
        
        # 数据显示区域
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ('draw_num', 'draw_date', 'front_numbers', 'back_numbers', 'prize_pool', 'sales')
        self.tree = ttk.Treeview(
            data_frame,
            columns=columns,
            show='headings',
            height=20
        )
        
        # 设置列标题
        self.tree.heading('draw_num', text='期号')
        self.tree.heading('draw_date', text='开奖日期')
        self.tree.heading('front_numbers', text='前区号码')
        self.tree.heading('back_numbers', text='后区号码')
        self.tree.heading('prize_pool', text='奖池(元)')
        self.tree.heading('sales', text='销量(元)')
        
        # 设置列宽度
        self.tree.column('draw_num', width=80)
        self.tree.column('draw_date', width=100)
        self.tree.column('front_numbers', width=150)
        self.tree.column('back_numbers', width=100)
        self.tree.column('prize_pool', width=100)
        self.tree.column('sales', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分页控制区域
        page_frame = ttk.Frame(main_frame)
        page_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            page_frame,
            text="上一页",
            command=self.prev_page
        ).pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(page_frame, text="第1页/共1页")
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            page_frame,
            text="下一页",
            command=self.next_page
        ).pack(side=tk.LEFT, padx=5)
        
        # 初始加载数据
        self.refresh_data()
        
    def format_number(self, number: int) -> str:
        """格式化数字为带逗号的字符串"""
        return "{:,}".format(number)
        
    def refresh_data(self):
        """刷新数据"""
        from ..core.data_fetcher import DLTDataFetcher
        fetcher = DLTDataFetcher()
        
        try:
            # 获取数据
            data = fetcher.fetch_history(page=self.page, page_size=self.page_size)
            self.current_data = data['items']
            self.total_pages = data['total_pages']
            
            # 更新表格
            self.update_table()
            # 更新分页信息
            self.update_page_info()
            
        except Exception as e:
            messagebox.showerror("错误", f"获取数据失败: {str(e)}")
            
    def update_table(self):
        """更新表格数据"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加新数据
        for item in self.current_data:
            front_numbers = ' '.join(str(x).zfill(2) for x in item['front_numbers'])
            back_numbers = ' '.join(str(x).zfill(2) for x in item['back_numbers'])
            
            self.tree.insert('', tk.END, values=(
                item['draw_num'],
                item['draw_date'],
                front_numbers,
                back_numbers,
                self.format_number(item['prize_pool']),
                self.format_number(item['sales'])
            ))
            
    def update_page_info(self):
        """更新分页信息"""
        self.page_label.config(text=f"第{self.page}页/共{self.total_pages}页")
        
    def prev_page(self):
        """上一页"""
        if self.page > 1:
            self.page -= 1
            self.refresh_data()
            
    def next_page(self):
        """下一页"""
        if self.page < self.total_pages:
            self.page += 1
            self.refresh_data()
            
    def search_history(self):
        """搜索历史数据"""
        draw_num = self.draw_num_var.get().strip()
        date = self.date_var.get().strip()
        
        if not draw_num and not date:
            messagebox.showwarning("提示", "请输入搜索条件")
            return
            
        from ..core.data_fetcher import DLTDataFetcher
        fetcher = DLTDataFetcher()
        
        try:
            # 获取搜索结果
            data = fetcher.search_history(draw_num=draw_num, draw_date=date)
            self.current_data = data['items']
            self.total_pages = 1
            self.page = 1
            
            # 更新显示
            self.update_table()
            self.update_page_info()
            
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {str(e)}")
