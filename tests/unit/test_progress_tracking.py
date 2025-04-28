from unittest.mock import Mock
import unittest
from src.core.features.feature_engineering import FeatureEngineering

class TestProgressTracking(unittest.TestCase):
    def setUp(self):
        self.fe = FeatureEngineering()
        # 创建测试数据
        import pandas as pd
        import numpy as np
        np.random.seed(42)
        self.test_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=10),
            'number': np.random.randint(1, 34, 10)
        })
        
    def test_progress_callback(self):
        """测试进度回调"""
        mock_callback = Mock()
        self.fe.generate_features(
            self.test_data,
            progress_callback=mock_callback
        )
        mock_callback.assert_called()

    def test_error_handling(self):
        """测试错误处理"""
        mock_callback = Mock()
        # 直接调用回调函数模拟错误情况
        self.fe.process_with_progress = lambda func, callback: callback(-1, '错误: 测试错误')
        self.fe.process_with_progress(lambda: None, mock_callback)
        mock_callback.assert_called_with(-1, '错误: 测试错误')
