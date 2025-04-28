import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class FeatureValidator:
    """特征验证器，用于验证特征的正确性和完整性"""
    
    def __init__(self):
        # 定义各彩票类型的必需特征
        self.required_features = {
            'ssq': {
                'basic': ['number_frequency', 'sum_stats', 'mean_stats'],
                'advanced': ['trend_features', 'pattern_features', 'statistical_features']
            },
            'dlt': {
                'basic': ['number_frequency', 'sum_stats', 'mean_stats'],
                'advanced': ['trend_features', 'pattern_features', 'statistical_features']
            }
        }
        
        # 定义特征值的合法范围
        self.feature_ranges = {
            'number_frequency': (0, float('inf')),
            'sum_stats': (0, float('inf')),
            'mean_stats': (0, float('inf')),
            'trend_features': (-float('inf'), float('inf')),
            'pattern_features': (0, 1),
            'statistical_features': (-float('inf'), float('inf'))
        }

        self.valid_ranges = {
            'number_frequency': (0, 1),
            'gap_days': (1, 365),
            'sum_value': (0, float('inf'))
        }

    def validate_features(self, features: pd.DataFrame, lottery_type: str, feature_type: str) -> Dict:
        """验证特征数据的有效性"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': []
        }
        
        # 基本验证
        if features.empty:
            validation_result['is_valid'] = False
            validation_result['issues'].append("特征数据不能为空")
            return validation_result
        
        # 检查缺失值
        if features.isnull().any().any():
            validation_result['is_valid'] = False
            validation_result['issues'].append("特征数据包含缺失值")
        
        # 检查极端值
        # 1. 使用绝对阈值
        ABSOLUTE_THRESHOLD = 1e6  # 设置绝对阈值为1百万
        has_extreme_values = False
        for column in features.columns:
            # 检查是否超过绝对阈值
            extreme_mask = (features[column].abs() > ABSOLUTE_THRESHOLD)
            if extreme_mask.any():
                extreme_values = features[column][extreme_mask].values.tolist()
                validation_result['warnings'].append(
                    f"特征'{column}'包含极端值(超过{ABSOLUTE_THRESHOLD}): {extreme_values}"
                )
                has_extreme_values = True
                
            # 使用IQR方法检测异常值
            Q1 = features[column].quantile(0.25)
            Q3 = features[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outlier_mask = (features[column] < lower_bound) | (features[column] > upper_bound)
            if outlier_mask.any():
                outlier_values = features[column][outlier_mask].values.tolist()
                validation_result['warnings'].append(
                    f"特征'{column}'包含统计意义上的极端值: {outlier_values}"
                )
                has_extreme_values = True
        
        # 如果存在极端值，将is_valid设置为False
        if has_extreme_values:
            validation_result['is_valid'] = False
        
        # 检查常量特征
        constant_columns = features.columns[features.nunique() == 1].tolist()
        if constant_columns:
            validation_result['issues'].append(f"发现常量特征: {constant_columns}")
        
        # 如果有任何警告，也应该反映在验证结果中
        if validation_result['warnings']:
            validation_result['is_valid'] = False
        
        return validation_result

    def _check_completeness(self, features: pd.DataFrame) -> bool:
        """检查特征完整性"""
        return not features.isnull().any().any()

    def _check_range(self, features: pd.DataFrame) -> bool:
        """检查特征值是否在有效范围内"""
        for col, (min_val, max_val) in self.valid_ranges.items():
            if col in features.columns:
                if not all((features[col] >= min_val) & (features[col] <= max_val)):
                    return False
        return True

    def _check_values(self, features: pd.DataFrame) -> bool:
        """检查特征值有效性"""
        return not features.isin([np.inf, -np.inf]).any().any()

    def validate_feature_correlations(self, features: pd.DataFrame, threshold: float = 0.8) -> dict:
        """验证特征之间的相关性"""
        if features.empty:
            return {}

        correlations = {}
        corr_matrix = features.corr()
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > threshold:
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    correlations[col1] = correlations.get(col1, [])
                    correlations[col1].append((col2, float(corr_matrix.iloc[i, j])))

        return correlations

    def check_feature_stability(self, features: pd.DataFrame, window_size: int = 2) -> dict:
        """检查特征的稳定性"""
        stability_scores = {}
        
        for column in features.columns:
            # 计算滚动标准差
            rolling_std = features[column].rolling(window=window_size).std()
            # 计算稳定性分数 (使用标准差的倒数，并归一化到0-1之间)
            stability = 1 / (1 + rolling_std.mean())
            stability_scores[column] = stability
            
        return stability_scores
