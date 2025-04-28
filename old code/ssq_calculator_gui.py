#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球计算器GUI界面

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
from ssq_calculator import SSQCalculator

# 导入开奖数据获取模块
from ssq_api_fetcher import SSQApiFetcher


class SSQCalculatorGUI:
    """双色球计算器GUI类"""

    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.calculator = SSQCalculator()
        self.data_fetcher = SSQApiFetcher()  # 创建 API 数据获取器

        # 设置窗口
        self.root.title("双色球计算器")
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
        self.create_prize_info_tab()  # 添加奖级信息标签页

        # 设置样式
        self.setup_styles()

    def setup_styles(self):
        """设置控件样式"""
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=3)
        style.configure("TEntry", padding=3)
        style.configure("TFrame", padding=5)
        style.configure("TLabelframe", padding=5)
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))

    def create_complex_bet_tab(self):
        """创建复式投注标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="复式投注")

        # 创建标题
        ttk.Label(tab, text="双色球复式投注计算器", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=10
        )

        # 创建输入区域
        input_frame = ttk.LabelFrame(tab, text="投注选号")
        input_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(input_frame, text="红球选号个数 (6-33):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_red_count = ttk.Entry(input_frame, width=10)
        self.complex_red_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        self.complex_red_count.insert(0, "6")

        ttk.Label(input_frame, text="蓝球选号个数 (1-16):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_blue_count = ttk.Entry(input_frame, width=10)
        self.complex_blue_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.complex_blue_count.insert(0, "1")

        # 计算按钮
        ttk.Button(tab, text="计算投注", command=self.calculate_complex_bet).grid(row=2, column=0, columnspan=4, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="计算结果")
        result_frame.grid(row=3, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(result_frame, text="注数:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_bet_count = ttk.Label(result_frame, text="0")
        self.complex_bet_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(result_frame, text="金额:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_bet_amount = ttk.Label(result_frame, text="0元")
        self.complex_bet_amount.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

    def create_dantuo_bet_tab(self):
        """创建胆拖投注标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="胆拖投注")

        # 创建标题
        ttk.Label(tab, text="双色球胆拖投注计算器", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=10
        )

        # 创建输入区域
        input_frame = ttk.LabelFrame(tab, text="投注选号")
        input_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(input_frame, text="红球胆码个数 (0-5):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_red_dan_count = ttk.Entry(input_frame, width=10)
        self.dantuo_red_dan_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_red_dan_count.insert(0, "0")

        ttk.Label(input_frame, text="红球拖码个数:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_red_tuo_count = ttk.Entry(input_frame, width=10)
        self.dantuo_red_tuo_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_red_tuo_count.insert(0, "7")

        ttk.Label(input_frame, text="蓝球选号个数 (1-16):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_blue_count = ttk.Entry(input_frame, width=10)
        self.dantuo_blue_count.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        self.dantuo_blue_count.insert(0, "1")

        # 计算按钮
        ttk.Button(tab, text="计算投注", command=self.calculate_dantuo_bet).grid(row=2, column=0, columnspan=4, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="计算结果")
        result_frame.grid(row=3, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(result_frame, text="注数:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_bet_count = ttk.Label(result_frame, text="0")
        self.dantuo_bet_count.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(result_frame, text="金额:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_bet_amount = ttk.Label(result_frame, text="0元")
        self.dantuo_bet_amount.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

    def create_complex_win_tab(self):
        """创建复式中奖计算标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="复式中奖计算")

        # 创建标题
        ttk.Label(tab, text="双色球复式中奖计算器", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=10
        )

        # 投注号码输入区域
        bet_frame = ttk.LabelFrame(tab, text="投注号码")
        bet_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(bet_frame, text="红球号码 (用空格分隔，如：1 3 5 7 9 11 13):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_red_numbers = ttk.Entry(bet_frame, width=40)
        self.complex_win_red_numbers.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="蓝球号码 (用空格分隔，如：2 4 6):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_blue_numbers = ttk.Entry(bet_frame, width=40)
        self.complex_win_blue_numbers.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        # 开奖号码输入区域
        draw_frame = ttk.LabelFrame(tab, text="开奖号码")
        draw_frame.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 添加期号输入和获取按钮
        ttk.Label(draw_frame, text="期号 (如：21001):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_term = ttk.Entry(draw_frame, width=10)
        self.complex_win_term.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Button(draw_frame, text="获取开奖号码", command=self.fetch_draw_numbers_for_complex).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(draw_frame, text="获取最新开奖", command=self.fetch_latest_draw_for_complex).grid(row=0, column=3, padx=10, pady=5)

        ttk.Label(draw_frame, text="红球号码 (用空格分隔，如：1 3 5 7 9 11):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_draw_red = ttk.Entry(draw_frame, width=40)
        self.complex_win_draw_red.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        ttk.Label(draw_frame, text="蓝球号码 (用空格分隔，如：2):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.complex_win_draw_blue = ttk.Entry(draw_frame, width=40)
        self.complex_win_draw_blue.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

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
        """创建胆拖中奖计算标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="胆拖中奖计算")

        # 创建标题
        ttk.Label(tab, text="双色球胆拖中奖计算器", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=10
        )

        # 投注号码输入区域
        bet_frame = ttk.LabelFrame(tab, text="投注号码")
        bet_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        ttk.Label(bet_frame, text="红球胆码 (用空格分隔，如：1 3 5):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_red_dan = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_red_dan.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="红球拖码 (用空格分隔，如：7 9 11 13):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_red_tuo = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_red_tuo.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(bet_frame, text="蓝球号码 (用空格分隔，如：2 4 6):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_blue_numbers = ttk.Entry(bet_frame, width=40)
        self.dantuo_win_blue_numbers.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        # 开奖号码输入区域
        draw_frame = ttk.LabelFrame(tab, text="开奖号码")
        draw_frame.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=10, pady=10)

        # 添加期号输入和获取按钮
        ttk.Label(draw_frame, text="期号 (如：21001):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_term = ttk.Entry(draw_frame, width=10)
        self.dantuo_win_term.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Button(draw_frame, text="获取开奖号码", command=self.fetch_draw_numbers_for_dantuo).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(draw_frame, text="获取最新开奖", command=self.fetch_latest_draw_for_dantuo).grid(row=0, column=3, padx=10, pady=5)

        ttk.Label(draw_frame, text="红球号码 (用空格分隔，如：1 3 5 7 9 11):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_draw_red = ttk.Entry(draw_frame, width=40)
        self.dantuo_win_draw_red.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

        ttk.Label(draw_frame, text="蓝球号码 (用空格分隔，如：2):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.dantuo_win_draw_blue = ttk.Entry(draw_frame, width=40)
        self.dantuo_win_draw_blue.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

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
            # 获取输入值
            red_count = int(self.complex_red_count.get())
            blue_count = int(self.complex_blue_count.get())

            # 计算注数
            bet_count = self.calculator.calculate_complex_bet_count(red_count, blue_count)

            # 计算金额
            bet_amount = self.calculator.calculate_bet_amount(bet_count)

            # 更新显示
            self.complex_bet_count.config(text=str(bet_count))
            self.complex_bet_amount.config(text=f"{bet_amount}元")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误：{e}")

    def calculate_dantuo_bet(self):
        """计算胆拖投注注数和金额"""
        try:
            # 获取输入值
            red_dan_count = int(self.dantuo_red_dan_count.get())
            red_tuo_count = int(self.dantuo_red_tuo_count.get())
            blue_count = int(self.dantuo_blue_count.get())

            # 计算注数
            bet_count = self.calculator.calculate_dantuo_bet_count(
                red_dan_count, red_tuo_count, blue_count
            )

            # 计算金额
            bet_amount = self.calculator.calculate_bet_amount(bet_count)

            # 更新显示
            self.dantuo_bet_count.config(text=str(bet_count))
            self.dantuo_bet_amount.config(text=f"{bet_amount}元")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误：{e}")

    def calculate_complex_win(self):
        """计算复式投注中奖情况"""
        try:
            # 获取投注号码
            red_numbers_str = self.complex_win_red_numbers.get()
            blue_numbers_str = self.complex_win_blue_numbers.get()

            # 获取开奖号码
            draw_red_str = self.complex_win_draw_red.get()
            draw_blue_str = self.complex_win_draw_blue.get()

            # 转换为整数列表
            red_numbers = [int(num) for num in red_numbers_str.split()]
            blue_numbers = [int(num) for num in blue_numbers_str.split()]
            draw_red = [int(num) for num in draw_red_str.split()]
            draw_blue = [int(num) for num in draw_blue_str.split()]

            # 验证开奖号码格式
            if len(draw_red) != 6 or len(draw_blue) != 1:
                messagebox.showerror("格式错误", "开奖号码格式错误！红球应为6个号码，蓝球应为1个号码。")
                return

            # 计算中奖情况
            result = self.calculator.calculate_complex_win(
                red_numbers, blue_numbers, (draw_red, draw_blue)
            )

            # 显示结果
            self.complex_win_result.delete(1.0, tk.END)  # 清空文本框

            self.complex_win_result.insert(tk.END, f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元\n\n")

            # 显示中奖情况
            has_prize = False
            for level in range(1, 7):
                if result['prize_stats'][level] > 0:
                    has_prize = True
                    self.complex_win_result.insert(tk.END, f"{level}等奖：{result['prize_stats'][level]}注\n")

            if not has_prize:
                self.complex_win_result.insert(tk.END, "很遗憾，未中奖！\n")
            else:
                self.complex_win_result.insert(tk.END, f"\n中奖金额：{result['total_prize']}元\n")
                self.complex_win_result.insert(tk.END, f"净收益：{result['net_win']}元\n")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字，并用空格分隔！")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误：{e}")

    def calculate_dantuo_win(self):
        """计算胆拖投注中奖情况"""
        try:
            # 获取投注号码
            red_dan_str = self.dantuo_win_red_dan.get()
            red_tuo_str = self.dantuo_win_red_tuo.get()
            blue_numbers_str = self.dantuo_win_blue_numbers.get()

            # 获取开奖号码
            draw_red_str = self.dantuo_win_draw_red.get()
            draw_blue_str = self.dantuo_win_draw_blue.get()

            # 转换为整数列表
            red_dan = [int(num) for num in red_dan_str.split()] if red_dan_str.strip() else []
            red_tuo = [int(num) for num in red_tuo_str.split()]
            blue_numbers = [int(num) for num in blue_numbers_str.split()]
            draw_red = [int(num) for num in draw_red_str.split()]
            draw_blue = [int(num) for num in draw_blue_str.split()]

            # 验证开奖号码格式
            if len(draw_red) != 6 or len(draw_blue) != 1:
                messagebox.showerror("格式错误", "开奖号码格式错误！红球应为6个号码，蓝球应为1个号码。")
                return

            # 计算中奖情况
            result = self.calculator.calculate_dantuo_win(
                red_dan, red_tuo, blue_numbers, (draw_red, draw_blue)
            )

            # 显示结果
            self.dantuo_win_result.delete(1.0, tk.END)  # 清空文本框

            self.dantuo_win_result.insert(tk.END, f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元\n\n")

            # 显示中奖情况
            has_prize = False
            for level in range(1, 7):
                if result['prize_stats'][level] > 0:
                    has_prize = True
                    self.dantuo_win_result.insert(tk.END, f"{level}等奖：{result['prize_stats'][level]}注\n")

            if not has_prize:
                self.dantuo_win_result.insert(tk.END, "很遗憾，未中奖！\n")
            else:
                self.dantuo_win_result.insert(tk.END, f"\n中奖金额：{result['total_prize']}元\n")
                self.dantuo_win_result.insert(tk.END, f"净收益：{result['net_win']}元\n")

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字，并用空格分隔！")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误：{e}")

    def fetch_draw_numbers_for_complex(self):
        """为复式中奖计算获取开奖号码"""
        try:
            # 获取期号
            term = self.complex_win_term.get().strip()
            if not term:
                messagebox.showerror("输入错误", "请输入期号！")
                return

            # 获取开奖数据
            result = self.data_fetcher.fetch_by_term(term)
            if not result:
                messagebox.showerror("获取失败", f"未找到期号 {term} 的开奖数据！")
                return

            # 更新开奖号码
            self.complex_win_draw_red.delete(0, tk.END)
            self.complex_win_draw_red.insert(0, " ".join(str(num) for num in result["red_numbers"]))

            self.complex_win_draw_blue.delete(0, tk.END)
            self.complex_win_draw_blue.insert(0, " ".join(str(num) for num in result["blue_numbers"]))

            messagebox.showinfo("获取成功", f"成功获取期号 {term} 的开奖数据！")

        except Exception as e:
            messagebox.showerror("获取错误", f"获取开奖数据时出现错误：{e}")

    def fetch_latest_draw_for_complex(self):
        """为复式中奖计算获取最新开奖号码"""
        try:
            # 获取最新开奖数据
            result = self.data_fetcher.fetch_latest()
            if not result:
                messagebox.showerror("获取失败", "未能获取最新开奖数据！")
                return

            # 更新期号和开奖号码
            self.complex_win_term.delete(0, tk.END)
            self.complex_win_term.insert(0, result["term"])

            self.complex_win_draw_red.delete(0, tk.END)
            self.complex_win_draw_red.insert(0, " ".join(str(num) for num in result["red_numbers"]))

            self.complex_win_draw_blue.delete(0, tk.END)
            self.complex_win_draw_blue.insert(0, " ".join(str(num) for num in result["blue_numbers"]))

            messagebox.showinfo("获取成功", f"成功获取最新期号 {result['term']} 的开奖数据！")

        except Exception as e:
            messagebox.showerror("获取错误", f"获取开奖数据时出现错误：{e}")

    def fetch_draw_numbers_for_dantuo(self):
        """为胆拖中奖计算获取开奖号码"""
        try:
            # 获取期号
            term = self.dantuo_win_term.get().strip()
            if not term:
                messagebox.showerror("输入错误", "请输入期号！")
                return

            # 获取开奖数据
            result = self.data_fetcher.fetch_by_term(term)
            if not result:
                messagebox.showerror("获取失败", f"未找到期号 {term} 的开奖数据！")
                return

            # 更新开奖号码
            self.dantuo_win_draw_red.delete(0, tk.END)
            self.dantuo_win_draw_red.insert(0, " ".join(str(num) for num in result["red_numbers"]))

            self.dantuo_win_draw_blue.delete(0, tk.END)
            self.dantuo_win_draw_blue.insert(0, " ".join(str(num) for num in result["blue_numbers"]))

            messagebox.showinfo("获取成功", f"成功获取期号 {term} 的开奖数据！")

        except Exception as e:
            messagebox.showerror("获取错误", f"获取开奖数据时出现错误：{e}")

    def fetch_latest_draw_for_dantuo(self):
        """为胆拖中奖计算获取最新开奖号码"""
        try:
            # 获取最新开奖数据
            result = self.data_fetcher.fetch_latest()
            if not result:
                messagebox.showerror("获取失败", "未能获取最新开奖数据！")
                return

            # 更新期号和开奖号码
            self.dantuo_win_term.delete(0, tk.END)
            self.dantuo_win_term.insert(0, result["term"])

            self.dantuo_win_draw_red.delete(0, tk.END)
            self.dantuo_win_draw_red.insert(0, " ".join(str(num) for num in result["red_numbers"]))

            self.dantuo_win_draw_blue.delete(0, tk.END)
            self.dantuo_win_draw_blue.insert(0, " ".join(str(num) for num in result["blue_numbers"]))

            messagebox.showinfo("获取成功", f"成功获取最新期号 {result['term']} 的开奖数据！")

        except Exception as e:
            messagebox.showerror("获取错误", f"获取开奖数据时出现错误：{e}")


    def create_prize_info_tab(self):
        """创建奖级信息标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="奖级信息")

        # 创建标题
        ttk.Label(tab, text="双色球奖级计算器", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=10
        )

        # 创建奖级表格
        prize_frame = ttk.LabelFrame(tab, text="奖级表")
        prize_frame.grid(row=1, column=0, columnspan=4, sticky=tk.NSEW, padx=10, pady=10)

        # 表格头
        headers = ["奖级", "中奖条件", "中奖个数", "单注奖金", "预测奖金"]
        for i, header in enumerate(headers):
            ttk.Label(prize_frame, text=header, font=("Arial", 10, "bold"),
                     background="#f0f0f0", relief="ridge", borderwidth=1,
                     width=15, anchor="center").grid(row=0, column=i, padx=1, pady=1, sticky=tk.NSEW)

        # 奖级数据
        prize_data = [
            ["一等奖", "6红+1蓝", "0", "5000000 元", "0 元"],
            ["二等奖", "6红", "0", "100000 元", "0 元"],
            ["三等奖", "5红+1蓝", "0", "3000 元", "0 元"],
            ["四等奖", "5红 或 4红+1蓝", "0", "200 元", "0 元"],
            ["五等奖", "4红 或 3红+1蓝", "0", "10 元", "0 元"],
            ["六等奖", "2红+1蓝 或 1红+1蓝 或 0红+1蓝", "0", "5 元", "0 元"],
        ]

        for i, row_data in enumerate(prize_data):
            for j, cell_data in enumerate(row_data):
                ttk.Label(prize_frame, text=cell_data, relief="ridge", borderwidth=1,
                         width=15, anchor="center").grid(row=i+1, column=j, padx=1, pady=1, sticky=tk.NSEW)

        # 总计行
        ttk.Label(prize_frame, text="预测奖金：", font=("Arial", 10, "bold"),
                 relief="ridge", borderwidth=1, anchor="e").grid(row=len(prize_data)+1, column=0,
                                                            columnspan=4, padx=1, pady=1, sticky=tk.NSEW)
        ttk.Label(prize_frame, text="0 元", relief="ridge", borderwidth=1,
                 anchor="center").grid(row=len(prize_data)+1, column=4, padx=1, pady=1, sticky=tk.NSEW)

        # 注释
        note_text = "说明： 高等奖奖金会根据当期奖池和中奖情况而变化，仅供参考。工具提供：彩经网。"
        ttk.Label(prize_frame, text=note_text, wraplength=600,
                 justify="center", font=("Arial", 9)).grid(row=len(prize_data)+2, column=0,
                                                      columnspan=5, padx=5, pady=5)

        # 设置行列权重
        for i in range(5):
            prize_frame.columnconfigure(i, weight=1)
        for i in range(len(prize_data) + 3):
            prize_frame.rowconfigure(i, weight=1)


def main():
    """主函数"""
    root = tk.Tk()
    app = SSQCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
