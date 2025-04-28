#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透计算器GUI版 - 参考中国体彩网官方计算器功能
https://www.lottery.gov.cn/tool/dltjsq.jspx/

功能：
1. 计算复式投注的注数和金额
2. 计算胆拖投注的注数和金额
3. 计算中奖情况和奖金
"""

import math
import itertools
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple, Dict, Optional

# 导入命令行版本的计算器核心类
from dlt_calculator import DLTCalculator

# 导入开奖数据获取模块
from dlt_api_fetcher import DLTApiFetcher


class DLTCalculatorGUI:
    """大乐透计算器GUI类"""

    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.calculator = DLTCalculator()
        self.data_fetcher = DLTApiFetcher()  # 创建 API 数据获取器

        # 设置窗口
        self.root.title("大乐透计算器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个标签页
        self.create_complex_bet_tab()
        self.create_dantuo_bet_tab()
        self.create_complex_win_tab()
        self.create_dantuo_win_tab()

        # 设置样式
        self.setup_styles()

    def setup_styles(self):
        """设置控件样式"""
        style = ttk.Style()
        style.configure("TLabel", font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10))
        style.configure("TEntry", font=("微软雅黑", 10))
        style.configure("TNotebook", font=("微软雅黑", 10))
        style.configure("TNotebook.Tab", font=("微软雅黑", 10))
        style.configure("TFrame", background="#f0f0f0")

    def create_complex_bet_tab(self):
        """创建复式投注标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="复式投注计算")

        # 创建控件
        ttk.Label(tab, text="复式投注注数计算", font=("微软雅黑", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(tab, text="前区选号个数 (5-35):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_front_count = ttk.Entry(tab, width=10)
        self.complex_front_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.complex_front_count.insert(0, "6")

        ttk.Label(tab, text="后区选号个数 (2-12):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_back_count = ttk.Entry(tab, width=10)
        self.complex_back_count.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        self.complex_back_count.insert(0, "2")

        self.complex_additional = tk.BooleanVar()
        ttk.Checkbutton(tab, text="追加投注", variable=self.complex_additional).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        ttk.Button(tab, text="计算", command=self.calculate_complex_bet).grid(row=4, column=0, columnspan=2, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="计算结果")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(result_frame, text="注数:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_bet_count = ttk.Label(result_frame, text="0")
        self.complex_bet_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(result_frame, text="金额:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_bet_amount = ttk.Label(result_frame, text="0元")
        self.complex_bet_amount.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

    def create_dantuo_bet_tab(self):
        """创建胆拖投注标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="胆拖投注计算")

        # 创建控件
        ttk.Label(tab, text="胆拖投注注数计算", font=("微软雅黑", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(tab, text="前区胆码个数 (0-4):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_front_dan_count = ttk.Entry(tab, width=10)
        self.dantuo_front_dan_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_front_dan_count.insert(0, "1")

        ttk.Label(tab, text="前区拖码个数:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_front_tuo_count = ttk.Entry(tab, width=10)
        self.dantuo_front_tuo_count.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_front_tuo_count.insert(0, "5")

        ttk.Label(tab, text="后区胆码个数 (0-1):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_back_dan_count = ttk.Entry(tab, width=10)
        self.dantuo_back_dan_count.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_back_dan_count.insert(0, "0")

        ttk.Label(tab, text="后区拖码个数:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_back_tuo_count = ttk.Entry(tab, width=10)
        self.dantuo_back_tuo_count.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_back_tuo_count.insert(0, "3")

        self.dantuo_additional = tk.BooleanVar()
        ttk.Checkbutton(tab, text="追加投注", variable=self.dantuo_additional).grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        ttk.Button(tab, text="计算", command=self.calculate_dantuo_bet).grid(row=6, column=0, columnspan=2, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="计算结果")
        result_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(result_frame, text="注数:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_bet_count = ttk.Label(result_frame, text="0")
        self.dantuo_bet_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(result_frame, text="金额:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_bet_amount = ttk.Label(result_frame, text="0元")
        self.dantuo_bet_amount.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

    def create_complex_win_tab(self):
        """创建复式投注中奖计算标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="复式中奖计算")

        # 创建控件
        ttk.Label(tab, text="复式投注中奖计算", font=("微软雅黑", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

        # 投注号码输入区域
        bet_frame = ttk.LabelFrame(tab, text="投注号码")
        bet_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(bet_frame, text="前区号码 (用空格分隔，如：1 3 5 7 9 11):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_front_numbers = ttk.Entry(bet_frame, width=40)
        self.complex_win_front_numbers.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="后区号码 (用空格分隔，如：2 4 6):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_back_numbers = ttk.Entry(bet_frame, width=40)
        self.complex_win_back_numbers.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        # 开奖号码输入区域
        draw_frame = ttk.LabelFrame(tab, text="开奖号码")
        draw_frame.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 添加期号输入和获取按钮
        ttk.Label(draw_frame, text="期号 (如：21001):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_term = ttk.Entry(draw_frame, width=10)
        self.complex_win_term.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Button(draw_frame, text="获取开奖号码", command=self.fetch_draw_numbers_for_complex).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(draw_frame, text="获取最新开奖", command=self.fetch_latest_draw_for_complex).grid(row=0, column=3, padx=10, pady=5)

        ttk.Label(draw_frame, text="前区号码 (用空格分隔，如：1 3 5 7 9):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_draw_front = ttk.Entry(draw_frame, width=40)
        self.complex_win_draw_front.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        ttk.Label(draw_frame, text="后区号码 (用空格分隔，如：2 4):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_draw_back = ttk.Entry(draw_frame, width=40)
        self.complex_win_draw_back.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        # 追加投注选项
        self.complex_win_additional = tk.BooleanVar()
        ttk.Checkbutton(tab, text="追加投注", variable=self.complex_win_additional).grid(row=3, column=0, columnspan=4, sticky=tk.W, padx=10, pady=5)

        # 计算按钮
        ttk.Button(tab, text="计算中奖", command=self.calculate_complex_win).grid(row=4, column=0, columnspan=4, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="中奖结果")
        result_frame.grid(row=5, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 创建结果显示的文本框
        self.complex_win_result = tk.Text(result_frame, width=60, height=10, wrap=tk.WORD)
        self.complex_win_result.grid(row=0, column=0, padx=10, pady=10)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.complex_win_result.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.complex_win_result.config(yscrollcommand=scrollbar.set)

    def create_dantuo_win_tab(self):
        """创建胆拖投注中奖计算标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="胆拖中奖计算")

        # 创建控件
        ttk.Label(tab, text="胆拖投注中奖计算", font=("微软雅黑", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

        # 投注号码输入区域
        bet_frame = ttk.LabelFrame(tab, text="投注号码")
        bet_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(bet_frame, text="前区胆码 (用空格分隔，如：1 3):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_front_dan = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_front_dan.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="前区拖码 (用空格分隔，如：5 7 9 11):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_front_tuo = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_front_tuo.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="后区胆码 (用空格分隔，如：2):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_back_dan = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_back_dan.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="后区拖码 (用空格分隔，如：4 6):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_back_tuo = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_back_tuo.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)

        # 开奖号码输入区域
        draw_frame = ttk.LabelFrame(tab, text="开奖号码")
        draw_frame.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 添加期号输入和获取按钮
        ttk.Label(draw_frame, text="期号 (如：21001):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_term = ttk.Entry(draw_frame, width=10)
        self.dantuo_win_term.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Button(draw_frame, text="获取开奖号码", command=self.fetch_draw_numbers_for_dantuo).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(draw_frame, text="获取最新开奖", command=self.fetch_latest_draw_for_dantuo).grid(row=0, column=3, padx=10, pady=5)

        ttk.Label(draw_frame, text="前区号码 (用空格分隔，如：1 3 5 7 9):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_draw_front = ttk.Entry(draw_frame, width=40)
        self.dantuo_win_draw_front.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        ttk.Label(draw_frame, text="后区号码 (用空格分隔，如：2 4):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_draw_back = ttk.Entry(draw_frame, width=40)
        self.dantuo_win_draw_back.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        # 追加投注选项
        self.dantuo_win_additional = tk.BooleanVar()
        ttk.Checkbutton(tab, text="追加投注", variable=self.dantuo_win_additional).grid(row=3, column=0, columnspan=4, sticky=tk.W, padx=10, pady=5)

        # 计算按钮
        ttk.Button(tab, text="计算中奖", command=self.calculate_dantuo_win).grid(row=4, column=0, columnspan=4, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="中奖结果")
        result_frame.grid(row=5, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 创建结果显示的文本框
        self.dantuo_win_result = tk.Text(result_frame, width=60, height=10, wrap=tk.WORD)
        self.dantuo_win_result.grid(row=0, column=0, padx=10, pady=10)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.dantuo_win_result.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.dantuo_win_result.config(yscrollcommand=scrollbar.set)

    def calculate_complex_bet(self):
        """计算复式投注注数和金额"""
        try:
            front_count = int(self.complex_front_count.get())
            back_count = int(self.complex_back_count.get())

            bet_count = self.calculator.calculate_complex_bet_count(front_count, back_count)

            if bet_count == 0:
                messagebox.showerror("输入错误", "请检查输入！前区至少选5个号码，后区至少选2个号码。")
                return

            is_additional = self.complex_additional.get()
            bet_amount = self.calculator.calculate_bet_amount(bet_count, is_additional)

            self.complex_bet_count.config(text=str(bet_count))
            self.complex_bet_amount.config(text=f"{bet_amount}元")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")

    def calculate_dantuo_bet(self):
        """计算胆拖投注注数和金额"""
        try:
            front_dan_count = int(self.dantuo_front_dan_count.get())
            front_tuo_count = int(self.dantuo_front_tuo_count.get())
            back_dan_count = int(self.dantuo_back_dan_count.get())
            back_tuo_count = int(self.dantuo_back_tuo_count.get())

            bet_count = self.calculator.calculate_dantuo_bet_count(
                front_dan_count, front_tuo_count, back_dan_count, back_tuo_count
            )

            if bet_count == 0:
                messagebox.showerror("输入错误", "请检查输入！前区胆码不超过4个，后区胆码不超过1个，且胆码+拖码数量要满足投注条件。")
                return

            is_additional = self.dantuo_additional.get()
            bet_amount = self.calculator.calculate_bet_amount(bet_count, is_additional)

            self.dantuo_bet_count.config(text=str(bet_count))
            self.dantuo_bet_amount.config(text=f"{bet_amount}元")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")

    def calculate_complex_win(self):
        """计算复式投注中奖情况"""
        try:
            # 获取投注号码
            front_numbers_str = self.complex_win_front_numbers.get().strip()
            back_numbers_str = self.complex_win_back_numbers.get().strip()

            if not front_numbers_str or not back_numbers_str:
                messagebox.showerror("输入错误", "请输入投注号码！")
                return

            front_numbers = [int(x) for x in front_numbers_str.split()]
            back_numbers = [int(x) for x in back_numbers_str.split()]

            # 获取开奖号码
            draw_front_str = self.complex_win_draw_front.get().strip()
            draw_back_str = self.complex_win_draw_back.get().strip()

            if not draw_front_str or not draw_back_str:
                messagebox.showerror("输入错误", "请输入开奖号码！")
                return

            draw_front = [int(x) for x in draw_front_str.split()]
            draw_back = [int(x) for x in draw_back_str.split()]

            # 验证号码
            if len(draw_front) != 5 or len(draw_back) != 2:
                messagebox.showerror("输入错误", "开奖号码格式错误！前区应为5个号码，后区应为2个号码。")
                return

            if len(front_numbers) < 5 or len(back_numbers) < 2:
                messagebox.showerror("输入错误", "投注号码格式错误！前区至少选择5个号码，后区至少选择2个号码。")
                return

            # 计算中奖情况
            is_additional = self.complex_win_additional.get()
            result = self.calculator.calculate_complex_win(
                front_numbers, back_numbers, (draw_front, draw_back), is_additional
            )

            # 生成结果文本
            win_result = "复式投注中奖结果：\n\n"
            win_result += f"投注号码：前区 {', '.join(map(str, front_numbers))}，后区 {', '.join(map(str, back_numbers))}\n"
            win_result += f"开奖号码：前区 {', '.join(map(str, draw_front))}，后区 {', '.join(map(str, draw_back))}\n"
            win_result += f"总注数：{result['bet_count']}注\n"
            win_result += f"投注金额：{result['bet_amount']}元\n\n"

            # 添加中奖明细
            has_prize = False
            for level in range(1, 10):
                if result['prize_stats'][level] > 0:
                    has_prize = True
                    win_result += f"{level}等奖：{result['prize_stats'][level]}注\n"

            if not has_prize:
                win_result += "很遗憾，本次投注未中奖。\n"
            else:
                win_result += f"\n总中奖金额：{result['total_prize']}元\n"
                win_result += f"净收益：{result['net_win']}元\n"

            # 显示结果
            self.complex_win_result.delete(1.0, tk.END)
            self.complex_win_result.insert(tk.END, win_result)

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")

    def calculate_dantuo_win(self):
        """计算胆拖投注中奖情况"""
        try:
            # 获取投注号码
            front_dan_str = self.dantuo_win_front_dan.get().strip()
            front_tuo_str = self.dantuo_win_front_tuo.get().strip()
            back_dan_str = self.dantuo_win_back_dan.get().strip()
            back_tuo_str = self.dantuo_win_back_tuo.get().strip()

            # 允许胆码为空，但拖码不能为空
            if not front_tuo_str or not back_tuo_str:
                messagebox.showerror("输入错误", "请至少输入前区和后区的拖码！")
                return

            front_dan = [int(x) for x in front_dan_str.split()] if front_dan_str else []
            front_tuo = [int(x) for x in front_tuo_str.split()]
            back_dan = [int(x) for x in back_dan_str.split()] if back_dan_str else []
            back_tuo = [int(x) for x in back_tuo_str.split()]

            # 获取开奖号码
            draw_front_str = self.dantuo_win_draw_front.get().strip()
            draw_back_str = self.dantuo_win_draw_back.get().strip()

            if not draw_front_str or not draw_back_str:
                messagebox.showerror("输入错误", "请输入开奖号码！")
                return

            draw_front = [int(x) for x in draw_front_str.split()]
            draw_back = [int(x) for x in draw_back_str.split()]

            # 验证号码
            if len(draw_front) != 5 or len(draw_back) != 2:
                messagebox.showerror("输入错误", "开奖号码格式错误！前区应为5个号码，后区应为2个号码。")
                return

            # 验证胆拖号码
            if len(front_dan) > 4 or len(back_dan) > 1:
                messagebox.showerror("输入错误", "胆码格式错误！前区胆码不超过4个，后区胆码不超过1个。")
                return

            if len(front_dan) + len(front_tuo) < 5 or len(back_dan) + len(back_tuo) < 2:
                messagebox.showerror("输入错误", "投注号码格式错误！前区胆码+拖码至少选择5个号码，后区胆码+拖码至少选择2个号码。")
                return

            # 计算中奖情况
            is_additional = self.dantuo_win_additional.get()
            result = self.calculator.calculate_dantuo_win(
                front_dan, front_tuo, back_dan, back_tuo, (draw_front, draw_back), is_additional
            )

            # 生成结果文本
            win_result = "胆拖投注中奖结果：\n\n"
            win_result += f"投注号码：前区胆码 {', '.join(map(str, front_dan)) if front_dan else '无'}，前区拖码 {', '.join(map(str, front_tuo))}\n"
            win_result += f"         后区胆码 {', '.join(map(str, back_dan)) if back_dan else '无'}，后区拖码 {', '.join(map(str, back_tuo))}\n"
            win_result += f"开奖号码：前区 {', '.join(map(str, draw_front))}，后区 {', '.join(map(str, draw_back))}\n"
            win_result += f"总注数：{result['bet_count']}注\n"
            win_result += f"投注金额：{result['bet_amount']}元\n\n"

            # 添加中奖明细
            has_prize = False
            for level in range(1, 10):
                if result['prize_stats'][level] > 0:
                    has_prize = True
                    win_result += f"{level}等奖：{result['prize_stats'][level]}注\n"

            if not has_prize:
                win_result += "很遗憾，本次投注未中奖。\n"
            else:
                win_result += f"\n总中奖金额：{result['total_prize']}元\n"
                win_result += f"净收益：{result['net_win']}元\n"

            # 显示结果
            self.dantuo_win_result.delete(1.0, tk.END)
            self.dantuo_win_result.insert(tk.END, win_result)

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")

    def fetch_draw_numbers_for_complex(self):
        """为复式中奖计算获取开奖号码"""
        term = self.complex_win_term.get().strip()
        if not term:
            messagebox.showerror("输入错误", "请输入期号！")
            return

        # 显示加载中提示
        self.root.config(cursor="wait")
        self.root.update()

        try:
            # 获取开奖数据
            result = self.data_fetcher.fetch_by_term(term)

            if result:
                # 清空开奖号码输入框
                self.complex_win_draw_front.delete(0, tk.END)
                self.complex_win_draw_back.delete(0, tk.END)

                # 填入开奖号码
                self.complex_win_draw_front.insert(0, " ".join(map(str, result["front_numbers"])))
                self.complex_win_draw_back.insert(0, " ".join(map(str, result["back_numbers"])))

                messagebox.showinfo("成功", f"已获取期号 {term} 的开奖号码\n\n开奖日期：{result['date']}")
            else:
                messagebox.showerror("获取失败", f"未找到期号 {term} 的开奖数据！")
        except Exception as e:
            messagebox.showerror("获取异常", f"获取开奖数据时发生异常：{str(e)}")
        finally:
            # 恢复光标
            self.root.config(cursor="")

    def fetch_latest_draw_for_complex(self):
        """为复式中奖计算获取最新开奖号码"""
        # 显示加载中提示
        self.root.config(cursor="wait")
        self.root.update()

        try:
            # 获取最新开奖数据
            result = self.data_fetcher.fetch_latest()

            if result:
                # 清空开奖号码输入框
                self.complex_win_draw_front.delete(0, tk.END)
                self.complex_win_draw_back.delete(0, tk.END)

                # 填入开奖号码
                self.complex_win_draw_front.insert(0, " ".join(map(str, result["front_numbers"])))
                self.complex_win_draw_back.insert(0, " ".join(map(str, result["back_numbers"])))

                # 填入期号
                self.complex_win_term.delete(0, tk.END)
                self.complex_win_term.insert(0, result["term"])

                messagebox.showinfo("成功", f"已获取最新期号 {result['term']} 的开奖号码\n\n开奖日期：{result['date']}")
            else:
                messagebox.showerror("获取失败", "获取最新开奖数据失败！")
        except Exception as e:
            messagebox.showerror("获取异常", f"获取开奖数据时发生异常：{str(e)}")
        finally:
            # 恢复光标
            self.root.config(cursor="")

    def fetch_draw_numbers_for_dantuo(self):
        """为胆拖中奖计算获取开奖号码"""
        term = self.dantuo_win_term.get().strip()
        if not term:
            messagebox.showerror("输入错误", "请输入期号！")
            return

        # 显示加载中提示
        self.root.config(cursor="wait")
        self.root.update()

        try:
            # 获取开奖数据
            result = self.data_fetcher.fetch_by_term(term)

            if result:
                # 清空开奖号码输入框
                self.dantuo_win_draw_front.delete(0, tk.END)
                self.dantuo_win_draw_back.delete(0, tk.END)

                # 填入开奖号码
                self.dantuo_win_draw_front.insert(0, " ".join(map(str, result["front_numbers"])))
                self.dantuo_win_draw_back.insert(0, " ".join(map(str, result["back_numbers"])))

                messagebox.showinfo("成功", f"已获取期号 {term} 的开奖号码\n\n开奖日期：{result['date']}")
            else:
                messagebox.showerror("获取失败", f"未找到期号 {term} 的开奖数据！")
        except Exception as e:
            messagebox.showerror("获取异常", f"获取开奖数据时发生异常：{str(e)}")
        finally:
            # 恢复光标
            self.root.config(cursor="")

    def fetch_latest_draw_for_dantuo(self):
        """为胆拖中奖计算获取最新开奖号码"""
        # 显示加载中提示
        self.root.config(cursor="wait")
        self.root.update()

        try:
            # 获取最新开奖数据
            result = self.data_fetcher.fetch_latest()

            if result:
                # 清空开奖号码输入框
                self.dantuo_win_draw_front.delete(0, tk.END)
                self.dantuo_win_draw_back.delete(0, tk.END)

                # 填入开奖号码
                self.dantuo_win_draw_front.insert(0, " ".join(map(str, result["front_numbers"])))
                self.dantuo_win_draw_back.insert(0, " ".join(map(str, result["back_numbers"])))

                # 填入期号
                self.dantuo_win_term.delete(0, tk.END)
                self.dantuo_win_term.insert(0, result["term"])

                messagebox.showinfo("成功", f"已获取最新期号 {result['term']} 的开奖号码\n\n开奖日期：{result['date']}")
            else:
                messagebox.showerror("获取失败", "获取最新开奖数据失败！")
        except Exception as e:
            messagebox.showerror("获取异常", f"获取开奖数据时发生异常：{str(e)}")
        finally:
            # 恢复光标
            self.root.config(cursor="")


def main():
    """主函数"""
    root = tk.Tk()
    app = DLTCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
