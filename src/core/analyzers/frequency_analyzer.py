from typing import Dict, List, Any
import pandas as pd
import numpy as np
from collections import Counter # 导入 Counter

class FrequencyAnalyzer:
    """号码频率分析器"""
    
    def __init__(self, lottery_type: str):
        """
        Args:
            lottery_type: 彩票类型 ('dlt' 或 'ssq')
        """
        self.lottery_type = lottery_type
        # 定义号码范围
        if lottery_type == 'ssq':
            self.red_range = range(1, 34) # 1-33
            self.blue_range = range(1, 17) # 1-16
        elif lottery_type == 'dlt':
            self.front_range = range(1, 36) # 1-35
            self.back_range = range(1, 13) # 1-12
        else:
            raise ValueError(f"Unknown lottery type: {lottery_type}")
        
    def analyze(self, history_data: pd.DataFrame) -> Dict:
        """分析历史数据中的号码频率
        
        Args:
            history_data: 历史开奖数据 (需要包含号码列表列)
            
        Returns:
            Dict: 频率分析结果
        """
        results = {}
        if self.lottery_type == 'ssq':
            if 'red_numbers' in history_data.columns:
                results['red'] = self._analyze_frequency(history_data['red_numbers'], self.red_range)
            if 'blue_numbers' in history_data.columns: # 确认列名是 blue_numbers
                results['blue'] = self._analyze_frequency(history_data['blue_numbers'], self.blue_range)
        elif self.lottery_type == 'dlt':
            if 'front_numbers' in history_data.columns:
                results['front'] = self._analyze_frequency(history_data['front_numbers'], self.front_range)
            if 'back_numbers' in history_data.columns:
                results['back'] = self._analyze_frequency(history_data['back_numbers'], self.back_range)
        return results
            
    def _analyze_frequency(self, numbers_series: pd.Series, num_range: range) -> Dict[str, Any]:
        """分析号码出现频率 (通用实现)
        
        Args:
            numbers_series: 包含号码列表的 Pandas Series
            num_range: 号码的有效范围 (e.g., range(1, 34))
            
        Returns:
            Dict: 包含频率、热号、冷号的字典
        """
        # 1. 展平所有号码列表到一个大列表
        #    需要处理 Series 中的 None 或空列表
        all_numbers = []
        for num_list in numbers_series.dropna(): # dropna 避免处理 None
            if isinstance(num_list, list):
                all_numbers.extend(num_list)
            elif isinstance(num_list, (int, np.integer)): # 处理单个数字的情况 (如旧的 blue_number)
                all_numbers.append(int(num_list))

        if not all_numbers:
            return {'frequencies': {}, 'hot_numbers': [], 'cold_numbers': list(num_range)}

        # 2. 计算每个号码的出现次数
        total_draws = len(numbers_series.dropna()) # 有效期数
        counts = Counter(all_numbers)

        # 3. 补全未出现的号码，计数为 0
        full_counts = {num: counts.get(num, 0) for num in num_range}

        # 4. 计算频率 (出现次数 / 有效期数)
        #    注意：对于红球/前区，一期出多个号，用总次数/总号码数更合适？
        #    暂时先用 次数/期数，表示这个号在多少期里出现过
        #    或者直接用次数？这里先用次数。
        # frequencies = {str(num): count / total_draws for num, count in full_counts.items()}
        frequencies_by_count = {str(num): count for num, count in full_counts.items()}

        # 5. 找出热号和冷号 (按出现次数排序)
        sorted_numbers = sorted(full_counts.items(), key=lambda item: item[1], reverse=True)

        num_hot_cold = 3 # 定义取多少个热号/冷号
        hot_numbers = [num for num, count in sorted_numbers[:num_hot_cold]]
        # 冷号是反向排序，取前面的
        cold_numbers = [num for num, count in sorted(full_counts.items(), key=lambda item: item[1])[:num_hot_cold]]

        return {
            'frequencies': frequencies_by_count, # 返回次数，而不是频率
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers
        }
