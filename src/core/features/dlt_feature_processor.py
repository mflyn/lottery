from typing import Dict, List
import pandas as pd
import numpy as np
from .base_feature_processor import BaseFeatureProcessor

class DLTFeatureProcessor(BaseFeatureProcessor):
    """大乐透特征处理器"""
    
    def extract_basic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """提取基础特征"""
        # 验证输入数据
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if 'front_numbers' not in data.columns or 'back_numbers' not in data.columns:
            raise ValueError("Input DataFrame must contain 'front_numbers' and 'back_numbers' columns")
            
        # 验证数据完整性
        if any(len(x) != 5 for x in data['front_numbers']) or any(len(x) != 2 for x in data['back_numbers']):
            raise ValueError("Invalid number format: front numbers must be 5 numbers, back numbers must be 2 numbers")
        
        # 继续处理特征提取...
        features = pd.DataFrame()
        
        # 前区号码特征
        front_numbers = data['front_numbers'].apply(pd.Series)
        features['front_sum'] = front_numbers.sum(axis=1)
        features['front_mean'] = front_numbers.mean(axis=1)
        features['front_std'] = front_numbers.std(axis=1)
        
        # 后区号码特征
        back_numbers = data['back_numbers'].apply(pd.Series)
        features['back_sum'] = back_numbers.sum(axis=1)
        features['back_mean'] = back_numbers.mean(axis=1)
        
        return features
    
    def extract_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """提取高级特征"""
        features = pd.DataFrame()
        
        # 计算前区号码间隔
        features['front_gaps'] = self.calculate_gaps(data['front_numbers'])
        
        # 计算后区号码间隔
        features['back_gaps'] = self.calculate_gaps(data['back_numbers'])
        
        # 分析前区号码模式
        features['front_patterns'] = self.analyze_patterns(data['front_numbers'])
        
        # 分析后区号码模式
        features['back_patterns'] = self.analyze_patterns(data['back_numbers'])
        
        return features

    def calculate_gaps(self, numbers_series: pd.Series) -> List[List[int]]:
        """计算号码间隔
        
        Args:
            numbers_series: 号码序列
        
        Returns:
            号码间隔列表的列表
        """
        if not isinstance(numbers_series, pd.Series):
            numbers_series = pd.Series(numbers_series)
        
        gaps = []
        for numbers in numbers_series:
            # 确保数据是有序的
            sorted_numbers = sorted(numbers)
            # 计算相邻数字之间的间隔
            number_gaps = []
            for i in range(len(sorted_numbers)-1):
                gap = sorted_numbers[i+1] - sorted_numbers[i]
                number_gaps.append(gap)
            gaps.append(number_gaps)
        
        return gaps

    def analyze_patterns(self, numbers_series: pd.Series) -> List[Dict]:
        """分析号码模式
        
        Args:
            numbers_series: 号码序列
        
        Returns:
            模式特征列表
        """
        patterns = []
        for numbers in numbers_series:
            sorted_numbers = sorted(numbers)
            pattern = {
                'odd_even_ratio': len([x for x in numbers if x % 2 == 1]) / len(numbers),
                'high_low_ratio': len([x for x in numbers if x > (max(numbers) / 2)]) / len(numbers),
                'consecutive_count': sum(1 for i in range(len(sorted_numbers)-1) 
                                      if sorted_numbers[i+1] - sorted_numbers[i] == 1),
                'span': max(numbers) - min(numbers)
            }
            patterns.append(pattern)
        return patterns

    def test_invalid_input(self):
        """测试无效输入处理"""
        invalid_data = pd.DataFrame({
            'front_numbers': [[1, 4, 5]], # 非完整一组
            'back_numbers': [[1], [2]]
        })
        
        with self.assertRaises(ValueError):
            self.processor.extract_basic_features(invalid_data)
