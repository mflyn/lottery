import unittest
import pandas as pd
import numpy as np
from src.core.features.feature_validator import FeatureValidator

class TestFeatureValidator(unittest.TestCase):
    def setUp(self):
        self.validator = FeatureValidator()
        self.test_features = pd.DataFrame({
            'number_frequency': [1, 2, 3],
            'sum_stats': [10, 20, 30],
            'mean_stats': [5, 10, 15],
            'gap_patterns': [1, 0, 1],
            'winning_patterns': [2, 1, 2]
        })

    def test_feature_completeness(self):
        """测试特征完整性验证"""
        # 创建测试数据
        features = pd.DataFrame({
            'number_frequency': [0.5, 0.3, 0.7],
            'sum_stats': [10, 20, 30],
            'mean_stats': [5, 10, 15]
        })
        
        results = self.validator.validate_features(
            features,
            lottery_type='ssq',
            feature_type='basic'
        )
        
        # 验证返回值类型
        self.assertIsInstance(results, dict)
        
        # 验证基本验证结果
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['issues']), 0)
        
        # 验证数值范围
        self.assertTrue(all(0 <= x <= 1 for x in features['number_frequency']))
        self.assertTrue(all(isinstance(x, (int, float)) for x in features['sum_stats']))
        self.assertTrue(all(isinstance(x, (int, float)) for x in features['mean_stats']))

    def test_range_validation(self):
        """测试数值范围验证"""
        outlier_features = self.test_features.copy()
        # 设置一个足够大的异常值，确保会被检测为极端值
        outlier_features.loc[0, 'number_frequency'] = 1e7  # 设置为1千万，超过1e6阈值
        
        results = self.validator.validate_features(
            outlier_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        
        # 验证结果应该包含警告信息
        self.assertFalse(results['is_valid'], "当有极端值警告时，is_valid应为False")
        self.assertTrue(any('极端值' in warning for warning in results['warnings']), "应该有关于极端值的警告")

    def test_value_validation(self):
        """测试数值有效性验证"""
        invalid_features = self.test_features.copy()
        # 将 number_frequency 列转换为 float 类型后再设置无效值
        invalid_features['number_frequency'] = invalid_features['number_frequency'].astype(float)
        invalid_features.loc[0, 'number_frequency'] = np.inf  # 设置无效值
        
        # 使用_check_values方法直接测试无效值检测
        is_valid = self.validator._check_values(invalid_features)
        self.assertFalse(is_valid, "应该检测到无效值(np.inf)")
        
        # 测试validate_features方法
        results = self.validator.validate_features(
            invalid_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        
        # 检查是否有警告信息
        self.assertTrue(len(results['warnings']) > 0 or len(results['issues']) > 0)
