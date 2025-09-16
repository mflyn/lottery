import unittest
import pandas as pd
from src.core.features.dlt_feature_processor import DLTFeatureProcessor

class TestDLTFeatureProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DLTFeatureProcessor()
        self.test_data = pd.DataFrame({
            'front_numbers': [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]],
            'back_numbers': [[1, 2], [3, 4]],
            'date': ['2024-01-01', '2024-01-02']
        })

    def test_extract_basic_features(self):
        """测试基础特征提取"""
        features = self.processor.extract_basic_features(self.test_data)
        
        self.assertIn('front_sum', features.columns)
        self.assertIn('front_mean', features.columns)
        self.assertIn('front_std', features.columns)
        self.assertIn('back_sum', features.columns)
        self.assertIn('back_mean', features.columns)
        
        # 验证计算结果
        self.assertEqual(features['front_sum'].iloc[0], 15)
        self.assertEqual(features['back_sum'].iloc[0], 3)
        
    def test_extract_advanced_features(self):
        """测试高级特征提取"""
        features = self.processor.extract_advanced_features(self.test_data)
        
        self.assertIn('front_gaps', features.columns)
        self.assertIn('back_gaps', features.columns)
        self.assertIn('front_patterns', features.columns)
        self.assertIn('back_patterns', features.columns)
        
    def test_invalid_input(self):
        """测试无效输入处理"""
        invalid_data = pd.DataFrame({
            'front_numbers': [[1, 2, 3], [4, 5]],  # 长度不一致
            'back_numbers': [[1], [2]]
        })
        
        with self.assertRaises(ValueError):
            self.processor.extract_basic_features(invalid_data)