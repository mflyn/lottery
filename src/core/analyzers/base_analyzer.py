#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础分析器模块
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging


class BaseAnalyzer(ABC):
    """分析器基类"""
    
    def __init__(self, lottery_type: str = 'ssq'):
        """初始化分析器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
        """
        self.lottery_type = lottery_type
        self.logger = logging.getLogger(__name__)
        
        # 设置彩票相关参数
        if lottery_type == 'ssq':
            self.red_columns = [f'red_{i}' for i in range(1, 7)]
            self.blue_columns = ['blue_1']  # 修正为实际的列名
            self.red_range = (1, 33)
            self.blue_range = (1, 16)
            self.config = {
                'red_range': (1, 33),
                'blue_range': (1, 16)
            }
        elif lottery_type == 'dlt':
            self.red_columns = [f'front_{i}' for i in range(1, 6)]
            self.blue_columns = [f'back_{i}' for i in range(1, 3)]
            self.red_range = (1, 35)
            self.blue_range = (1, 12)
            self.config = {
                'front_range': (1, 35),
                'back_range': (1, 12)
            }
        else:
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
    
    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析数据
        
        Args:
            data: 历史数据DataFrame
            
        Returns:
            分析结果字典
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据格式
        
        Args:
            data: 待验证的数据
            
        Returns:
            验证结果
        """
        if data is None or data.empty:
            self.logger.warning("数据为空")
            return False
        
        # 检查必要的列
        required_columns = self.red_columns + self.blue_columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            self.logger.warning(f"缺少必要的列: {missing_columns}")
            return False
        
        return True
    
    def get_red_numbers(self, data: pd.DataFrame) -> np.ndarray:
        """获取红球号码数组
        
        Args:
            data: 历史数据
            
        Returns:
            红球号码数组
        """
        return data[self.red_columns].values
    
    def get_blue_numbers(self, data: pd.DataFrame) -> np.ndarray:
        """获取蓝球号码数组
        
        Args:
            data: 历史数据
            
        Returns:
            蓝球号码数组
        """
        return data[self.blue_columns].values
    
    def calculate_basic_stats(self, numbers: np.ndarray) -> Dict[str, float]:
        """计算基础统计信息
        
        Args:
            numbers: 号码数组
            
        Returns:
            统计信息字典
        """
        return {
            'mean': np.mean(numbers),
            'std': np.std(numbers),
            'min': np.min(numbers),
            'max': np.max(numbers),
            'median': np.median(numbers)
        }
    
    def extract_numbers(self, data: pd.DataFrame, column_name: str) -> List[List[int]]:
        """从数据中提取号码列表
        
        Args:
            data: 历史数据
            column_name: 列名 ('red_numbers', 'front_numbers', 'back_numbers')
            
        Returns:
            号码列表的列表
        """
        if column_name not in data.columns:
            self.logger.warning(f"列 {column_name} 不存在")
            return []
        
        numbers_list = []
        for _, row in data.iterrows():
            value = row[column_name]
            # 安全的空值检查
            if value is not None and isinstance(value, list) and len(value) > 0:
                # 确保列表中的元素不是NaN
                try:
                    if not any(pd.isna(x) for x in value):
                        numbers_list.append(value)
                except:
                    # 如果检查失败，直接添加（可能是整数列表）
                    numbers_list.append(value)
        
        return numbers_list
    
    def calculate_frequency(self, numbers_list: List[List[int]], number_range: tuple) -> Dict[int, int]:
        """计算号码频率
        
        Args:
            numbers_list: 号码列表的列表
            number_range: 号码范围 (min, max)
            
        Returns:
            频率字典
        """
        from collections import Counter
        
        # 展平所有号码
        all_numbers = []
        for numbers in numbers_list:
            all_numbers.extend(numbers)
        
        # 计算频率
        counter = Counter(all_numbers)
        
        # 确保所有可能的号码都在结果中
        frequency = {}
        for num in range(number_range[0], number_range[1] + 1):
            frequency[num] = counter.get(num, 0)
        
        return frequency
    
    def calculate_missing_values(self, numbers_list: List[List[int]], number_range: tuple) -> Dict[int, int]:
        """计算号码遗漏值
        
        Args:
            numbers_list: 号码列表的列表
            number_range: 号码范围
            
        Returns:
            遗漏值字典
        """
        missing_values = {}
        
        for num in range(number_range[0], number_range[1] + 1):
            missing_count = 0
            for numbers in reversed(numbers_list):  # 从最新开始
                if num in numbers:
                    break
                missing_count += 1
            missing_values[num] = missing_count
        
        return missing_values
    
    def classify_hot_cold_numbers(self, frequency: Dict[int, int]) -> Dict[str, List[int]]:
        """分类热号、冷号、正常号
        
        Args:
            frequency: 频率字典
            
        Returns:
            分类结果
        """
        if not frequency:
            return {'hot': [], 'cold': [], 'normal': []}
        
        frequencies = list(frequency.values())
        avg_freq = np.mean(frequencies)
        std_freq = np.std(frequencies)
        
        hot_threshold = avg_freq + std_freq * 0.5
        cold_threshold = avg_freq - std_freq * 0.5
        
        hot_numbers = [num for num, freq in frequency.items() if freq >= hot_threshold]
        cold_numbers = [num for num, freq in frequency.items() if freq <= cold_threshold]
        normal_numbers = [num for num, freq in frequency.items() 
                         if cold_threshold < freq < hot_threshold]
        
        return {
            'hot': sorted(hot_numbers),
            'cold': sorted(cold_numbers),
            'normal': sorted(normal_numbers)
        }
    
    def calculate_statistics(self, numbers_list: List[List[int]]) -> Dict[str, float]:
        """计算统计信息
        
        Args:
            numbers_list: 号码列表的列表
            
        Returns:
            统计信息字典
        """
        if not numbers_list:
            return {}
        
        all_numbers = []
        for numbers in numbers_list:
            all_numbers.extend(numbers)
        
        return {
            'mean': np.mean(all_numbers),
            'std': np.std(all_numbers),
            'min': np.min(all_numbers),
            'max': np.max(all_numbers),
            'median': np.median(all_numbers),
            'total_count': len(all_numbers)
        }
    
    def analyze_patterns(self, numbers_list: List[List[int]]) -> Dict[str, Any]:
        """分析号码模式
        
        Args:
            numbers_list: 号码列表的列表
            
        Returns:
            模式分析结果
        """
        if not numbers_list:
            return {}
        
        # 简单的模式分析
        consecutive_counts = []
        odd_even_ratios = []
        
        for numbers in numbers_list:
            sorted_numbers = sorted(numbers)
            
            # 连号统计
            consecutive = 0
            for i in range(1, len(sorted_numbers)):
                if sorted_numbers[i] - sorted_numbers[i-1] == 1:
                    consecutive += 1
            consecutive_counts.append(consecutive)
            
            # 奇偶比例
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            odd_even_ratios.append(odd_count / len(numbers))
        
        return {
            'avg_consecutive': np.mean(consecutive_counts),
            'avg_odd_ratio': np.mean(odd_even_ratios),
            'pattern_count': len(numbers_list)
        }
    
    def analyze_trends(self, numbers_list: List[List[int]], window_size: int = 10) -> Dict[str, Any]:
        """分析趋势
        
        Args:
            numbers_list: 号码列表的列表
            window_size: 窗口大小
            
        Returns:
            趋势分析结果
        """
        if len(numbers_list) < window_size:
            return {}
        
        # 简单的趋势分析
        trends = []
        for i in range(len(numbers_list) - window_size + 1):
            window_data = numbers_list[i:i + window_size]
            window_numbers = []
            for numbers in window_data:
                window_numbers.extend(numbers)
            trends.append(np.mean(window_numbers))
        
        return {
            'trend_values': trends,
            'trend_direction': 'increasing' if trends[-1] > trends[0] else 'decreasing',
            'window_size': window_size
        }
    
    def get_recent_data(self, periods: int) -> pd.DataFrame:
        """获取最近的数据
        
        Args:
            periods: 期数
            
        Returns:
            最近的数据
        """
        # 这里需要从数据管理器获取数据
        # 暂时返回空DataFrame，子类可以重写此方法
        from ..data_manager import LotteryDataManager
        dm = LotteryDataManager()
        return dm.get_history_data(self.lottery_type, periods)
    
    def format_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化分析结果
        
        Args:
            result: 原始结果
            
        Returns:
            格式化后的结果
        """
        return {
            'success': True,
            'analyzer': self.__class__.__name__,
            'lottery_type': self.lottery_type,
            'data': result,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要
        
        Returns:
            分析摘要字典
        """
        return {
            'analyzer_type': self.__class__.__name__,
            'lottery_type': self.lottery_type,
            'red_range': self.red_range,
            'blue_range': self.blue_range
        } 