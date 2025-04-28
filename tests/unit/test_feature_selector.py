import unittest
import pandas as pd
import numpy as np
from src.core.features.feature_selector import FeatureSelector

class TestFeatureSelector(unittest.TestCase):
    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        n_samples = 100
        
        # 创建测试数据
        self.X = pd.DataFrame({
            'feature1': np.random.normal(0, 1, n_samples),
            'feature2': np.random.normal(0, 1, n_samples),
            'feature3': np.random.normal(0, 1, n_samples),
            'feature4': np.random.normal(0, 1, n_samples),
            'feature5': np.random.normal(0, 1, n_samples)
        })
        
        # 创建目标变量 (与feature1和feature2有较强相关性)
        self.y = 0.8 * self.X['feature1'] + 0.5 * self.X['feature2'] + np.random.normal(0, 0.1, n_samples)
        
        self.selector = FeatureSelector()

    def test_mutual_info_selection(self):
        """测试互信息特征选择"""
        self.selector.method = 'mutual_info'
        selected = self.selector.select_features(self.X, self.y, n_features=3)
        
        self.assertEqual(len(selected.columns), 3)
        self.assertIn('feature1', selected.columns)
        self.assertIn('feature2', selected.columns)

    def test_correlation_selection(self):
        """测试相关性特征选择"""
        self.selector.method = 'correlation'
        selected = self.selector.select_features(self.X, self.y, n_features=2)
        
        self.assertEqual(len(selected.columns), 2)
        self.assertIn('feature1', selected.columns)
        self.assertIn('feature2', selected.columns)

    def test_combined_selection(self):
        """测试组合特征选择"""
        self.selector.method = 'combined'
        selected = self.selector.select_features(self.X, self.y, n_features=3)
        
        self.assertEqual(len(selected.columns), 3)
        importance = self.selector.get_feature_importance()
        
        self.assertTrue(len(importance) > 0)
        self.assertTrue(all(0 <= score <= 1 for score in importance.values()))
