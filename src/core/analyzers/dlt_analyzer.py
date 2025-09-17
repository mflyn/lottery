from typing import List, Dict
from collections import Counter
import numpy as np
from .lottery_analyzer import LotteryAnalyzer

class DLTAnalyzer(LotteryAnalyzer):
    """大乐透数据分析器"""
    def analyze_frequency(self, history_data: List[Dict], periods: int = 100) -> Dict:
        recent_data = history_data[:periods]
        front_numbers = []
        back_numbers = []
        for draw in recent_data:
            front_numbers.extend(draw['front_numbers'])
            back_numbers.extend(draw['back_numbers'])
        front_freq = Counter(front_numbers)
        back_freq = Counter(back_numbers)
        front_theory = periods * 5 / 35
        back_theory = periods * 2 / 12
        return {
            'front_frequency': dict(front_freq),
            'back_frequency': dict(back_freq),
            'front_theory': front_theory,
            'back_theory': back_theory,
            'periods': periods
        }
    def analyze_trends(self, history_data: List[Dict], periods: int = 30) -> Dict:
        recent_data = history_data[:periods]
        front_matrix = np.zeros((periods, 35))
        back_matrix = np.zeros((periods, 12))
        for i, draw in enumerate(recent_data):
            for num in draw['front_numbers']:
                front_matrix[i][num-1] = 1
            for num in draw['back_numbers']:
                back_matrix[i][num-1] = 1
        return {
            'front_trends': front_matrix.tolist(),
            'back_trends': back_matrix.tolist(),
            'periods': periods
        }
