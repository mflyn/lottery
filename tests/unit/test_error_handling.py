import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.utils.error_handler import ErrorHandler
from src.core.features.feature_engineering import FeatureEngineering

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.error_handler = ErrorHandler()
        self.feature_engineering = FeatureEngineering()
    
    def test_handle_value_error(self):
        """测试处理ValueError"""
        # 创建一个会引发ValueError的函数
        def raise_value_error():
            raise ValueError("测试值错误")
        
        # 使用错误处理器
        result = self.error_handler.safe_execute(raise_value_error)
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'ValueError')
        self.assertEqual(result['error_message'], '测试值错误')
    
    def test_handle_key_error(self):
        """测试处理KeyError"""
        # 创建一个会引发KeyError的函数
        def raise_key_error():
            d = {}
            return d['nonexistent']
        
        # 使用错误处理器
        result = self.error_handler.safe_execute(raise_key_error)
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'KeyError')
    
    def test_handle_file_not_found(self):
        """测试处理FileNotFoundError"""
        # 创建一个会引发FileNotFoundError的函数
        def raise_file_not_found():
            with open('nonexistent_file.txt', 'r') as f:
                return f.read()
        
        # 使用错误处理器
        result = self.error_handler.safe_execute(raise_file_not_found)
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'FileNotFoundError')
    
    def test_successful_execution(self):
        """测试成功执行"""
        # 创建一个正常函数
        def normal_function():
            return "成功"
        
        # 使用错误处理器
        result = self.error_handler.safe_execute(normal_function)
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], "成功")
    
    @patch('src.core.features.feature_engineering.FeatureEngineering.generate_features')
    def test_feature_engineering_error(self, mock_generate):
        """测试特征工程错误处理"""
        # 设置模拟对象抛出异常
        mock_generate.side_effect = ValueError("特征生成错误")
        
        # 使用错误处理器
        result = self.error_handler.safe_execute(
            self.feature_engineering.generate_features,
            lottery_type='ssq'
        )
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'ValueError')
        self.assertEqual(result['error_message'], '特征生成错误')