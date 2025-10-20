import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import pandas as pd # 移到这里，确保在 matplotlib 之前导入
import matplotlib
matplotlib.use('TkAgg') # 明确指定 backend，有时有助于避免冲突
import matplotlib.pyplot as plt # 恢复 pyplot 导入
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # 恢复 canvas 导入
import threading # <--- 导入 threading
import queue     # <--- 导入 queue

# --- Matplotlib 中文显示配置 ---
try:
    # 优先尝试 macOS 字体
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Songti SC', 'AppleGothic', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    print("已尝试配置 macOS 中文字体 (PingFang SC, Heiti SC, Songti SC, AppleGothic, Arial Unicode MS)")
except Exception as e_mac:
    print(f"配置 macOS 字体失败: {e_mac}")
    try:
        # 尝试常见 Windows/Linux 字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        print("已尝试配置 Windows/Linux 中文字体 (SimHei, Microsoft YaHei, WenQuanYi Micro Hei)")
    except Exception as e_other:
        print(f"配置 Windows/Linux 字体失败: {e_other}")
        # 作为最后手段，尝试 STIX
        try:
            plt.rcParams['font.sans-serif'] = ['STIXGeneral']
            plt.rcParams['axes.unicode_minus'] = False
            print("已尝试配置 STIXGeneral 字体")
        except Exception as e_stix:
            print(f"配置 STIXGeneral 字体失败: {e_stix}")
            print("\n*** 警告：未能成功配置任何支持中文的字体。图表中的中文可能无法正常显示。***")
            print("*** 建议：请尝试安装 'Source Han Sans' (思源黑体) 或其他中文字体。***\n")
# --- 配置结束 ---

from src.core.ssq_calculator import SSQCalculator
from src.core.dlt_calculator import DLTCalculator # 导入大乐透计算器
from src.core.data_manager import LotteryDataManager # 导入数据管理器
from src.core.analyzer import LotteryAnalyzer # LotteryAnalyzer 在这里
from src.core.analyzers import FrequencyAnalyzer, PatternAnalyzer, DLTAnalyzer # 其他分析器在这里
from src.core.ssq_analyzer import SSQAnalyzer
from src.gui.generation_frame import GenerationFrame # 导入新的 Frame
from src.gui.feature_engineering_frame import FeatureEngineeringFrame # 导入特征工程 Frame

def parse_numbers(entry_widget) -> List[int]:
    """从输入框解析数字列表 (公共函数)"""
    try:
        text = entry_widget.get().strip()
        if not text:
            return []
        parts = text.replace(',', ' ').split()
        # 过滤掉非数字并去重
        numbers = sorted(list(set(int(p) for p in parts if p.isdigit())))
        return numbers
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的数字，并用空格或逗号分隔。")
        return [] # 返回空列表表示解析失败或无效

