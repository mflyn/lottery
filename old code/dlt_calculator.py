#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大乐透计算器 - 参考中国体彩网官方计算器功能
https://www.lottery.gov.cn/tool/dltjsq.jspx/

功能：
1. 计算复式投注的注数和金额
2. 计算胆拖投注的注数和金额
3. 计算中奖情况和奖金
"""

import math
import itertools
from typing import List, Tuple, Dict, Set, Optional


class DLTCalculator:
    """大乐透计算器类"""

    # 大乐透奖级设置
    PRIZE_LEVELS = {
        # 格式：(前区命中数, 后区命中数): [奖级, 基本奖金, 追加奖金]
        (5, 2): [1, 10000000, 8000000],  # 一等奖
        (5, 1): [2, 250000, 200000],     # 二等奖
        (5, 0): [3, 10000, 8000],        # 三等奖
        (4, 2): [4, 3000, 2400],         # 四等奖
        (4, 1): [5, 300, 240],           # 五等奖
        (3, 2): [6, 200, 160],           # 六等奖
        (4, 0): [7, 100, 80],            # 七等奖
        (3, 1): [8, 15, 12],             # 八等奖
        (2, 2): [8, 15, 12],             # 八等奖
        (3, 0): [9, 5, 0],               # 九等奖
        (1, 2): [9, 5, 0],               # 九等奖
        (2, 1): [9, 5, 0],               # 九等奖
        (0, 2): [9, 5, 0],               # 九等奖
    }

    # 基本投注单注金额
    BASIC_PRICE = 2
    # 追加投注单注金额
    ADDITIONAL_PRICE = 1

    def __init__(self):
        """初始化计算器"""
        pass

    @staticmethod
    def combination(n: int, m: int) -> int:
        """计算组合数 C(n,m)"""
        if m > n:
            return 0
        return math.comb(n, m)

    def calculate_complex_bet_count(self, front_count: int, back_count: int) -> int:
        """
        计算复式投注的注数

        参数:
            front_count: 前区选号个数
            back_count: 后区选号个数

        返回:
            注数
        """
        if front_count < 5 or back_count < 2:
            return 0

        # 复式投注注数 = C(前区选号个数,5) × C(后区选号个数,2)
        return self.combination(front_count, 5) * self.combination(back_count, 2)

    def calculate_dantuo_bet_count(self, front_dan_count: int, front_tuo_count: int,
                                  back_dan_count: int, back_tuo_count: int) -> int:
        """
        计算胆拖投注的注数

        参数:
            front_dan_count: 前区胆码个数
            front_tuo_count: 前区拖码个数
            back_dan_count: 后区胆码个数
            back_tuo_count: 后区拖码个数

        返回:
            注数
        """
        # 前区胆码不能超过4个，后区胆码不能超过1个
        if front_dan_count > 4 or back_dan_count > 1:
            return 0

        # 前区胆码+拖码至少要有5个，后区胆码+拖码至少要有2个
        if front_dan_count + front_tuo_count < 5 or back_dan_count + back_tuo_count < 2:
            return 0

        # 胆拖投注注数 = C(前区拖码个数, 5-前区胆码个数) × C(后区拖码个数, 2-后区胆码个数)
        return (self.combination(front_tuo_count, 5 - front_dan_count) *
                self.combination(back_tuo_count, 2 - back_dan_count))

    def calculate_bet_amount(self, bet_count: int, is_additional: bool = False) -> float:
        """
        计算投注金额

        参数:
            bet_count: 注数
            is_additional: 是否追加投注

        返回:
            投注金额
        """
        if is_additional:
            return bet_count * (self.BASIC_PRICE + self.ADDITIONAL_PRICE)
        else:
            return bet_count * self.BASIC_PRICE

    def check_win(self, bet_numbers: Tuple[List[int], List[int]],
                 draw_numbers: Tuple[List[int], List[int]]) -> Dict:
        """
        检查单注投注是否中奖

        参数:
            bet_numbers: 投注号码，格式为([前区号码], [后区号码])
            draw_numbers: 开奖号码，格式为([前区号码], [后区号码])

        返回:
            中奖信息字典
        """
        bet_front, bet_back = bet_numbers
        draw_front, draw_back = draw_numbers

        # 计算前区和后区的命中数
        front_hits = len(set(bet_front) & set(draw_front))
        back_hits = len(set(bet_back) & set(draw_back))

        # 查找奖级
        prize_key = (front_hits, back_hits)
        if prize_key in self.PRIZE_LEVELS:
            level, basic_prize, additional_prize = self.PRIZE_LEVELS[prize_key]
            return {
                "win": True,
                "level": level,
                "front_hits": front_hits,
                "back_hits": back_hits,
                "basic_prize": basic_prize,
                "additional_prize": additional_prize
            }
        else:
            return {
                "win": False,
                "front_hits": front_hits,
                "back_hits": back_hits
            }

    def calculate_complex_win(self, front_numbers: List[int], back_numbers: List[int],
                             draw_numbers: Tuple[List[int], List[int]],
                             is_additional: bool = False) -> Dict:
        """
        计算复式投注的中奖情况

        参数:
            front_numbers: 前区投注号码列表
            back_numbers: 后区投注号码列表
            draw_numbers: 开奖号码，格式为([前区号码], [后区号码])
            is_additional: 是否追加投注

        返回:
            中奖统计信息
        """
        # 生成所有可能的单式投注组合
        front_combinations = list(itertools.combinations(front_numbers, 5))
        back_combinations = list(itertools.combinations(back_numbers, 2))

        # 统计各奖级中奖注数
        prize_stats = {level: 0 for level in range(1, 14)}
        total_prize = 0

        for front_combo in front_combinations:
            for back_combo in back_combinations:
                bet = (list(front_combo), list(back_combo))
                result = self.check_win(bet, draw_numbers)

                if result["win"]:
                    level = result["level"]
                    prize_stats[level] += 1

                    if is_additional:
                        total_prize += result["basic_prize"] + result["additional_prize"]
                    else:
                        total_prize += result["basic_prize"]

        # 计算总投注注数和金额
        bet_count = self.calculate_complex_bet_count(len(front_numbers), len(back_numbers))
        bet_amount = self.calculate_bet_amount(bet_count, is_additional)

        return {
            "bet_count": bet_count,
            "bet_amount": bet_amount,
            "prize_stats": prize_stats,
            "total_prize": total_prize,
            "net_win": total_prize - bet_amount
        }

    def calculate_dantuo_win(self, front_dan: List[int], front_tuo: List[int],
                            back_dan: List[int], back_tuo: List[int],
                            draw_numbers: Tuple[List[int], List[int]],
                            is_additional: bool = False) -> Dict:
        """
        计算胆拖投注的中奖情况

        参数:
            front_dan: 前区胆码列表
            front_tuo: 前区拖码列表
            back_dan: 后区胆码列表
            back_tuo: 后区拖码列表
            draw_numbers: 开奖号码，格式为([前区号码], [后区号码])
            is_additional: 是否追加投注

        返回:
            中奖统计信息
        """
        # 生成所有可能的单式投注组合
        front_tuo_combinations = list(itertools.combinations(front_tuo, 5 - len(front_dan)))
        back_tuo_combinations = list(itertools.combinations(back_tuo, 2 - len(back_dan)))

        # 统计各奖级中奖注数
        prize_stats = {level: 0 for level in range(1, 14)}
        total_prize = 0

        for front_tuo_combo in front_tuo_combinations:
            front_combo = front_dan + list(front_tuo_combo)

            for back_tuo_combo in back_tuo_combinations:
                back_combo = back_dan + list(back_tuo_combo)

                bet = (front_combo, back_combo)
                result = self.check_win(bet, draw_numbers)

                if result["win"]:
                    level = result["level"]
                    prize_stats[level] += 1

                    if is_additional:
                        total_prize += result["basic_prize"] + result["additional_prize"]
                    else:
                        total_prize += result["basic_prize"]

        # 计算总投注注数和金额
        bet_count = self.calculate_dantuo_bet_count(
            len(front_dan), len(front_tuo), len(back_dan), len(back_tuo)
        )
        bet_amount = self.calculate_bet_amount(bet_count, is_additional)

        return {
            "bet_count": bet_count,
            "bet_amount": bet_amount,
            "prize_stats": prize_stats,
            "total_prize": total_prize,
            "net_win": total_prize - bet_amount
        }


def main():
    """主函数，提供命令行界面"""
    calculator = DLTCalculator()

    print("=" * 50)
    print("大乐透计算器 - 参考中国体彩网官方计算器")
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
                front_count = int(input("请输入前区选号个数(5-35): "))
                back_count = int(input("请输入后区选号个数(2-12): "))

                bet_count = calculator.calculate_complex_bet_count(front_count, back_count)

                if bet_count == 0:
                    print("输入有误，请检查！")
                    continue

                is_additional = input("是否追加投注(y/n): ").lower() == 'y'
                bet_amount = calculator.calculate_bet_amount(bet_count, is_additional)

                print(f"\n复式投注：前区选{front_count}个，后区选{back_count}个")
                print(f"共{bet_count}注，投注金额{bet_amount}元")

            except ValueError:
                print("输入有误，请输入数字！")

        elif choice == "2":
            try:
                front_dan_count = int(input("请输入前区胆码个数(0-4): "))
                front_tuo_count = int(input("请输入前区拖码个数: "))
                back_dan_count = int(input("请输入后区胆码个数(0-1): "))
                back_tuo_count = int(input("请输入后区拖码个数: "))

                bet_count = calculator.calculate_dantuo_bet_count(
                    front_dan_count, front_tuo_count, back_dan_count, back_tuo_count
                )

                if bet_count == 0:
                    print("输入有误，请检查！")
                    continue

                is_additional = input("是否追加投注(y/n): ").lower() == 'y'
                bet_amount = calculator.calculate_bet_amount(bet_count, is_additional)

                print(f"\n胆拖投注：前区胆{front_dan_count}拖{front_tuo_count}，后区胆{back_dan_count}拖{back_tuo_count}")
                print(f"共{bet_count}注，投注金额{bet_amount}元")

            except ValueError:
                print("输入有误，请输入数字！")

        elif choice == "3":
            try:
                print("\n请输入前区号码(用空格分隔，如：1 3 5 7 9 11)：")
                front_numbers = list(map(int, input().split()))

                print("请输入后区号码(用空格分隔，如：2 4 6)：")
                back_numbers = list(map(int, input().split()))

                print("请输入开奖号码：")
                print("前区号码(用空格分隔，如：1 3 5 7 9)：")
                draw_front = list(map(int, input().split()))

                print("后区号码(用空格分隔，如：2 4)：")
                draw_back = list(map(int, input().split()))

                if len(draw_front) != 5 or len(draw_back) != 2:
                    print("开奖号码格式错误！前区应为5个号码，后区应为2个号码。")
                    continue

                is_additional = input("是否追加投注(y/n): ").lower() == 'y'

                result = calculator.calculate_complex_win(
                    front_numbers, back_numbers, (draw_front, draw_back), is_additional
                )

                print("\n中奖计算结果：")
                print(f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元")

                has_prize = False
                for level in range(1, 14):
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
                print("\n请输入前区胆码(用空格分隔，如：1 3 5)：")
                front_dan = list(map(int, input().split()))

                print("请输入前区拖码(用空格分隔，如：7 9 11 13)：")
                front_tuo = list(map(int, input().split()))

                print("请输入后区胆码(用空格分隔，如：2)：")
                back_dan = list(map(int, input().split()))

                print("请输入后区拖码(用空格分隔，如：4 6 8)：")
                back_tuo = list(map(int, input().split()))

                print("请输入开奖号码：")
                print("前区号码(用空格分隔，如：1 3 5 7 9)：")
                draw_front = list(map(int, input().split()))

                print("后区号码(用空格分隔，如：2 4)：")
                draw_back = list(map(int, input().split()))

                if len(draw_front) != 5 or len(draw_back) != 2:
                    print("开奖号码格式错误！前区应为5个号码，后区应为2个号码。")
                    continue

                is_additional = input("是否追加投注(y/n): ").lower() == 'y'

                result = calculator.calculate_dantuo_win(
                    front_dan, front_tuo, back_dan, back_tuo,
                    (draw_front, draw_back), is_additional
                )

                print("\n中奖计算结果：")
                print(f"投注：{result['bet_count']}注，金额：{result['bet_amount']}元")

                has_prize = False
                for level in range(1, 14):
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
