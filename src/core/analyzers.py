#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票数据分析器 - 简单分析器实现
注意：此文件保留用于向后兼容，建议使用 src/core/analyzers/ 目录下的完整实现
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from collections import Counter
import pandas as pd
import numpy as np
from .analyzers.lottery_analyzer import LotteryAnalyzer


class SSQAnalyzer(LotteryAnalyzer):
    """双色球数据分析器 - 简单实现

    注意：这是一个简化版本，用于向后兼容。
    推荐使用 src/core/ssq_analyzer.py 中的完整实现。
    """

    def analyze_frequency(self, history_data: List[Dict], periods: int = 100) -> Dict:
        """分析号码出现频率"""
        recent_data = history_data[:periods]

        # 统计红球和蓝球号码
        red_numbers = []
        blue_numbers = []
        for draw in recent_data:
            red_numbers.extend(draw['red_numbers'])
            blue_numbers.append(draw['blue_number'])

        # 计算频率
        red_freq = Counter(red_numbers)
        blue_freq = Counter(blue_numbers)

        # 计算理论频率
        red_theory = periods * 6 / 33   # 红球每个号码理论出现次数
        blue_theory = periods / 16      # 蓝球每个号码理论出现次数

        return {
            'red_frequency': dict(red_freq),
            'blue_frequency': dict(blue_freq),
            'red_theory': red_theory,
            'blue_theory': blue_theory,
            'periods': periods
        }

    def analyze_trends(self, history_data: List[Dict], periods: int = 30) -> Dict:
        """分析号码走势"""
        recent_data = history_data[:periods]

        # 创建红球和蓝球矩阵
        red_matrix = np.zeros((periods, 33))
        blue_matrix = np.zeros((periods, 16))

        # 填充矩阵
        for i, draw in enumerate(recent_data):
            for num in draw['red_numbers']:
                red_matrix[i][num-1] = 1
            blue_matrix[i][draw['blue_number']-1] = 1

        return {
            'red_trends': red_matrix.tolist(),
            'blue_trends': blue_matrix.tolist(),
            'periods': periods
        }

# --- 新增 PatternAnalyzer --- >
class PatternAnalyzer:
    """分析号码模式（奇偶、大小、和值等）"""
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type

    def _analyze_single_draw(self, numbers: List[int], area: str) -> Dict:
        """分析单期单区域的模式"""
        if not numbers:
             return {}

        patterns = {}

        # 奇偶比
        odd_count = sum(1 for n in numbers if n % 2 != 0)
        even_count = len(numbers) - odd_count
        patterns['odd_even_ratio'] = f"{odd_count}:{even_count}"

        # 定义大小分界线
        small_large_threshold = 0
        if self.lottery_type == 'ssq' and area == 'red':
            small_large_threshold = 17 # 1-16 小, 17-33 大
        elif self.lottery_type == 'dlt' and area == 'front':
            small_large_threshold = 18 # 1-17 小, 18-35 大
        elif self.lottery_type == 'ssq' and area == 'blue':
            small_large_threshold = 9  # 1-8 小, 9-16 大
        elif self.lottery_type == 'dlt' and area == 'back':
            small_large_threshold = 7  # 1-6 小, 7-12 大

        if small_large_threshold > 0:
            small_count = sum(1 for n in numbers if n < small_large_threshold)
            large_count = len(numbers) - small_count
            patterns['small_large_ratio'] = f"{small_count}:{large_count}"

        # 和值 (仅对红球/前区计算)
        if area == 'red' or area == 'front':
            patterns['sum'] = sum(numbers)

        return patterns

    def analyze(self, data: pd.DataFrame) -> Dict:
        """分析 DataFrame 中所有期数的模式，返回每期的模式字典列表"""
        results = {'patterns_by_draw': []}

        num_cols_map = {}
        if self.lottery_type == 'ssq':
            num_cols_map = {'red': 'red_numbers', 'blue': 'blue_numbers'}
        elif self.lottery_type == 'dlt':
            num_cols_map = {'front': 'front_numbers', 'back': 'back_numbers'}
        else:
            return {"error": "不支持的彩票类型"}

        # 检查必需列是否存在
        if not all(col in data.columns for col in num_cols_map.values()):
             missing = [col for col in num_cols_map.values() if col not in data.columns]
             return {"error": f"数据缺少必需列: {missing}"}

        for index, row in data.iterrows():
            draw_patterns = {'draw_num': row.get('draw_num', '未知')}
            for area, col_name in num_cols_map.items():
                numbers = row.get(col_name, [])
                if isinstance(numbers, list) and numbers:
                    draw_patterns[area] = self._analyze_single_draw(numbers, area)
                else:
                    draw_patterns[area] = {"error": "号码数据无效或缺失"}
            results['patterns_by_draw'].append(draw_patterns)

        # TODO: 可以添加对所有期数模式的汇总统计
        # 例如，统计最常见的奇偶比、大小比等

        return results
# <---------------------------