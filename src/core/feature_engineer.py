# src/core/feature_engineer.py
import pandas as pd
from typing import List, Dict, Optional, Set

class FeatureEngineer:
    """负责计算各种彩票特征工程"""

    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type

    def _get_number_columns(self) -> Optional[Dict[str, str]]:
        """根据彩票类型获取号码列名"""
        if self.lottery_type == 'ssq':
            # 注意：需要预处理确保 blue_number 变为了 blue_numbers (list)
            return {'red': 'red_numbers', 'blue': 'blue_numbers'}
        elif self.lottery_type == 'dlt':
            return {'front': 'front_numbers', 'back': 'back_numbers'}
        else:
            print(f"错误：不支持的彩票类型 {self.lottery_type}")
            return None

    def calculate_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算红球/前区和值"""
        num_cols = self._get_number_columns()
        if not num_cols: return df

        area_col = num_cols.get('red') or num_cols.get('front')
        if area_col and area_col in df.columns:
            df[f'{area_col}_sum'] = df[area_col].apply(lambda x: sum(x) if isinstance(x, list) else None)
        return df

    def calculate_odd_even_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算各区域奇偶比"""
        num_cols = self._get_number_columns()
        if not num_cols: return df

        for area, col_name in num_cols.items():
            if col_name in df.columns:
                def get_ratio(numbers):
                    if not isinstance(numbers, list) or not numbers: return None
                    odd_count = sum(1 for n in numbers if n % 2 != 0)
                    even_count = len(numbers) - odd_count
                    return f"{odd_count}:{even_count}"
                df[f'{area}_odd_even_ratio'] = df[col_name].apply(get_ratio)
        return df

    def calculate_big_small_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算各区域大小比"""
        num_cols = self._get_number_columns()
        if not num_cols: return df

        thresholds = {}
        if self.lottery_type == 'ssq': thresholds = {'red': 17, 'blue': 9}
        elif self.lottery_type == 'dlt': thresholds = {'front': 18, 'back': 7}

        for area, col_name in num_cols.items():
            threshold = thresholds.get(area)
            if threshold and col_name in df.columns:
                def get_ratio(numbers):
                    if not isinstance(numbers, list) or not numbers: return None
                    small_count = sum(1 for n in numbers if n < threshold)
                    large_count = len(numbers) - small_count
                    return f"{small_count}:{large_count}"
                df[f'{area}_big_small_ratio'] = df[col_name].apply(get_ratio)
        return df

    # --- 可以添加更多特征计算方法 ---
    # def calculate_consecutive_numbers(self, df: pd.DataFrame) -> pd.DataFrame: ...
    # def calculate_omissions(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def generate_features(self, df: pd.DataFrame, features_to_generate: List[str]) -> pd.DataFrame:
        """根据请求生成指定的特征列"""
        df_processed = df.copy()

        # 确保号码列存在且格式正确 (特别是 ssq blue)
        # TODO: 调用一个通用的预处理函数，确保号码列是列表形式
        # 例如: df_processed = self._preprocess_data(df_processed)
        # 暂时假设输入 DataFrame 已基本处理好

        if 'sum' in features_to_generate:
            df_processed = self.calculate_sum(df_processed)
        if 'odd_even' in features_to_generate:
            df_processed = self.calculate_odd_even_ratio(df_processed)
        if 'big_small' in features_to_generate:
            df_processed = self.calculate_big_small_ratio(df_processed)
        # ... 调用其他特征计算 ...

        return df_processed 