import numpy as np
import pandas as pd
from typing import List, Dict

def analyze_number_patterns(numbers: List[int]) -> Dict:
    """分析号码模式
    - 奇偶比例
    - 大小比例
    - 连号特征
    - 间隔特征
    """
    patterns = {
        'odd_even_ratio': len([x for x in numbers if x % 2 == 1]) / len(numbers),
        'high_low_ratio': len([x for x in numbers if x > 16]) / len(numbers),
        'consecutive_count': _count_consecutive(sorted(numbers)),
        'gap_features': _analyze_gaps(sorted(numbers))
    }
    return patterns

def extract_temporal_features(historical_data: pd.DataFrame) -> pd.DataFrame:
    """提取时间序列特征
    - 周期性特征
    - 趋势特征
    - 滞后特征
    """
    features = pd.DataFrame()
    
    # 添加日期相关特征
    features['dayofweek'] = historical_data['date'].dt.dayofweek
    features['month'] = historical_data['date'].dt.month
    features['year'] = historical_data['date'].dt.year
    
    # 添加滞后特征
    for lag in [1, 3, 5, 7]:
        features[f'lag_{lag}'] = historical_data['number'].shift(lag)
        
    # 添加滚动统计特征
    for window in [5, 10, 20]:
        features[f'rolling_mean_{window}'] = historical_data['number'].rolling(window).mean()
        features[f'rolling_std_{window}'] = historical_data['number'].rolling(window).std()
        
    return features

def _count_consecutive(numbers: List[int]) -> int:
    """计算连号数量"""
    count = 0
    for i in range(len(numbers)-1):
        if numbers[i+1] - numbers[i] == 1:
            count += 1
    return count

def _analyze_gaps(numbers: List[int]) -> Dict:
    """分析号码间隔"""
    gaps = np.diff(numbers)
    return {
        'max_gap': np.max(gaps),
        'min_gap': np.min(gaps),
        'mean_gap': np.mean(gaps),
        'std_gap': np.std(gaps)
    }