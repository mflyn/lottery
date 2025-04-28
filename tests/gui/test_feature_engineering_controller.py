import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from src.gui.controllers.feature_engineering_controller import FeatureEngineeringController

class TestFeatureEngineeringController(unittest.TestCase):
    def setUp(self):
        self.view = MagicMock()
        self.model = MagicMock()
        self.controller = FeatureEngineeringController()
        
        # 模拟数据
        self.mock_data = pd.DataFrame({
            'red_1': [1, 2, 3],
            'red_2': [4, 5, 6],
            'blue': [1, 2, 3]
        })
        self.model.get_data.return_value = self.mock_data
        
        # 模拟特征
        self.mock_features = {
            'basic_features': pd.DataFrame({'feature1': [1, 2, 3]}),
            'advanced_features': pd.DataFrame({'feature2': [4, 5, 6]})
        }
        self.model.generate_features.return_value = self.mock_features
    
    def test_initialize(self):
        """测试控制器初始化"""
        self.controller.initialize('ssq')
        # 由于initialize方法现在接受lottery_type参数，不再调用view的方法
        # 检查feature_engineering是否已初始化
        self.assertIsNotNone(self.controller.feature_engineering)
    
    def test_generate_features(self):
        """测试特征生成功能"""
        # 初始化控制器
        self.controller.initialize('ssq')
        
        # 模拟feature_engineering
        self.controller.feature_engineering = MagicMock()
        self.controller.feature_engineering.generate_features.return_value = self.mock_features
        
        # 注册回调函数
        callback = MagicMock()
        self.controller.register_callback('on_feature_generated', callback)
        
        # 调用方法
        self.controller.generate_features(periods=100)
        
        # 验证方法调用
        self.controller.feature_engineering.generate_features.assert_called_once_with(100)
        
        # 验证回调函数被调用
        callback.assert_called_once()
        
    def test_get_feature_importance_report(self):
        """测试获取特征重要性报告功能"""
        # 初始化控制器
        self.controller.initialize('ssq')
        
        # 模拟feature_engineering
        self.controller.feature_engineering = MagicMock()
        self.controller.feature_engineering.get_feature_importance_report.return_value = {'feature1': 0.8, 'feature2': 0.6}
        
        # 调用方法
        report = self.controller.get_feature_importance_report()
        
        # 验证方法调用
        self.controller.feature_engineering.get_feature_importance_report.assert_called_once()
        
        # 验证返回结果
        self.assertIsNotNone(report)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 初始化控制器
        self.controller.initialize('ssq')
        
        # 模拟feature_engineering抛出异常
        self.controller.feature_engineering = MagicMock()
        self.controller.feature_engineering.generate_features.side_effect = ValueError("测试错误")
        
        # 注册错误回调函数
        error_callback = MagicMock()
        self.controller.register_callback('on_error', error_callback)
        
        # 调用方法
        self.controller.generate_features()
        
        # 验证错误回调被调用
        error_callback.assert_called_once()
        
    def test_feature_selection(self):
        """测试特征选择功能"""
        # 初始化控制器
        self.controller.initialize('ssq')
        
        # 模拟数据
        features_df = pd.DataFrame({'feature1': [1, 2, 3], 'feature2': [4, 5, 6]})
        target = pd.Series([0, 1, 0])
        
        # 模拟feature_engineering
        self.controller.feature_engineering = MagicMock()
        self.controller.feature_engineering.select_features.return_value = pd.DataFrame({'selected_feature': [1, 2, 3]})
        
        # 注册回调函数
        callback = MagicMock()
        self.controller.register_callback('on_feature_selected', callback)
        
        # 调用方法
        self.controller.select_features(features_df, target, method='mutual_info', k=5)
        
        # 验证方法调用
        self.controller.feature_engineering.select_features.assert_called_once_with(features_df, target, 'mutual_info', 5)
        
        # 验证回调函数被调用
        callback.assert_called_once()