import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.core.features.feature_engineering import FeatureEngineering, FeatureProcessor

class TestFeatureEngineering(unittest.TestCase):
    """特征工程模块单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据
        self.test_data = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=20),
            'red_numbers': [[1, 5, 10, 15, 20, 25]] * 20,
            'blue': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'red_sum': [76] * 20,
            'blue_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        # 创建模拟对象
        self.mock_processor = MagicMock(spec=FeatureProcessor)
        self.mock_processor.extract_basic_features.return_value = pd.DataFrame({
            'basic_feature1': range(20),
            'basic_feature2': range(20, 40)
        })
        self.mock_processor.extract_advanced_features.return_value = pd.DataFrame({
            'advanced_feature1': range(40, 60),
            'advanced_feature2': range(60, 80)
        })
        self.mock_processor.normalize_features.return_value = pd.DataFrame({
            'norm_feature1': np.random.random(20),
            'norm_feature2': np.random.random(20)
        })
        self.mock_processor.calculate_feature_importance.return_value = {
            'norm_feature1': 0.7,
            'norm_feature2': 0.3
        }
        self.mock_processor.feature_importance = {
            'norm_feature1': 0.7,
            'norm_feature2': 0.3
        }
        
        # 创建模拟数据管理器
        self.mock_data_manager = MagicMock()
        self.mock_data_manager.get_history_data.return_value = self.test_data
        
    def test_init(self):
        """测试初始化"""
        # 测试有效的彩票类型
        fe = FeatureEngineering('ssq')
        self.assertEqual(fe.lottery_type, 'ssq')
        self.assertIsNotNone(fe.processor)
        
        # 测试无效的彩票类型
        fe = FeatureEngineering('invalid')
        self.assertEqual(fe.lottery_type, 'invalid')
        self.assertIsNone(fe.processor)
        
        # 测试不指定彩票类型
        fe = FeatureEngineering()
        self.assertIsNone(fe.lottery_type)
        self.assertIsNone(fe.processor)
        
    @patch('src.core.features.feature_engineering.SSQFeatureProcessor')
    @patch('src.core.features.feature_engineering.LotteryDataManager')
    def test_generate_features(self, mock_data_manager_class, mock_processor_class):
        """测试生成特征"""
        # 设置模拟对象
        mock_processor_class.return_value = self.mock_processor
        mock_data_manager_class.return_value = self.mock_data_manager
        
        # 创建特征工程对象
        fe = FeatureEngineering('ssq')
        
        # 测试生成特征
        result = fe.generate_features(100)
        
        # 验证结果
        self.assertIn('raw_features', result)
        self.assertIn('normalized_features', result)
        self.assertIn('feature_importance', result)
        self.assertIn('basic_features', result)
        self.assertIn('advanced_features', result)
        
        # 验证调用
        self.mock_data_manager.get_history_data.assert_called_once_with('ssq', 100)
        self.mock_processor.extract_basic_features.assert_called_once()
        self.mock_processor.extract_advanced_features.assert_called_once()
        self.mock_processor.normalize_features.assert_called_once()
        self.mock_processor.calculate_feature_importance.assert_called_once()
        
    def test_generate_features_no_processor(self):
        """测试没有处理器时生成特征"""
        fe = FeatureEngineering()
        
        # 应该抛出异常
        with self.assertRaises(ValueError):
            fe.generate_features()
            
    def test_get_feature_importance_report(self):
        """测试获取特征重要性报告"""
        # 设置模拟对象
        fe = FeatureEngineering('ssq')
        fe.processor = self.mock_processor
        
        # 测试获取报告
        report = fe.get_feature_importance_report()
        
        # 验证结果
        self.assertIsInstance(report, pd.DataFrame)
        self.assertEqual(len(report), 2)  # 两个特征
        self.assertIn('feature', report.columns)
        self.assertIn('importance', report.columns)
        self.assertIn('importance_normalized', report.columns)
        self.assertIn('cumulative_importance', report.columns)
        
    def test_extract_temporal_features(self):
        """测试提取时间序列特征"""
        fe = FeatureEngineering()
        
        # 测试提取特征
        features = fe._extract_temporal_features(self.test_data)
        
        # 验证结果
        self.assertIsInstance(features, pd.DataFrame)
        self.assertIn('day_of_week', features.columns)
        self.assertIn('month', features.columns)
        self.assertIn('season', features.columns)
        
        # 测试滞后特征
        for lag in [1, 3, 5, 7, 14]:
            self.assertIn(f'red_sum_lag_{lag}', features.columns)
            self.assertIn(f'blue_lag_{lag}', features.columns)
            
        # 测试滚动统计
        for window in [5, 10, 20]:
            self.assertIn(f'red_mean_{window}', features.columns)
            self.assertIn(f'red_std_{window}', features.columns)
            
    def test_extract_combination_features(self):
        """测试提取组合特征"""
        fe = FeatureEngineering()
        
        # 测试提取特征
        features = fe._extract_combination_features(self.test_data)
        
        # 验证结果
        self.assertIsInstance(features, pd.DataFrame)
        self.assertIn('consecutive_pairs', features.columns)
        self.assertIn('number_span', features.columns)
        self.assertIn('sum_digits', features.columns)
        
        # 验证区间分布
        self.assertIn('zone_1_11', features.columns)
        self.assertIn('zone_12_22', features.columns)
        self.assertIn('zone_23_33', features.columns)
        
    def test_extract_statistical_features(self):
        """测试提取统计特征"""
        fe = FeatureEngineering()
        
        # 测试提取特征
        features = fe._extract_statistical_features(self.test_data)
        
        # 验证结果
        self.assertIsInstance(features, pd.DataFrame)
        self.assertIn('mean', features.columns)
        self.assertIn('std', features.columns)
        self.assertIn('median', features.columns)
        self.assertIn('skewness', features.columns)
        self.assertIn('kurtosis', features.columns)
        
    def test_select_features(self):
        """测试特征选择"""
        fe = FeatureEngineering()
        
        # 创建测试数据
        features_df = pd.DataFrame({
            'feature1': np.random.random(20),
            'feature2': np.random.random(20),
            'feature3': np.random.random(20),
            'feature4': np.random.random(20),
            'feature5': np.random.random(20)
        })
        target = pd.Series(np.random.randint(0, 2, 20))
        
        # 测试特征选择
        with patch('src.core.features.feature_engineering.SelectKBest'):
            selected = fe.select_features(features_df, target, k=3)
            
            # 验证结果
            self.assertIsInstance(selected, pd.DataFrame)
            self.assertIsInstance(fe.feature_scores, dict)

if __name__ == '__main__':
    unittest.main()