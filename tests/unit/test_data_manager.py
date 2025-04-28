import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
import numpy as np
import json
import os
from src.data.data_manager import DataManager

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.data_manager = DataManager()
        
        # 模拟数据
        self.mock_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-08'],
            'red_1': [1, 10],
            'red_2': [2, 11],
            'red_3': [3, 12],
            'red_4': [4, 13],
            'red_5': [5, 14],
            'red_6': [6, 15],
            'blue': [7, 16]
        })
    
    @patch('src.data.data_manager.pd.read_csv')
    def test_load_lottery_data(self, mock_read_csv):
        """测试加载彩票数据"""
        # 设置模拟返回值
        mock_read_csv.return_value = self.mock_data
        
        # 调用方法
        result = self.data_manager.load_lottery_data('ssq')
        
        # 验证结果
        self.assertIsNotNone(result)
        mock_read_csv.assert_called_once()
    
    @patch('src.data.data_manager.pd.read_csv')
    def test_load_lottery_data_with_filter(self, mock_read_csv):
        """测试加载并过滤彩票数据"""
        # 设置模拟返回值
        mock_read_csv.return_value = self.mock_data
        
        # 调用方法
        result = self.data_manager.load_lottery_data('ssq', start_date='2023-01-05')
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)  # 应该只有一条记录
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_json_data(self, mock_json_load, mock_file_open):
        """测试加载JSON数据"""
        # 设置模拟返回值
        mock_json_data = {'data': [1, 2, 3]}
        mock_json_load.return_value = mock_json_data
        
        # 调用方法
        result = self.data_manager.load_json_data('test.json')
        
        # 验证结果
        self.assertEqual(result, mock_json_data)
        mock_file_open.assert_called_once_with('test.json', 'r', encoding='utf-8')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_json_data(self, mock_json_dump, mock_file_open):
        """测试保存JSON数据"""
        # 测试数据
        test_data = {'data': [1, 2, 3]}
        
        # 调用方法
        result = self.data_manager.save_json_data(test_data, 'test.json')
        
        # 验证结果
        self.assertTrue(result)
        mock_file_open.assert_called_once_with('test.json', 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
    
    @patch('src.data.data_manager.requests.get')
    def test_fetch_online_data(self, mock_get):
        """测试获取在线数据"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'date': '2023-01-01', 'numbers': [1, 2, 3, 4, 5, 6, 7]}]}
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.data_manager.fetch_online_data('ssq', 1)
        
        # 验证结果
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
    
    def test_preprocess_data(self):
        """测试数据预处理"""
        # 调用方法
        result = self.data_manager.preprocess_data(self.mock_data)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn('date', result.columns)
        
    def test_validate_data(self):
        """测试数据验证"""
        # 有效数据
        valid_result = self.data_manager.validate_data(self.mock_data)
        self.assertTrue(valid_result)
        
        # 无效数据 - 缺少必要列
        invalid_data = pd.DataFrame({'invalid': [1, 2]})
        invalid_result = self.data_manager.validate_data(invalid_data)
        self.assertFalse(invalid_result)
    
    @patch('src.data.data_manager.pd.DataFrame.to_csv')
    def test_export_data(self, mock_to_csv):
        """测试数据导出"""
        # 调用方法
        result = self.data_manager.export_data(self.mock_data, 'test_export.csv')
        
        # 验证结果
        self.assertTrue(result)
        mock_to_csv.assert_called_once()