class SSQFrame(ttk.Frame):
    """双色球功能框架"""
    def __init__(self, master):
        super().__init__(master, padding="10")
        self.calculator = SSQCalculator()
        self.data_manager = LotteryDataManager("data")
        self._create_widgets()

    def _create_widgets(self):
        # --- 创建投注计算区 ---
        bet_frame = ttk.LabelFrame(self, text="投注计算", padding="10")
        bet_frame.pack(fill=tk.X, pady=5)

        # 复式投注
        complex_frame = ttk.Frame(bet_frame)
        complex_frame.pack(fill=tk.X, pady=5)
        ttk.Label(complex_frame, text="复式红球 (空格分隔):").grid(row=0, column=0, padx=5, sticky="w")
        self.complex_red_entry = ttk.Entry(complex_frame, width=30)
        self.complex_red_entry.grid(row=0, column=1, padx=5)
        ttk.Label(complex_frame, text="复式蓝球 (空格分隔):").grid(row=1, column=0, padx=5, sticky="w")
        self.complex_blue_entry = ttk.Entry(complex_frame, width=30)
        self.complex_blue_entry.grid(row=1, column=1, padx=5)
        self.complex_button = ttk.Button(complex_frame, text="计算复式", command=self.calculate_complex)
        self.complex_button.grid(row=0, column=2, rowspan=2, padx=10)

        # 胆拖投注
        dantuo_frame = ttk.Frame(bet_frame)
        dantuo_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dantuo_frame, text="红球胆码 (空格分隔):").grid(row=0, column=0, padx=5, sticky="w")
        self.dantuo_dan_entry = ttk.Entry(dantuo_frame, width=15)
        self.dantuo_dan_entry.grid(row=0, column=1, padx=5)
        ttk.Label(dantuo_frame, text="红球拖码 (空格分隔):").grid(row=1, column=0, padx=5, sticky="w")
        self.dantuo_tuo_entry = ttk.Entry(dantuo_frame, width=15)
        self.dantuo_tuo_entry.grid(row=1, column=1, padx=5)
        ttk.Label(dantuo_frame, text="蓝球 (空格分隔):").grid(row=0, column=2, padx=5, sticky="w")
        self.dantuo_blue_entry = ttk.Entry(dantuo_frame, width=15)
        self.dantuo_blue_entry.grid(row=0, column=3, padx=5)
        self.dantuo_button = ttk.Button(dantuo_frame, text="计算胆拖", command=self.calculate_dantuo)
        self.dantuo_button.grid(row=0, column=4, rowspan=2, padx=10)

        # 投注结果显示
        self.bet_result_label = ttk.Label(bet_frame, text="投注结果: ")
        self.bet_result_label.pack(pady=5)

        # --- 创建中奖核对区 ---
        check_frame = ttk.LabelFrame(self, text="中奖核对", padding="10")
        check_frame.pack(fill=tk.X, pady=5)

        # 获取开奖号码行
        fetch_frame = ttk.Frame(check_frame)
        fetch_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        ttk.Label(fetch_frame, text="期号:").pack(side=tk.LEFT, padx=5)
        self.check_issue_entry = ttk.Entry(fetch_frame, width=15)
        self.check_issue_entry.pack(side=tk.LEFT, padx=5)
        self.fetch_button = ttk.Button(fetch_frame, text="获取开奖号", command=self.fetch_draw_numbers)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(check_frame, text="开奖号码 (6红+1蓝, 空格分隔):").grid(row=1, column=0, padx=5, sticky="w")
        self.draw_entry = ttk.Entry(check_frame, width=30)
        self.draw_entry.grid(row=1, column=1, padx=5)

        # --- 修改：我的投注区域 --- > 改为可输入复式/胆拖
        my_bet_frame = ttk.LabelFrame(check_frame, text="我的投注号码", padding=5)
        my_bet_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # 单注/复式输入
        ttk.Label(my_bet_frame, text="红球:").grid(row=0, column=0, padx=5, sticky="w")
        self.my_bet_red_entry = ttk.Entry(my_bet_frame, width=20)
        self.my_bet_red_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(my_bet_frame, text="蓝球:").grid(row=0, column=2, padx=5, sticky="w")
        self.my_bet_blue_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_blue_entry.grid(row=0, column=3, padx=5, pady=2)

        # 胆拖输入
        ttk.Label(my_bet_frame, text="红胆:").grid(row=1, column=0, padx=5, sticky="w")
        self.my_bet_dan_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_dan_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(my_bet_frame, text="红拖:").grid(row=1, column=2, padx=5, sticky="w")
        self.my_bet_tuo_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_tuo_entry.grid(row=1, column=3, padx=5, pady=2, sticky="w")
        # <--- SSQ 胆拖的蓝球可以和上面复用的 self.my_bet_blue_entry

        self.check_button = ttk.Button(check_frame, text="核对中奖", command=self.check_prize)
        self.check_button.grid(row=1, column=2, rowspan=2, padx=10) # 调整按钮位置

        # 中奖结果显示
        self.prize_result_label = ttk.Label(check_frame, text="中奖结果: ")
        self.prize_result_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="w") # 调整行号

    def calculate_complex(self):
        red_numbers = parse_numbers(self.complex_red_entry)
        blue_numbers = parse_numbers(self.complex_blue_entry)

        if not red_numbers or not blue_numbers:
            return

        try:
            result = self.calculator.calculate_complex_bet(red_numbers, blue_numbers)
            self.bet_result_label.config(text=f"投注结果: {result.total_bets} 注, {result.total_amount} 元")
        except ValueError as e:
            messagebox.showerror("计算错误", str(e))
            self.bet_result_label.config(text="投注结果: 计算错误")

    def calculate_dantuo(self):
        red_dan = parse_numbers(self.dantuo_dan_entry)
        red_tuo = parse_numbers(self.dantuo_tuo_entry)
        blue_numbers = parse_numbers(self.dantuo_blue_entry)

        if red_dan is None or red_tuo is None or blue_numbers is None: # parse_numbers 返回 [] 而不是 None
            return
        if not red_tuo or not blue_numbers: # 胆码可以为空, 但拖码和蓝球不能为空
             messagebox.showerror("输入错误", "胆拖投注时，红球拖码和蓝球不能为空。")
             return

        if set(red_dan) & set(red_tuo):
             messagebox.showerror("输入错误", "红球胆码和拖码不能有重复数字。")
             return

        try:
            result = self.calculator.calculate_dantuo_bet(red_dan, red_tuo, blue_numbers)
            self.bet_result_label.config(text=f"投注结果: {result.total_bets} 注, {result.total_amount} 元")
        except ValueError as e:
            messagebox.showerror("计算错误", str(e))
            self.bet_result_label.config(text="投注结果: 计算错误")

    def fetch_draw_numbers(self):
        """根据输入的期号获取开奖号码并填充，如果期号为空则获取最新一期"""
        issue = self.check_issue_entry.get().strip()
        lottery_type = 'ssq' # Hardcoded for SSQFrame

        self.fetch_button.config(text="查询中...", state=tk.DISABLED)
        self.master.update_idletasks()

        try:
            # 情况1：未输入期号，获取最新一期
            if not issue:
                print("未输入期号，尝试获取最新数据...")
                update_success = self.data_manager.update_data(lottery_type)
                if update_success:
                    print("在线更新成功，获取最新一期数据...")
                    latest_data_df = self.data_manager.get_history_data(lottery_type, periods=1)
                    if not latest_data_df.empty:
                        latest_issue_data = latest_data_df.iloc[0].to_dict()
                        # 提取期号和号码
                        latest_issue = latest_issue_data.get('draw_num')
                        red_nums = latest_issue_data.get('red_numbers', [])
                        blue_num = latest_issue_data.get('blue_number', None)
                        if latest_issue and red_nums and blue_num is not None:
                            numbers_str = ",".join(map(str, sorted(red_nums))) + "," + str(blue_num)
                            numbers_str_display = numbers_str.replace(',', ' ')

                            self.check_issue_entry.delete(0, tk.END)
                            self.check_issue_entry.insert(0, str(latest_issue))
                            self.draw_entry.delete(0, tk.END)
                            self.draw_entry.insert(0, numbers_str_display)
                        else:
                             messagebox.showwarning("获取失败", "获取到最新数据，但数据格式不完整。")
                    else:
                        messagebox.showwarning("无数据", "无法获取最新一期开奖数据。")
                else:
                    messagebox.showerror("更新失败", f"无法从官网获取 {self.data_manager.LOTTERY_TYPES[lottery_type]} 最新数据，请检查网络或稍后再试。")

            # 情况2：输入了期号，按原逻辑查找
            else:
                print(f"查询期号 {issue}...")
                # 1. 先查本地
                issue_data = self.data_manager.get_issue_data(lottery_type, issue)

                if issue_data and 'numbers' in issue_data:
                    # 本地找到
                    numbers_str = issue_data['numbers'].replace(',', ' ')
                    self.draw_entry.delete(0, tk.END)
                    self.draw_entry.insert(0, numbers_str)
                else:
                    # 2. 本地未找到，尝试在线更新 (移除提示框)
                    print(f"本地未找到期号 {issue}，尝试在线更新...")
                    update_success = self.data_manager.update_data(lottery_type)
                    if update_success:
                        print("在线更新成功，再次查询本地数据...")
                        # 3. 再次查询本地
                        issue_data_after_update = self.data_manager.get_issue_data(lottery_type, issue)
                        if issue_data_after_update and 'numbers' in issue_data_after_update:
                            numbers_str = issue_data_after_update['numbers'].replace(',', ' ')
                            self.draw_entry.delete(0, tk.END)
                            self.draw_entry.insert(0, numbers_str)
                        else:
                            # 4. 更新后仍未找到
                            print(f"更新后仍未找到期号 {issue}")
                            messagebox.showwarning("未找到", f"未能从近期官网数据中找到期号 {issue}。\n可能期号过旧或不存在。")
                    else:
                        # 更新失败
                        print("在线更新失败")
                        messagebox.showerror("更新失败", f"无法从官网获取 {self.data_manager.LOTTERY_TYPES[lottery_type]} 最新数据，请检查网络或稍后再试。")

        except Exception as e:
             messagebox.showerror("查询错误", f"获取开奖号时发生错误: {str(e)}")
        finally:
             self.fetch_button.config(text="获取开奖号", state=tk.NORMAL)

    def check_prize(self):
        # --- 修改：不再使用 parse_numbers 解析开奖号 --- >
        draw_numbers_text = self.draw_entry.get().strip()
        if not draw_numbers_text:
             messagebox.showerror("输入错误", "请输入开奖号码。")
             return
        try:
            parts = draw_numbers_text.replace(',', ' ').split()
            draw_numbers_int = [int(p) for p in parts if p.isdigit()] # 转换为整数
            if len(draw_numbers_int) != 7:
                raise ValueError("开奖号码必须是7个数字。")
            # 不排序！直接使用原始顺序
            draw_numbers = draw_numbers_int
        except ValueError as e:
            messagebox.showerror("输入错误", f"开奖号码格式错误: {e}")
            return
        # <-----------------------------------------

        # --- 修改：根据输入判断核对类型 --- >
        bet_red = parse_numbers(self.my_bet_red_entry) # 投注号码仍用 parse_numbers
        bet_blue = parse_numbers(self.my_bet_blue_entry)
        bet_dan = parse_numbers(self.my_bet_dan_entry)
        bet_tuo = parse_numbers(self.my_bet_tuo_entry)

        prize_summary = None
        check_type = "unknown"

        try:
            # 优先判断胆拖 (需要胆码或拖码有输入，且蓝球有输入)
            if (bet_dan or bet_tuo) and bet_blue:
                if not bet_tuo:
                     messagebox.showerror("输入错误", "胆拖投注核对时，红球拖码不能为空。")
                     return
                if set(bet_dan) & set(bet_tuo):
                     messagebox.showerror("输入错误", "胆拖投注核对时，红球胆码和拖码不能重复。")
                     return
                # 验证号码范围 (简略，完整验证在 calculator 中)
                if not self.calculator.validate_numbers(bet_dan + bet_tuo, 'red') or \
                   not self.calculator.validate_numbers(bet_blue, 'blue'):
                     messagebox.showerror("输入错误", "胆拖投注号码范围无效。")
                     return

                prize_summary = self.calculator.check_dantuo_prize(bet_dan, bet_tuo, bet_blue, draw_numbers)
                check_type = "胆拖"

            # 否则判断复式/单式 (红球和蓝球都有输入)
            elif bet_red and bet_blue:
                 # 验证号码范围
                if not self.calculator.validate_numbers(bet_red, 'red') or \
                   not self.calculator.validate_numbers(bet_blue, 'blue'):
                     messagebox.showerror("输入错误", "投注号码范围无效。")
                     return

                # 如果是刚好 6 红 1 蓝，按单式处理 (调用旧方法，但返回格式统一)
                if len(bet_red) == 6 and len(bet_blue) == 1:
                    level, amount = self.calculator.check_prize(bet_red + bet_blue, draw_numbers)
                    prize_summary = {lvl: (1 if lvl == level else 0) for lvl in range(1, 7)}
                    check_type = "单式"
                # 否则按复式处理
                else:
                    prize_summary = self.calculator.check_complex_prize(bet_red, bet_blue, draw_numbers)
                    print(f"--- Debug: check_complex_prize returned: {prize_summary} ---")
                    check_type = "复式"
            else:
                messagebox.showerror("输入错误", "请输入有效的投注号码（复式、胆拖或单式）。")
                return

            # --- 显示汇总结果 --- >
            if prize_summary:
                total_wins = sum(prize_summary.values())
                if total_wins > 0:
                    result_lines = [f"{check_type}中奖结果:"]
                    total_amount = 0
                    for level in range(1, 7):
                        count = prize_summary.get(level, 0)
                        if count > 0:
                            # 从 PRIZE_LEVELS 获取单注奖金用于估算总额
                            # 注意：浮动奖金无法精确计算
                            # Need to find the actual key based on level which check_prize does internally. This is complex.
                            # Let's find the first key that matches the level for approximate prize amount
                            level_prize = 0
                            level_desc = f"{level}等奖"
                            for (r, b), info in self.calculator.PRIZE_LEVELS.items():
                                if info[0] == level:
                                     level_prize = info[1]
                                     if level <= 2:
                                         level_desc += "(浮动奖金)"
                                     break
                            result_lines.append(f"  - {level_desc}: {count} 注 x {level_prize} 元 (约)")
                            total_amount += count * level_prize # 估算总奖金
                    result_lines.append(f"总计: {total_wins} 注, 估算总奖金: {total_amount} 元")
                    self.prize_result_label.config(text="\n".join(result_lines))
                else:
                    self.prize_result_label.config(text=f"{check_type}中奖结果: 未中奖")
            else:
                 # prize_summary 为 None 通常意味着输入错误或未执行检查
                 self.prize_result_label.config(text="中奖结果: 无法核对，请检查输入。")

        except ValueError as e:
            messagebox.showerror("核对错误", f"输入号码格式或数量错误: {str(e)}")
            self.prize_result_label.config(text="中奖结果: 核对出错")
        except Exception as e:
            messagebox.showerror("核对错误", f"发生未知错误: {str(e)}")
            self.prize_result_label.config(text="中奖结果: 核对出错")

