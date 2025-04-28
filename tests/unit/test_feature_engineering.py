import unittest
import pandas as pd
import numpy as np
from src.core.features.feature_engineering import FeatureEngineering

class TestFeatureEngineering(unittest.TestCase):
    def setUp(self):
        """测试初始化"""
        self.feature_engineering = FeatureEngineering(lottery_type='ssq')

    def test_basic_feature_generation(self):
        """测试基础特征生成"""
        # 创建测试数据
        np.random.seed(42)  # 设置随机种子以保证结果可重现
        test_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=20),
            'red_1': np.random.randint(1, 34, 20),
            'red_2': np.random.randint(1, 34, 20),
            'red_3': np.random.randint(1, 34, 20),
            'red_4': np.random.randint(1, 34, 20),
            'red_5': np.random.randint(1, 34, 20),
            'red_6': np.random.randint(1, 34, 20),
            'blue': np.random.randint(1, 17, 20)
        })
        
        # 执行特征生成
        result = self.feature_engineering.generate_features(test_data)
        
        # 基本验证
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(test_data))
        
        # 验证特征列存在
        expected_features = {
            'red_sum', 'red_mean', 'red_std',
            'red_odd_count', 'red_even_count',
            'red_prime_count', 'red_consecutive_count',
            'blue_is_prime', 'blue_is_odd'
        }
        
        self.assertTrue(all(feature in result.columns for feature in expected_features))
        
        # 验证特征值范围
        self.assertTrue(all(result['red_sum'] >= 6))  # 最小和为6个1
        self.assertTrue(all(result['red_sum'] <= 198))  # 最大和为6个33
        self.assertTrue(all(result['red_odd_count'] >= 0))
        self.assertTrue(all(result['red_odd_count'] <= 6))
        self.assertTrue(all(result['red_even_count'] >= 0))
        self.assertTrue(all(result['red_even_count'] <= 6))
