#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球计算器核心类 - 参考中国福彩网官方计算器功能

功能：
1. 计算复式投注的注数和金额
2. 计算胆拖投注的注数和金额
3. 计算中奖情况和奖金
"""

import math
import itertools
from typing import List, Tuple, Dict, Set, Optional


class SSQCalculator:
    """双色球计算器类"""

    # 双色球奖级设置
    PRIZE_LEVELS = {
        # 格式：(红球命中数, 蓝球命中数): [奖级, 基本奖金]
        (6, 1): [1, 5000000],  # 一等奖，浮动奖金，这里设置一个基本值
        (6, 0): [2, 100000],   # 二等奖，浮动奖金，这里设置一个基本值
        (5, 1): [3, 3000],     # 三等奖
        (5, 0): [4, 200],      # 四等奖
        (4, 1): [4, 200],      # 四等奖
        (4, 0): [5, 10],       # 五等奖
        (3, 1): [5, 10],       # 五等奖
        (2, 1): [6, 5],        # 六等奖
        (1, 1): [6, 5],        # 六等奖
        (0, 1): [6, 5],        # 六等奖
    }

    # 基本投注单注金额
    BASIC_PRICE = 2

    def __init__(self):
        """初始化计算器"""
        pass

    @staticmethod
    def combination(n: int, m: int) -> int:
        """计算组合数 C(n,m)"""
        if m > n:
            return 0
        return math.comb(n, m)

    def calculate_complex_bet_count(self, red_count: int, blue_count: int) -> int:
        """
        计算复式投注的注数

        参数:
            red_count: 红球选号个数
            blue_count: 蓝球选号个数

        返回:
            注数
        """
        if red_count < 6 or blue_count < 1:
            return 0

        # 复式投注注数 = C(红球选号个数,6) × C(蓝球选号个数,1)
        return self.combination(red_count, 6) * self.combination(blue_count, 1)

    def calculate_dantuo_bet_count(self, red_dan_count: int, red_tuo_count: int,
                                  blue_count: int) -> int:
        """
        计算胆拖投注的注数

        参数:
            red_dan_count: 红球胆码个数
            red_tuo_count: 红球拖码个数
            blue_count: 蓝球选号个数

        返回:
            注数
        """
        # 红球胆码不能超过5个
        if red_dan_count > 5:
            return 0

        # 红球胆码+拖码至少要有6个
        if red_dan_count + red_tuo_count < 6 or blue_count < 1:
            return 0

        # 胆拖投注注数 = C(红球拖码个数, 6-红球胆码个数) × C(蓝球个数, 1)
        return (self.combination(red_tuo_count, 6 - red_dan_count) *
                self.combination(blue_count, 1))

    def calculate_bet_amount(self, bet_count: int) -> float:
        """
        计算投注金额

        参数:
            bet_count: 注数

        返回:
            投注金额
        """
        return bet_count * self.BASIC_PRICE

    def check_win(self, bet_numbers: Tuple[List[int], List[int]],
                 draw_numbers: Tuple[List[int], List[int]]) -> Dict:
        """
        检查单注投注是否中奖

        参数:
            bet_numbers: 投注号码，格式为([红球号码], [蓝球号码])
            draw_numbers: 开奖号码，格式为([红球号码], [蓝球号码])

        返回:
            中奖信息字典
        """
        bet_red, bet_blue = bet_numbers
        draw_red, draw_blue = draw_numbers

        # 计算红球和蓝球的命中数
        red_hits = len(set(bet_red) & set(draw_red))
        blue_hits = len(set(bet_blue) & set(draw_blue))

        # 查找奖级
        prize_key = (red_hits, blue_hits)
        if prize_key in self.PRIZE_LEVELS:
            level, prize = self.PRIZE_LEVELS[prize_key]
            return {
                "win": True,
                "level": level,
                "red_hits": red_hits,
                "blue_hits": blue_hits,
                "prize": prize
            }
        else:
            return {
                "win": False,
                "red_hits": red_hits,
                "blue_hits": blue_hits
            }

    def calculate_complex_win(self, red_numbers: List[int], blue_numbers: List[int],
                             draw_numbers: Tuple[List[int], List[int]]) -> Dict:
        """
        计算复式投注的中奖情况

        参数:
            red_numbers: 红球投注号码列表
            blue_numbers: 蓝球投注号码列表
            draw_numbers: 开奖号码，格式为([红球号码], [蓝球号码])

        返回:
            中奖统计信息
        """
        # 生成所有可能的单式投注组合
        red_combinations = list(itertools.combinations(red_numbers, 6))
        blue_combinations = list(itertools.combinations(blue_numbers, 1))

        # 统计各奖级中奖注数
        prize_stats = {level: 0 for level in range(1, 7)}
        total_prize = 0

        for red_combo in red_combinations:
            for blue_combo in blue_combinations:
                bet = (list(red_combo), list(blue_combo))
                result = self.check_win(bet, draw_numbers)

                if result["win"]:
                    level = result["level"]
                    prize_stats[level] += 1
                    total_prize += result["prize"]

        # 计算总投注注数和金额
        bet_count = self.calculate_complex_bet_count(len(red_numbers), len(blue_numbers))
        bet_amount = self.calculate_bet_amount(bet_count)

        return {
            "bet_count": bet_count,
            "bet_amount": bet_amount,
            "prize_stats": prize_stats,
            "total_prize": total_prize,
            "net_win": total_prize - bet_amount
        }

    def calculate_dantuo_win(self, red_dan: List[int], red_tuo: List[int],
                            blue_numbers: List[int],
                            draw_numbers: Tuple[List[int], List[int]]) -> Dict:
        """
        计算胆拖投注的中奖情况

        参数:
            red_dan: 红球胆码列表
            red_tuo: 红球拖码列表
            blue_numbers: 蓝球号码列表
            draw_numbers: 开奖号码，格式为([红球号码], [蓝球号码])

        返回:
            中奖统计信息
        """
        # 生成所有可能的单式投注组合
        red_tuo_combinations = list(itertools.combinations(red_tuo, 6 - len(red_dan)))
        blue_combinations = list(itertools.combinations(blue_numbers, 1))

        # 统计各奖级中奖注数
        prize_stats = {level: 0 for level in range(1, 7)}
        total_prize = 0

        for red_tuo_combo in red_tuo_combinations:
            red_combo = red_dan + list(red_tuo_combo)

            for blue_combo in blue_combinations:
                bet = (red_combo, list(blue_combo))
                result = self.check_win(bet, draw_numbers)

                if result["win"]:
                    level = result["level"]
                    prize_stats[level] += 1
                    total_prize += result["prize"]

        # 计算总投注注数和金额
        bet_count = self.calculate_dantuo_bet_count(
            len(red_dan), len(red_tuo), len(blue_numbers)
        )
        bet_amount = self.calculate_bet_amount(bet_count)

        return {
            "bet_count": bet_count,
            "bet_amount": bet_amount,
            "prize_stats": prize_stats,
            "total_prize": total_prize,
            "net_win": total_prize - bet_amount
        }


def main():
    """主函数，提供命令行界面"""
    calculator = SSQCalculator()

    print("=" * 50)
    print("双色球计算器 - 参考中国福彩网官方计算器")
    print("=" * 50)

    while True:
        print("\n请选择功能：")
        print("1. 复式投注注数计算")
        print("2. 胆拖投注注数计算")
        print("3. 复式投注中奖计算")
        print("4. 胆拖投注中奖计算")
        print("0. 退出")

        choice = input("请输入选择(0-4): ")

        if choice == "0":
            print("感谢使用，再见！")
            break

        elif choice == "1":
            try:
                red_count = int(input("请输入红球选号个数(6-33): "))
                blue_count = int(input("请输入蓝球选号个数(1-16): "))

                bet_count = calculator.calculate_complex_bet_count(red_count, blue_count)

                if bet_count == 0:
                    print("输入有误，请检查！")
                    continue

                bet_amount = calculator.calculate_bet_amount(bet_count)

                print(f"\n复式投注：红球选{red_count}个，蓝球选{blue_count}个")
                print(f"共{bet_count}注，投注金额{bet_amount}元")

            except ValueError:
                print("输入有误，请输入数字！")

        elif choice == "2":
            try:
                red_dan_count = int(input("请输入红球胆码个数(0-5): "))
                red_tuo_count = int(input("请输入红球拖码个数: "))
                blue_count = int(input("请输入蓝球选号个数(1-16): "))

                bet_count = calculator.calculate_dantuo_bet_count(
                    red_dan_count, red_tuo_count, blue_count
                )

                if bet_count == 0:
                    print("输入有误，请检查！")
                    continue

                bet_amount = calculator.calculate_bet_amount(bet_count)

                print(f"\n胆拖投注：红球胆{red_dan_count}拖{red_tuo_count}，蓝球选{blue_count}个")
                print(f"共{bet_count}注，投注金额{bet_amount}元")

            except ValueError:
                print("输入有误，请输入数字！")

        elif choice == "3":
            try:
                print("\n请输入红球号码(用空格分隔，如：1 3 5 7 9 11)：")
                red_numbers = list(map(int, input().split()))

                print("请输入蓝球号码(用空格分隔，如：2 4 6)：")
                blue_numbers = list(map(int, input().split()))

                print("请输入开奖号码：")
                print("红球号码(用空格分隔，如：1 3 5 7 9 11)：")
                draw_red = list(map(int, input().split()))

                print("蓝球号码(用空格分隔，如：2)：")
                draw_blue = list(map(int, input().split()))

                if len(draw_red) != 6 or len(draw_blue) != 1:
                    print("开奖号码格式错误！红球应为6个号码，蓝球应为1个号码。")
                    continue

                result = calculator.calculate_complex_win(
                    red_numbers, blue_numbers, (draw_red, draw_blue)
                )

                print("\n中奖计算结果：")
                print(f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元")

                has_prize = False
                for level in range(1, 7):
                    if result['prize_stats'][level] > 0:
                        has_prize = True
                        print(f"{level}等奖：{result['prize_stats'][level]}注")

                if not has_prize:
                    print("很遗憾，未中奖！")
                else:
                    print(f"中奖金额：{result['total_prize']}元")
                    print(f"净收益：{result['net_win']}元")

            except ValueError:
                print("输入有误，请检查！")

        elif choice == "4":
            try:
                print("\n请输入红球胆码(用空格分隔，如：1 3 5)：")
                red_dan = list(map(int, input().split()))

                print("请输入红球拖码(用空格分隔，如：7 9 11 13)：")
                red_tuo = list(map(int, input().split()))

                print("请输入蓝球号码(用空格分隔，如：2 4 6)：")
                blue_numbers = list(map(int, input().split()))

                print("请输入开奖号码：")
                print("红球号码(用空格分隔，如：1 3 5 7 9 11)：")
                draw_red = list(map(int, input().split()))

                print("蓝球号码(用空格分隔，如：2)：")
                draw_blue = list(map(int, input().split()))

                if len(draw_red) != 6 or len(draw_blue) != 1:
                    print("开奖号码格式错误！红球应为6个号码，蓝球应为1个号码。")
                    continue

                result = calculator.calculate_dantuo_win(
                    red_dan, red_tuo, blue_numbers, (draw_red, draw_blue)
                )

                print("\n中奖计算结果：")
                print(f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元")

                has_prize = False
                for level in range(1, 7):
                    if result['prize_stats'][level] > 0:
                        has_prize = True
                        print(f"{level}等奖：{result['prize_stats'][level]}注")

                if not has_prize:
                    print("很遗憾，未中奖！")
                else:
                    print(f"中奖金额：{result['total_prize']}元")
                    print(f"净收益：{result['net_win']}元")

            except ValueError:
                print("输入有误，请检查！")

        else:
            print("无效选择，请重新输入！")


if __name__ == "__main__":
    main()