class DLTFrame(ttk.Frame):
    """大乐透功能框架"""
    def __init__(self, master):
        super().__init__(master, padding="10")
        self.calculator = DLTCalculator()
        # 假设 DataManager 实例可以通过某种方式访问，或者在这里也创建一个
        # 最简单的方式是每个 Frame 都创建一个，或者通过主 App 传递
        # 最简单的方式是每个 Frame 都创建一个，或者通过主 App 传递
        self.data_manager = LotteryDataManager("data")
        self.additional_bet = tk.BooleanVar(value=False)
        self._create_widgets()

    def _create_widgets(self):
        # --- 创建投注计算区 ---
        bet_frame = ttk.LabelFrame(self, text="投注计算", padding="10")
        bet_frame.pack(fill=tk.X, pady=5)

        # 追加投注选项
        additional_check = ttk.Checkbutton(bet_frame, text="追加投注 (每注3元)", variable=self.additional_bet)
        additional_check.pack(anchor="e", padx=5)

        # 复式投注
        complex_frame = ttk.Frame(bet_frame)
        complex_frame.pack(fill=tk.X, pady=5)
        ttk.Label(complex_frame, text="复式前区 (空格分隔):").grid(row=0, column=0, padx=5, sticky="w")
        self.complex_front_entry = ttk.Entry(complex_frame, width=30)
        self.complex_front_entry.grid(row=0, column=1, padx=5)
        ttk.Label(complex_frame, text="复式后区 (空格分隔):").grid(row=1, column=0, padx=5, sticky="w")
        self.complex_back_entry = ttk.Entry(complex_frame, width=30)
        self.complex_back_entry.grid(row=1, column=1, padx=5)
        self.complex_button = ttk.Button(complex_frame, text="计算复式", command=self.calculate_complex)
        self.complex_button.grid(row=0, column=2, rowspan=2, padx=10)

        # 胆拖投注
        dantuo_frame = ttk.Frame(bet_frame)
        dantuo_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dantuo_frame, text="前区胆码:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.dantuo_front_dan_entry = ttk.Entry(dantuo_frame, width=15)
        self.dantuo_front_dan_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(dantuo_frame, text="前区拖码:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.dantuo_front_tuo_entry = ttk.Entry(dantuo_frame, width=15)
        self.dantuo_front_tuo_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(dantuo_frame, text="后区胆码:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.dantuo_back_dan_entry = ttk.Entry(dantuo_frame, width=10)
        self.dantuo_back_dan_entry.grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(dantuo_frame, text="后区拖码:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.dantuo_back_tuo_entry = ttk.Entry(dantuo_frame, width=10)
        self.dantuo_back_tuo_entry.grid(row=1, column=3, padx=5, pady=2)
        self.dantuo_button = ttk.Button(dantuo_frame, text="计算胆拖", command=self.calculate_dantuo)
        self.dantuo_button.grid(row=0, column=4, rowspan=2, padx=10)

        # 投注结果显示
        self.bet_result_label = ttk.Label(bet_frame, text="投注结果: ")
        self.bet_result_label.pack(pady=5)

        # --- 创建中奖核对区 ---
        check_frame = ttk.LabelFrame(self, text="中奖核对", padding="10")
        check_frame.pack(fill=tk.X, pady=5)

        # 获取开奖号码行
        fetch_frame = ttk.Frame(check_frame)
        fetch_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        ttk.Label(fetch_frame, text="期号:").pack(side=tk.LEFT, padx=5)
        self.check_issue_entry = ttk.Entry(fetch_frame, width=15)
        self.check_issue_entry.pack(side=tk.LEFT, padx=5)
        self.fetch_button = ttk.Button(fetch_frame, text="获取开奖号", command=self.fetch_draw_numbers)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(check_frame, text="开奖号码 (5前+2后, 空格分隔):").grid(row=1, column=0, padx=5, sticky="w")
        self.draw_entry = ttk.Entry(check_frame, width=30)
        self.draw_entry.grid(row=1, column=1, padx=5)

        # --- 修改：我的投注区域 --- >
        my_bet_frame = ttk.LabelFrame(check_frame, text="我的投注号码", padding=5)
        my_bet_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # 单注/复式输入
        ttk.Label(my_bet_frame, text="前区:").grid(row=0, column=0, padx=5, sticky="w")
        self.my_bet_front_entry = ttk.Entry(my_bet_frame, width=20)
        self.my_bet_front_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(my_bet_frame, text="后区:").grid(row=0, column=2, padx=5, sticky="w")
        self.my_bet_back_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_back_entry.grid(row=0, column=3, padx=5, pady=2)

        # 胆拖输入
        ttk.Label(my_bet_frame, text="前胆:").grid(row=1, column=0, padx=5, sticky="w")
        self.my_bet_front_dan_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_front_dan_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(my_bet_frame, text="前拖:").grid(row=1, column=2, padx=5, sticky="w")
        self.my_bet_front_tuo_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_front_tuo_entry.grid(row=1, column=3, padx=5, pady=2, sticky="w")
        ttk.Label(my_bet_frame, text="后胆:").grid(row=2, column=0, padx=5, sticky="w")
        self.my_bet_back_dan_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_back_dan_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(my_bet_frame, text="后拖:").grid(row=2, column=2, padx=5, sticky="w")
        self.my_bet_back_tuo_entry = ttk.Entry(my_bet_frame, width=10)
        self.my_bet_back_tuo_entry.grid(row=2, column=3, padx=5, pady=2, sticky="w")

        # 核对时也需要追加选项
        self.check_additional_bet = tk.BooleanVar(value=False)
        check_additional_check = ttk.Checkbutton(check_frame, text="追加投注", variable=self.check_additional_bet)
        check_additional_check.grid(row=2, column=2, padx=5, sticky="w") # 位置调整到按钮左边

        self.check_button = ttk.Button(check_frame, text="核对中奖", command=self.check_prize)
        self.check_button.grid(row=1, column=2, rowspan=1, padx=10) # 按钮位置

        # 中奖结果显示
        self.prize_result_label = ttk.Label(check_frame, text="中奖结果: ")
        self.prize_result_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="w")

    def calculate_complex(self):
        front_numbers = parse_numbers(self.complex_front_entry)
        back_numbers = parse_numbers(self.complex_back_entry)

        if not front_numbers or not back_numbers:
            return

        try:
            is_add = self.additional_bet.get()
            result = self.calculator.calculate_complex_bet(front_numbers, back_numbers, is_additional=is_add)
            self.bet_result_label.config(text=f"投注结果: {result.total_bets} 注, {result.total_amount} 元")
        except ValueError as e:
            messagebox.showerror("计算错误", str(e))
            self.bet_result_label.config(text="投注结果: 计算错误")

    def calculate_dantuo(self):
        front_dan = parse_numbers(self.dantuo_front_dan_entry)
        front_tuo = parse_numbers(self.dantuo_front_tuo_entry)
        back_dan = parse_numbers(self.dantuo_back_dan_entry)
        back_tuo = parse_numbers(self.dantuo_back_tuo_entry)

        # 基本校验，详细校验交给 calculator
        if front_dan is None or front_tuo is None or back_dan is None or back_tuo is None:
             return
        if not front_tuo or not back_tuo:
            messagebox.showerror("输入错误", "胆拖投注时，前后区拖码不能为空。")
            return

        # 检查胆码和拖码是否有重复
        if set(front_dan) & set(front_tuo):
             messagebox.showerror("输入错误", "前区胆码和拖码不能有重复数字。")
             return
        if set(back_dan) & set(back_tuo):
             messagebox.showerror("输入错误", "后区胆码和拖码不能有重复数字。")
             return

        try:
            is_add = self.additional_bet.get()
            result = self.calculator.calculate_dantuo_bet(front_dan, front_tuo, back_dan, back_tuo, is_additional=is_add)
            self.bet_result_label.config(text=f"投注结果: {result.total_bets} 注, {result.total_amount} 元")
        except ValueError as e:
            messagebox.showerror("计算错误", str(e))
            self.bet_result_label.config(text="投注结果: 计算错误")

    def fetch_draw_numbers(self):
        """根据输入的期号获取开奖号码并填充，如果期号为空则获取最新一期"""
        issue = self.check_issue_entry.get().strip()
        lottery_type = 'dlt' # Hardcoded for DLTFrame

        self.fetch_button.config(text="查询中...", state=tk.DISABLED)
        self.master.update_idletasks()

        try:
            # 情况1：未输入期号，获取最新一期
            if not issue:
                print("未输入期号，尝试获取最新数据...")
                update_success = self.data_manager.update_data(lottery_type)
                if update_success:
                    print("在线更新成功，获取最新一期数据...")
                    latest_data_df = self.data_manager.get_history_data(lottery_type, periods=1)
                    if not latest_data_df.empty:
                        latest_issue_data = latest_data_df.iloc[0].to_dict()
                        # 提取期号和号码
                        latest_issue = latest_issue_data.get('draw_num')
                        front_nums = latest_issue_data.get('front_numbers', [])
                        back_nums = latest_issue_data.get('back_numbers', [])
                        if latest_issue and front_nums and back_nums:
                            numbers_str = (",".join(map(str, sorted(front_nums))) +
                                           "," +
                                           ",".join(map(str, sorted(back_nums))))
                            numbers_str_display = numbers_str.replace(',', ' ')

                            self.check_issue_entry.delete(0, tk.END)
                            self.check_issue_entry.insert(0, str(latest_issue))
                            self.draw_entry.delete(0, tk.END)
                            self.draw_entry.insert(0, numbers_str_display)
                        else:
                             messagebox.showwarning("获取失败", "获取到最新数据，但数据格式不完整。")
                    else:
                        messagebox.showwarning("无数据", "无法获取最新一期开奖数据。")
                else:
                    messagebox.showerror("更新失败", f"无法从官网获取 {self.data_manager.LOTTERY_TYPES[lottery_type]} 最新数据，请检查网络或稍后再试。")

            # 情况2：输入了期号，按原逻辑查找
            else:
                print(f"查询期号 {issue}...")
                # 1. 先查本地
                issue_data = self.data_manager.get_issue_data(lottery_type, issue)

                if issue_data and 'numbers' in issue_data:
                    # 本地找到
                    numbers_str = issue_data['numbers'].replace(',', ' ')
                    self.draw_entry.delete(0, tk.END)
                    self.draw_entry.insert(0, numbers_str)
                else:
                    # 2. 本地未找到，尝试在线更新 (移除提示框)
                    print(f"本地未找到期号 {issue}，尝试在线更新...")
                    update_success = self.data_manager.update_data(lottery_type)
                    if update_success:
                        print("在线更新成功，再次查询本地数据...")
                        # 3. 再次查询本地
                        issue_data_after_update = self.data_manager.get_issue_data(lottery_type, issue)
                        if issue_data_after_update and 'numbers' in issue_data_after_update:
                            numbers_str = issue_data_after_update['numbers'].replace(',', ' ')
                            self.draw_entry.delete(0, tk.END)
                            self.draw_entry.insert(0, numbers_str)
                        else:
                            # 4. 更新后仍未找到
                            print(f"更新后仍未找到期号 {issue}")
                            messagebox.showwarning("未找到", f"未能从近期官网数据中找到期号 {issue}。\n可能期号过旧或不存在。")
                    else:
                        # 更新失败
                        print("在线更新失败")
                        messagebox.showerror("更新失败", f"无法从官网获取 {self.data_manager.LOTTERY_TYPES[lottery_type]} 最新数据，请检查网络或稍后再试。")

        except Exception as e:
             messagebox.showerror("查询错误", f"获取开奖号时发生错误: {str(e)}")
        finally:
             self.fetch_button.config(text="获取开奖号", state=tk.NORMAL)

    def check_prize(self):
        # --- 修改：不再使用 parse_numbers 解析开奖号 --- >
        draw_numbers_text = self.draw_entry.get().strip()
        if not draw_numbers_text:
             messagebox.showerror("输入错误", "请输入开奖号码。")
             return
        try:
            parts = draw_numbers_text.replace(',', ' ').split()
            draw_numbers_int = [int(p) for p in parts if p.isdigit()] # 转换为整数
            if len(draw_numbers_int) != 7:
                raise ValueError("开奖号码必须是7个数字 (5前+2后)。") # DLT 特定提示
            # 不排序！直接使用原始顺序
            draw_numbers = draw_numbers_int
        except ValueError as e:
            messagebox.showerror("输入错误", f"开奖号码格式错误: {e}")
            return
        # <-----------------------------------------

        is_add = self.check_additional_bet.get()

        # --- 修改：根据输入判断核对类型 --- >
        bet_front = parse_numbers(self.my_bet_front_entry) # 投注号码仍用 parse_numbers
        bet_back = parse_numbers(self.my_bet_back_entry)
        bet_front_dan = parse_numbers(self.my_bet_front_dan_entry)
        bet_front_tuo = parse_numbers(self.my_bet_front_tuo_entry)
        bet_back_dan = parse_numbers(self.my_bet_back_dan_entry)
        bet_back_tuo = parse_numbers(self.my_bet_back_tuo_entry)

        prize_summary = None
        check_type = "unknown"

        try:
            # 优先判断胆拖
            if (bet_front_dan or bet_front_tuo or bet_back_dan or bet_back_tuo):
                # 胆拖时，所有胆拖相关输入框必须有合理的值 (或为空列表)
                if not bet_front_tuo or not bet_back_tuo:
                    messagebox.showerror("输入错误", "胆拖投注核对时，前后区拖码不能为空。")
                    return
                if set(bet_front_dan) & set(bet_front_tuo) or set(bet_back_dan) & set(bet_back_tuo):
                     messagebox.showerror("输入错误", "胆拖投注核对时，同区的胆码和拖码不能重复。")
                     return
                # 验证号码范围 (简略)
                if not self.calculator.validate_numbers(bet_front_dan + bet_front_tuo, 'front') or \
                   not self.calculator.validate_numbers(bet_back_dan + bet_back_tuo, 'back'):
                     messagebox.showerror("输入错误", "胆拖投注号码范围无效。")
                     return

                prize_summary = self.calculator.check_dantuo_prize(
                    bet_front_dan, bet_front_tuo, bet_back_dan, bet_back_tuo, draw_numbers, is_add
                )
                check_type = "胆拖"

            # 否则判断复式/单式
            elif bet_front and bet_back:
                # 验证号码范围
                if not self.calculator.validate_numbers(bet_front, 'front') or \
                   not self.calculator.validate_numbers(bet_back, 'back'):
                     messagebox.showerror("输入错误", "投注号码范围无效。")
                     return

                # 如果是刚好 5 前 2 后，按单式处理
                if len(bet_front) == 5 and len(bet_back) == 2:
                    level, amount = self.calculator.check_prize(bet_front + bet_back, draw_numbers, is_add)
                    prize_summary = {lvl: (1 if lvl == level else 0) for lvl in range(1, 10)}
                    check_type = "单式"
                # 否则按复式处理
                else:
                    prize_summary = self.calculator.check_complex_prize(bet_front, bet_back, draw_numbers, is_add)
                    print(f"--- Debug: check_complex_prize returned: {prize_summary} ---")
                    check_type = "复式"
            else:
                messagebox.showerror("输入错误", "请输入有效的投注号码（复式、胆拖或单式）。")
                return

            # --- 显示汇总结果 --- >
            if prize_summary:
                total_wins = sum(prize_summary.values())
                if total_wins > 0:
                    result_lines = [f"{check_type}中奖结果 ({'追加' if is_add else '基本'}):"]
                    total_amount = 0
                    for level in range(1, 10):
                        count = prize_summary.get(level, 0)
                        if count > 0:
                             # 从 PRIZE_LEVELS 获取单注奖金
                            level_prize = 0
                            level_desc = f"{level}等奖"
                            for (f, b), info in self.calculator.PRIZE_LEVELS.items():
                                if info[0] == level:
                                     level_prize = info[1] + (info[2] if is_add else 0)
                                     break
                            result_lines.append(f"  - {level_desc}: {count} 注 x {level_prize} 元")
                            total_amount += count * level_prize
                    result_lines.append(f"总计: {total_wins} 注, 总奖金: {total_amount} 元")
                    self.prize_result_label.config(text="\n".join(result_lines))
                else:
                    self.prize_result_label.config(text=f"{check_type}中奖结果 ({'追加' if is_add else '基本'}): 未中奖")
            else:
                 self.prize_result_label.config(text="中奖结果: 无法核对，请检查输入。")

        except ValueError as e:
            messagebox.showerror("核对错误", f"输入号码格式或数量错误: {str(e)}")
            self.prize_result_label.config(text="中奖结果: 核对出错")
        except Exception as e:
            messagebox.showerror("核对错误", f"发生未知错误: {str(e)}")
            self.prize_result_label.config(text="中奖结果: 核对出错")

class DataAnalysisFrame(ttk.Frame):
    """数据分析功能框架"""
    def __init__(self, master):
        super().__init__(master, padding="10")
        # 假设数据文件在项目根目录的 data/ 子目录下
        self.data_manager = LotteryDataManager("data")
        self.history_data = pd.DataFrame() # 用于存储加载的数据
        self.update_queue = queue.Queue() # <--- 创建用于线程通信的队列
        self.is_updating = False # <--- 添加状态标志
        self._create_widgets()

    def _create_widgets(self):
        # --- 控制区 ---
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=5)

        # 彩种选择
        ttk.Label(control_frame, text="彩种:").grid(row=0, column=0, padx=5, sticky="w")
        self.lottery_type_var = tk.StringVar(value='ssq')
        lottery_options = [("双色球", "ssq"), ("大乐透", "dlt")]
        col_offset = 1
        for text, val in lottery_options:
            rb = ttk.Radiobutton(control_frame, text=text, variable=self.lottery_type_var, value=val, command=self.load_data) # 切换彩种时自动加载数据
            rb.grid(row=0, column=col_offset, padx=5, sticky="w")
            col_offset += 1

        # 更新数据按钮
        self.update_button = ttk.Button(control_frame, text="更新最新数据", command=self.update_data)
        self.update_button.grid(row=0, column=col_offset, padx=10)
        col_offset += 1

        # 分析设置
        ttk.Label(control_frame, text="分析类型:").grid(row=1, column=0, padx=5, sticky="w")
        self.analysis_type_var = tk.StringVar(value='frequency')
        analysis_options = {"频率分析": "frequency", "模式分析": "pattern", "走势分析": "trend"} # 添加走势分析
        self.analysis_dropdown = ttk.Combobox(control_frame, textvariable=self.analysis_type_var,
                                              values=list(analysis_options.keys()), state="readonly")
        self.analysis_dropdown.grid(row=1, column=1, columnspan=2, padx=5, sticky="ew")

        # --- 添加图表区域选择 --- >
        self.plot_area_var = tk.StringVar(value='red_front') # 默认值
        self.plot_area_label = ttk.Label(control_frame, text="图表区域:")
        self.plot_area_label.grid(row=2, column=0, padx=5, sticky="w")
        self.plot_area_rb_frame = ttk.Frame(control_frame)
        self.plot_area_rb_frame.grid(row=2, column=1, columnspan=2, padx=5, sticky="ew")
        # 初始化时不显示选项，根据彩种动态更新
        # <----------------------

        ttk.Label(control_frame, text="分析期数 (留空为全部):").grid(row=1, column=3, padx=5, sticky="w") # 调整回第1行
        self.periods_entry = ttk.Entry(control_frame, width=10)
        self.periods_entry.grid(row=1, column=4, padx=5) # 调整回第1行

        self.analyze_button = ttk.Button(control_frame, text="执行分析", command=self.perform_analysis)
        self.analyze_button.grid(row=1, column=5, padx=10) # 调整回第1行

        # --- 结果显示区分隔 ---
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # --- 结果显示区 (左右布局) ---
        result_area = ttk.Frame(self)
        result_area.pack(fill=tk.BOTH, expand=True)

        # 左侧：历史数据表格
        table_frame = ttk.LabelFrame(result_area, text="历史数据", padding="5")
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 表格滚动条
        table_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        table_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

        self.data_tree = ttk.Treeview(table_frame,
                                      yscrollcommand=table_scroll_y.set,
                                      xscrollcommand=table_scroll_x.set,
                                      show='headings') # 只显示表头

        table_scroll_y.config(command=self.data_tree.yview)
        table_scroll_x.config(command=self.data_tree.xview)

        table_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        table_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(fill=tk.BOTH, expand=True)

        # 右侧：分析结果和图表
        analysis_display_frame = ttk.Frame(result_area)
        analysis_display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # 分析结果文本区
        self.result_text_frame = ttk.LabelFrame(analysis_display_frame, text="分析结果", padding="5")
        self.result_text_frame.pack(fill=tk.X, pady=(0, 5)) # 初始不扩展
        self.result_text = tk.Text(self.result_text_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.result_text.pack(fill=tk.X, expand=True)

        # 图表区
        self.chart_frame = ttk.LabelFrame(analysis_display_frame, text="图表展示", padding="5")
        self.chart_frame.pack(fill=tk.BOTH, expand=True) # 初始扩展

        # 使用 Matplotlib 创建图表
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100) # 图表大小可以调整
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.ax.set_title("请先执行分析")
        self.ax.text(0.5, 0.5, '无图表数据', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
        self.canvas.draw()

        # 初始化加载一次默认彩种数据
        self.load_data()
        self._update_plot_area_options() # 初始化时根据默认彩种更新选项
        self._check_update_queue() # <--- 开始检查更新队列

    def _update_plot_area_options(self): # 新增方法
        """根据当前选择的彩种更新图表区域选项"""
        # 清空旧选项
        for widget in self.plot_area_rb_frame.winfo_children():
            widget.destroy()

        lottery_type = self.lottery_type_var.get()
        options = []
        default_value = ''
        if lottery_type == 'ssq':
            options = [("红球", "red"), ("蓝球", "blue")]
            default_value = 'red'
            self.plot_area_label.config(text="图表区域:")
        elif lottery_type == 'dlt':
            options = [("前区", "front"), ("后区", "back")]
            default_value = 'front'
            self.plot_area_label.config(text="图表区域:")
        else:
             self.plot_area_label.config(text="") # 未知彩种不显示

        self.plot_area_var.set(default_value) # 设置默认值
        for i, (text, val) in enumerate(options):
             rb = ttk.Radiobutton(self.plot_area_rb_frame, text=text,
                                  variable=self.plot_area_var, value=val,
                                  command=self.perform_analysis) # 切换时自动重新绘图/分析
             rb.pack(side=tk.LEFT, padx=5)

    def _check_update_queue(self):
        """定期检查更新队列，处理后台线程的结果"""
        try:
            message = self.update_queue.get_nowait() # 非阻塞获取
            success, lottery_type, error_msg = message

            if success:
                messagebox.showinfo("更新成功", f"{self.data_manager.LOTTERY_TYPES[lottery_type]} 数据已更新。")
                # 只有当更新的彩种是当前选中的彩种时才重新加载
                if lottery_type == self.lottery_type_var.get():
                    self.load_data()
            else:
                messagebox.showerror("更新失败", f"更新 {self.data_manager.LOTTERY_TYPES[lottery_type]} 数据失败: {error_msg}")

            # 不管成功失败，恢复按钮状态
            self._finalize_update_ui()

        except queue.Empty:
            pass # 队列为空，不做任何事
        except Exception as e:
             print(f"Error checking update queue: {e}")
             self._finalize_update_ui() # 出错也要恢复UI

        # 每隔 100ms 检查一次队列
        self.master.after(100, self._check_update_queue)

    def update_data(self):
        if self.is_updating:
             messagebox.showwarning("请稍候", "正在更新数据中，请勿重复操作。")
             return

        lottery_type = self.lottery_type_var.get()
        self.is_updating = True
        self.update_button.config(text="更新中...", state=tk.DISABLED)
        self.master.update_idletasks()

        # 创建并启动后台线程执行更新
        update_thread = threading.Thread(target=self._background_update, args=(lottery_type,), daemon=True)
        update_thread.start()

    def _background_update(self, lottery_type: str):
        """在后台线程中执行数据更新"""
        error_msg = ""
        success = False
        try:
            success = self.data_manager.update_data(lottery_type)
            if not success:
                 error_msg = "获取或更新数据失败，请检查网络或API。"
        except Exception as e:
            error_msg = str(e)
            success = False
        finally:
            # 将结果放入队列
            self.update_queue.put((success, lottery_type, error_msg))
            # 注意：后台线程不直接操作UI或 self.is_updating

    def _finalize_update_ui(self):
         """恢复UI状态"""
         self.update_button.config(text="更新最新数据", state=tk.NORMAL)
         self.is_updating = False

    def load_data(self):
        lottery_type = self.lottery_type_var.get()
        periods_str = self.periods_entry.get().strip()
        periods = int(periods_str) if periods_str.isdigit() else None

        try:
            self.history_data = self.data_manager.get_history_data(lottery_type, periods=periods)
            self.display_data_in_table(self.history_data)
            self._update_plot_area_options() # <--- 添加调用以更新图表区域选项
        except Exception as e:
            messagebox.showerror("加载错误", f"加载历史数据时发生错误: {str(e)}")
            self.history_data = pd.DataFrame()

    def display_data_in_table(self, df: pd.DataFrame):
        # 清空旧数据
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        if df.empty:
            self.data_tree["columns"] = []
            self.data_tree.heading("#0", text="无数据")
            return

        # --- 定义中文列名映射 --- >
        column_mapping = {
            'draw_num': '期号',
            'draw_date': '开奖日期',
            'red_numbers': '红球',
            'blue_number': '蓝球',
            'blue_numbers': '蓝球', # 兼容 preprocess_data 可能产生的列名
            'front_numbers': '前区号码',
            'back_numbers': '后区号码',
            'prize_pool': '奖池金额',
            'sales': '销售额',
            'first_prize_num': '一等奖注数',
            'first_prize_amount': '一等奖金额'
            # 可以根据实际 DataFrame 列名添加更多映射
        }
        # <-----------------------

        # --- 定义要显示的核心列 --- >
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            # 双色球：显示核心列，隐藏展开的号码列
            core_columns = ['draw_num', 'draw_date', 'red_numbers', 'blue_number', 'prize_pool', 'sales', 'first_prize_num', 'first_prize_amount']
            # 过滤掉展开的号码列 (red_1, red_2, ..., red_6, blue_1)
            expanded_columns = [f'red_{i}' for i in range(1, 7)] + ['blue_1']
        elif lottery_type == 'dlt':
            # 大乐透：显示核心列，隐藏展开的号码列
            core_columns = ['draw_num', 'draw_date', 'front_numbers', 'back_numbers', 'prize_pool', 'sales', 'first_prize_num', 'first_prize_amount']
            # 过滤掉展开的号码列 (front_1, front_2, ..., front_5, back_1, back_2)
            expanded_columns = [f'front_{i}' for i in range(1, 6)] + [f'back_{i}' for i in range(1, 3)]
        else:
            core_columns = list(df.columns)
            expanded_columns = []
        
        # 只显示存在的核心列，排除展开列
        columns_to_display = [col for col in core_columns if col in df.columns and col not in expanded_columns]
        
        # --- 大乐透条件列显示逻辑（隐藏全为0的列）--- >
        if lottery_type == 'dlt':
            columns_to_hide = []
            for col in ['prize_pool', 'sales']:
                if col in columns_to_display:
                    try:
                        # 尝试将列转为数字，无法转换的视为NaN，然后检查是否全为0或NaN
                        numeric_col = pd.to_numeric(df[col], errors='coerce')
                        if numeric_col.fillna(0).eq(0).all():
                            columns_to_hide.append(col)
                    except Exception:
                        # 如果转换或检查出错，也隐藏该列
                        columns_to_hide.append(col)
            columns_to_display = [col for col in columns_to_display if col not in columns_to_hide]
        # <---------------------------

        # 设置列 (使用中文名)
        display_column_ids = [col for col in df.columns if col in columns_to_display] # 按原始顺序过滤
        display_column_names = [column_mapping.get(col, col) for col in display_column_ids]

        self.data_tree["columns"] = display_column_ids
        self.data_tree.heading("#0", text="", anchor=tk.W) # 隐藏第一列
        self.data_tree.column("#0", width=0, stretch=tk.NO)

        for col_id, col_name in zip(display_column_ids, display_column_names):
            self.data_tree.heading(col_id, text=col_name, anchor=tk.W)
            # 根据列名调整宽度 (示例)
            width = 100
            if '号码' in col_name or 'numbers' in col_id:
                 width = 150
            elif '日期' in col_name or 'date' in col_id:
                 width = 120
            elif '金额' in col_name or '销售额' in col_name or 'amount' in col_id or 'sales' in col_id:
                 width = 120
            self.data_tree.column(col_id, anchor=tk.W, width=width)

        # 插入数据 (只插入需要显示的列)
        for index, row in df[display_column_ids].iterrows():
             # 将列表转换为更易读的字符串显示
             display_values = []
             for col_id in display_column_ids:
                 value = row[col_id]
                 if isinstance(value, list):
                     display_values.append(' '.join(map(str, value)))
                 elif pd.isna(value):
                     display_values.append('') # NaN 显示为空
                 else:
                     display_values.append(str(value))
             self.data_tree.insert("", tk.END, values=display_values)

    def perform_analysis(self):
        if self.history_data.empty:
            messagebox.showwarning("无法分析", "请先加载或更新数据。")
            return

        lottery_type = self.lottery_type_var.get()
        # --- 修改：获取内部标识符 --- >
        # analysis_type = self.analysis_type_var.get() # 不再直接使用 StringVar 的值
        analysis_name = self.analysis_dropdown.get() # 获取显示名称，例如 "模式分析"
        analysis_options = {"频率分析": "frequency", "模式分析": "pattern", "走势分析": "trend"} # 需要这个映射关系
        analysis_key = analysis_options.get(analysis_name) # 根据显示名称查找内部 key
        # <---------------------------------

        # 清空旧结果和图表
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.ax.clear()
        self.ax.set_title(f"{analysis_name} - {self.data_manager.LOTTERY_TYPES[lottery_type]}")

        try:
            analyzer = None
            # --- 修改：使用内部 key 进行判断 --- >
            if analysis_key == 'frequency':
                analyzer = FrequencyAnalyzer(lottery_type)
            elif analysis_key == 'pattern':
                analyzer = PatternAnalyzer(lottery_type)
            elif analysis_key == 'trend':
                # 走势分析在 SSQAnalyzer/DLTAnalyzer 中实现
                if lottery_type == 'ssq':
                    analyzer = SSQAnalyzer() # 实例化对应的具体分析器
                elif lottery_type == 'dlt':
                    analyzer = DLTAnalyzer()
                else:
                    analyzer = None # 不支持的类型
            # <---------------------------------
            # TODO: 添加更多分析器选择

            if analyzer:
                # --- 数据预处理 --- >
                # 注意：SSQ/DLTAnalyzer 的方法目前期望 List[Dict] 而不是 DataFrame
                # 需要调整或转换
                # 暂时先尝试直接传递 DataFrame，看是否出错，后续再调整
                processed_data = self.preprocess_data(self.history_data.copy(), lottery_type)
                if processed_data is None:
                    return # 预处理失败

                # --- 调用 analyze 方法 --- >
                results = None
                if analysis_key == 'trend':
                    if hasattr(analyzer, 'analyze_trends'):
                        # 假设 analyze_trends 接受 DataFrame (如果报错则需修改)
                        # 它们实际需要 List[Dict]，需要转换
                        history_list = processed_data.to_dict('records')
                        results = analyzer.analyze_trends(history_list) # 传递 List[Dict]
                    else:
                         messagebox.showerror("错误", f"{type(analyzer).__name__} 没有实现 analyze_trends 方法")
                         return
                elif hasattr(analyzer, 'analyze'): # 其他分析器调用 analyze
                    results = analyzer.analyze(processed_data)
                else:
                    messagebox.showerror("错误", f"{type(analyzer).__name__} 没有实现 analyze 方法")
                    return

                # 如果分析返回 None 或出错信息
                if results is None:
                     messagebox.showerror("分析失败", "分析过程未能返回有效结果。")
                     return
                if isinstance(results, dict) and "error" in results:
                    messagebox.showerror("分析错误", results["error"])
                    return
                # <--------------------------

                # 显示文本结果
                self.display_text_results(results)

                # 可视化结果
                if analysis_key == 'frequency': # 只有频率分析绘制图表
                    self.plot_frequency(results)
                elif analysis_key not in ['pattern', 'trend']: # 其他未来可能有图表的分析
                    self.ax.clear()
                    self.ax.text(0.5, 0.5, '暂无此分析的图表', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)

            else:
                 # 如果 analysis_key 为 None 或未匹配到 analyzer
                 self.ax.clear()
                 self.ax.text(0.5, 0.5, '无效的分析类型', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
                 messagebox.showwarning("分析错误", f"不支持或未知的分析类型: {analysis_name}")

            self.canvas.draw() # 更新图表

            # --- 根据分析类型调整布局 --- >
            if analysis_key in ['pattern', 'trend']: # 模式和走势暂时都隐藏图表
                self.chart_frame.pack_forget() # 隐藏图表区域
                # 让文本区域填充可用空间
                self.result_text_frame.pack_configure(fill=tk.BOTH, expand=True, pady=(0, 5))
            else:
                # 确保文本区域恢复原样 (不垂直扩展)
                self.result_text_frame.pack_configure(fill=tk.X, expand=False, pady=(0, 5))
                # 检查图表区域是否已被隐藏，如果是，则重新显示
                if not self.chart_frame.winfo_viewable(): # 使用 winfo_viewable 检查更可靠
                    self.chart_frame.pack(fill=tk.BOTH, expand=True) # 使用原始 pack 参数重新显示
            # <--------------------------

        except Exception as e:
            messagebox.showerror("分析错误", f"执行分析时出错: {str(e)}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, '分析出错', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
            self.canvas.draw()

    def preprocess_data(self, df: pd.DataFrame, lottery_type: str) -> Optional[pd.DataFrame]:
        """验证数据是否包含所需的号码列表列"""
        try:
            required_num_cols = []
            if lottery_type == 'ssq':
                required_num_cols = ['red_numbers', 'blue_number']
            elif lottery_type == 'dlt':
                required_num_cols = ['front_numbers', 'back_numbers']
            else:
                messagebox.showerror("预处理错误", f"未知的彩票类型: {lottery_type}")
                return None

            missing_cols = [col for col in required_num_cols if col not in df.columns]
            if missing_cols:
                messagebox.showerror("预处理错误", f"数据缺少必需的号码列: {', '.join(missing_cols)}")
                return None

            # 可选：添加对列类型的验证，确保它们是列表或数字
            # 例如，检查 ssq 的 red_numbers 是否是 list, blue_number 是否是 int/list
            # 此处暂时省略详细验证，假设 DataManager 加载的数据格式基本正确

            # 如果需要，确保蓝球/后区也被处理成列表形式，以统一后续分析器接口
            if lottery_type == 'ssq' and 'blue_number' in df.columns:
                 # 检查第一行，如果不是列表，则转换整列
                 # 检查类型是否已经是 list 或类似 list 的结构（如 numpy array）
                 first_val = df['blue_number'].iloc[0]
                 if not isinstance(first_val, list) and not pd.api.types.is_list_like(first_val):
                      print("--- Debug preprocess_data: Converting SSQ blue_number to list ---")
                      # 为了避免 SettingWithCopyWarning，创建一个新列或使用 .loc
                      df.loc[:, 'blue_numbers'] = df['blue_number'].apply(lambda x: [x] if pd.notna(x) else [])
                 elif 'blue_numbers' not in df.columns: # 如果已经是 list 但列名不对
                      print("--- Debug preprocess_data: Renaming SSQ blue_number to blue_numbers ---")
                      df = df.rename(columns={'blue_number': 'blue_numbers'})

            elif lottery_type == 'dlt' and 'back_numbers' in df.columns:
                 # dlt 的 back_numbers 应该已经是列表了，可加验证
                 pass

            print(f"--- Debug preprocess_data: Validation passed for {lottery_type}. Returning DataFrame with columns: {list(df.columns)}")
            return df # 数据格式符合预期，直接返回

        except Exception as e:
            messagebox.showerror("预处理错误", f"验证号码列时出错: {str(e)}")
            return None

    def display_text_results(self, results: dict):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        # 格式化字典输出
        import json
        result_str = json.dumps(results, indent=4, ensure_ascii=False)
        self.result_text.insert(tk.END, result_str)
        self.result_text.config(state=tk.DISABLED)

    def plot_frequency(self, results: dict):
        if not results or not isinstance(results, dict):
             self.ax.text(0.5, 0.5, '分析结果格式错误', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
             return

        lottery_type = self.lottery_type_var.get()
        plot_area = self.plot_area_var.get()
        area_data = None
        area_label = "号码"

        # 根据彩种和选择的区域获取数据
        if lottery_type == 'ssq':
            if plot_area == 'red' and 'red' in results:
                area_data = results['red'].get('frequencies')
                area_label = "红球号码"
            elif plot_area == 'blue' and 'blue' in results:
                area_data = results['blue'].get('frequencies')
                area_label = "蓝球号码"
        elif lottery_type == 'dlt':
            if plot_area == 'front' and 'front' in results:
                area_data = results['front'].get('frequencies')
                area_label = "前区号码"
            elif plot_area == 'back' and 'back' in results:
                area_data = results['back'].get('frequencies')
                area_label = "后区号码"

        if area_data is None or not isinstance(area_data, dict) or not area_data:
             self.ax.text(0.5, 0.5, f'{plot_area} 频率数据缺失或格式错误', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
             return

        # 绘制频率图 (注意 key 是字符串)
        try:
            # 将字典的键（字符串）转为整数用于排序和绘图，值保持不变
            numbers = sorted([int(k) for k in area_data.keys()])
            frequencies = [area_data[str(n)] for n in numbers]

            self.ax.bar(numbers, frequencies)
            self.ax.set_xlabel(area_label)
            self.ax.set_ylabel("出现次数") # 改为次数
            # 根据号码数量调整 x 轴刻度，避免过于密集
            if len(numbers) > 20:
                 self.ax.set_xticks(numbers[::2]) # 每隔一个显示刻度
                 self.ax.tick_params(axis='x', rotation=90, labelsize=8)
            else:
                 self.ax.set_xticks(numbers)
                 self.ax.tick_params(axis='x', rotation=0, labelsize=10)

            plt.tight_layout() # 调整布局防止标签重叠
        except Exception as e:
             self.ax.text(0.5, 0.5, f'绘制图表时出错:\n{e}', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)

class LotteryApp:
    def __init__(self, master):
        self.master = master
        master.title("彩票工具集")
        master.geometry("800x600") # 增加窗口大小以容纳更多内容

        # 创建 Notebook (选项卡控件)
        self.notebook = ttk.Notebook(master)

        # 创建并添加双色球选项卡
        self.ssq_tab = SSQFrame(self.notebook)
        self.notebook.add(self.ssq_tab, text='双色球')

        # 创建并添加大乐透选项卡
        self.dlt_tab = DLTFrame(self.notebook)
        self.notebook.add(self.dlt_tab, text='大乐透')

        # 创建并添加数据分析选项卡
        self.analysis_tab = DataAnalysisFrame(self.notebook)
        self.notebook.add(self.analysis_tab, text='数据分析')

        # 添加号码推荐标签页
        self.generation_tab = GenerationFrame(self.notebook, self.analysis_tab.data_manager, LotteryAnalyzer())
        self.notebook.add(self.generation_tab, text="号码推荐")

        # 添加号码评价标签页
        from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
        self.evaluation_tab = NumberEvaluationFrame(self.notebook, self.analysis_tab.data_manager)
        self.notebook.add(self.evaluation_tab, text="号码评价")

        # 添加特征工程标签页
        # 需要传递 DataManager 实例
        # self.feature_tab = FeatureEngineeringFrame(self.notebook)
        # self.feature_tab.set_data_manager(self.analysis_tab.data_manager) # 调用 setter 传递
        # self.notebook.add(self.feature_tab, text="特征工程")

        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # 状态栏

# 在文件末尾添加缺失的LotteryToolsGUI类
class LotteryToolsGUI:
    """彩票工具集主应用程序类"""
    
    def __init__(self, root=None, data_path=None):
        """初始化应用程序
        
        Args:
            root: Tkinter根窗口，如果为None则创建新窗口
            data_path: 数据路径，如果为None则使用默认路径
        """
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root
            
        self.data_path = data_path or "data"
        self._setup_window()
        self._create_application()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("彩票工具集")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("resources/icon.ico")
            pass
        except Exception:
            pass
    
    def _create_application(self):
        """创建应用程序主界面"""
        # 使用现有的LotteryApp类
        self.app = LotteryApp(self.root)
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()
        except Exception as e:
            messagebox.showerror("应用程序错误", f"发生未知错误: {str(e)}")
            self.quit()
    
    def quit(self):
        """退出应用程序"""
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    # 保持原有的启动方式
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()
