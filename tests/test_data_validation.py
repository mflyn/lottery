#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据验证功能测试
"""

import unittest
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.validation import (
    DataValidator, 
    DataCleaner, 
    validate_lottery_data,
    clean_lottery_data
)

class TestDataValidator(unittest.TestCase):
    """数据验证器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.ssq_validator = DataValidator('ssq')
        self.dlt_validator = DataValidator('dlt')
    
    def test_ssq_valid_data(self):
        """测试双色球有效数据"""
        valid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 8
            }
        ])
        
        result = self.ssq_validator.validate(valid_data)
        self.assertTrue(result['valid'])
        self.assertEqual(result['summary']['error_count'], 0)
    
    def test_ssq_invalid_red_count(self):
        """测试双色球红球数量错误"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25],  # 只有5个红球
                'blue_number': 8
            }
        ])
        
        result = self.ssq_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_ssq_invalid_red_range(self):
        """测试双色球红球范围错误"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 35],  # 35超出范围
                'blue_number': 8
            }
        ])
        
        result = self.ssq_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_ssq_invalid_blue_range(self):
        """测试双色球蓝球范围错误"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 18  # 18超出范围
            }
        ])
        
        result = self.ssq_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_dlt_valid_data(self):
        """测试大乐透有效数据"""
        valid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'front_numbers': [5, 12, 18, 25, 35],
                'back_numbers': [3, 8]
            }
        ])
        
        result = self.dlt_validator.validate(valid_data)
        self.assertTrue(result['valid'])
        self.assertEqual(result['summary']['error_count'], 0)
    
    def test_dlt_invalid_front_count(self):
        """测试大乐透前区数量错误"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'front_numbers': [5, 12, 18, 25],  # 只有4个前区号码
                'back_numbers': [3, 8]
            }
        ])
        
        result = self.dlt_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_dlt_invalid_back_range(self):
        """测试大乐透后区范围错误"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'front_numbers': [5, 12, 18, 25, 35],
                'back_numbers': [3, 15]  # 15超出范围
            }
        ])
        
        result = self.dlt_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_missing_required_columns(self):
        """测试缺少必需列"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001'
                # 缺少号码列
            }
        ])
        
        result = self.ssq_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)
    
    def test_invalid_date_format(self):
        """测试无效日期格式"""
        invalid_data = pd.DataFrame([
            {
                'draw_date': 'invalid-date',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 8
            }
        ])
        
        result = self.ssq_validator.validate(invalid_data)
        self.assertFalse(result['valid'])
        self.assertGreater(result['summary']['error_count'], 0)

class TestDataCleaner(unittest.TestCase):
    """数据清洗器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.ssq_cleaner = DataCleaner('ssq')
        self.dlt_cleaner = DataCleaner('dlt')
    
    def test_clean_ssq_data(self):
        """测试双色球数据清洗"""
        dirty_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': '[1, 5, 12, 18, 25, 33]',  # 字符串格式
                'blue_number': '8'  # 字符串格式
            },
            {
                'draw_date': '2024/01/02',  # 不同日期格式
                'draw_num': '24001002',
                'red_numbers': [2, 6, 13, 19, 26, 32],
                'blue_number': 9
            },
            {
                'draw_date': None,  # 空值
                'draw_num': None,
                'red_numbers': None,
                'blue_number': None
            }
        ])
        
        cleaned_data, report = self.ssq_cleaner.clean_data(dirty_data)
        
        # 验证清洗结果
        self.assertGreater(len(cleaned_data), 0)
        self.assertLess(len(cleaned_data), len(dirty_data))  # 应该移除了无效记录
        self.assertGreater(report['data_quality']['data_quality_score'], 0)
    
    def test_clean_dlt_data(self):
        """测试大乐透数据清洗"""
        dirty_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'front_numbers': '[5, 12, 18, 25, 35]',  # 字符串格式
                'back_numbers': '[3, 8]'  # 字符串格式
            },
            {
                'draw_date': '2024.01.02',  # 不同日期格式
                'draw_num': '24001002',
                'front_numbers': [6, 13, 19, 26, 34],
                'back_numbers': [4, 9]
            }
        ])
        
        cleaned_data, report = self.dlt_cleaner.clean_data(dirty_data)
        
        # 验证清洗结果
        self.assertEqual(len(cleaned_data), 2)  # 应该保留两条有效记录
        self.assertGreater(report['data_quality']['data_quality_score'], 80)
    
    def test_auto_fix_numeric_fields(self):
        """测试自动修复数值字段"""
        dirty_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 8,
                'sales': '1,234,567',  # 带逗号的数字
                'prize_pool': '¥9,876,543'  # 带货币符号的数字
            }
        ])
        
        cleaned_data, report = self.ssq_cleaner.clean_data(dirty_data, auto_fix=True)
        
        # 验证数值字段被正确清理
        self.assertIsInstance(cleaned_data['sales'].iloc[0], (int, float))
        self.assertIsInstance(cleaned_data['prize_pool'].iloc[0], (int, float))
    
    def test_remove_duplicates(self):
        """测试移除重复记录"""
        duplicate_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 8
            },
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',  # 重复期号
                'red_numbers': [2, 6, 13, 19, 26, 32],
                'blue_number': 9
            },
            {
                'draw_date': '2024-01-02',
                'draw_num': '24001002',
                'red_numbers': [3, 7, 14, 20, 27, 31],
                'blue_number': 10
            }
        ])
        
        cleaned_data, report = self.ssq_cleaner.clean_data(duplicate_data)
        
        # 验证重复记录被移除
        self.assertEqual(len(cleaned_data), 2)
        self.assertEqual(len(cleaned_data['draw_num'].unique()), 2)

class TestConvenienceFunctions(unittest.TestCase):
    """便捷函数测试"""
    
    def test_validate_lottery_data_function(self):
        """测试验证彩票数据便捷函数"""
        test_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': [1, 5, 12, 18, 25, 33],
                'blue_number': 8
            }
        ])
        
        result = validate_lottery_data(test_data, 'ssq')
        self.assertIn('valid', result)
        self.assertIn('summary', result)
    
    def test_clean_lottery_data_function(self):
        """测试清洗彩票数据便捷函数"""
        test_data = pd.DataFrame([
            {
                'draw_date': '2024-01-01',
                'draw_num': '24001001',
                'red_numbers': '[1, 5, 12, 18, 25, 33]',
                'blue_number': '8'
            }
        ])
        
        cleaned_data, report = clean_lottery_data(test_data, 'ssq')
        self.assertIsInstance(cleaned_data, pd.DataFrame)
        self.assertIn('data_quality', report)

if __name__ == '__main__':
    unittest.main() 