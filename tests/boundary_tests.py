import unittest
import pandas as pd
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering

class BoundaryTests(unittest.TestCase):
    """边界条件测试类"""
    
    def setUp(self):
        self.number_generator = LotteryNumberGenerator()
        self.feature_engineering = FeatureEngineering()
    
    def test_empty_input(self):
        """测试空输入"""
        with self.assertRaises(ValueError):
            self.number_generator.generate_numbers([])
    
    def test_max_numbers(self):
        """测试最大号码限制"""
        # 测试大乐透前区超出范围
        with self.assertRaises(ValueError):
            self.number_generator.generate_dlt_numbers(front_numbers=[36])
        
        # 测试大乐透后区超出范围
        with self.assertRaises(ValueError):
            self.number_generator.generate_dlt_numbers(back_numbers=[13])
    
    def test_invalid_dates(self):
        """测试无效日期"""
        with self.assertRaises(ValueError):
            self.feature_engineering.extract_temporal_features("2024-13-01")
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        result = self.number_generator.process_input("test!@#$%^&*()")
        self.assertEqual(result, "test")
    
    def test_memory_limits(self):
        """测试内存限制"""
        import psutil
        
        # 记录初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 执行大量数据处理
        large_data = list(range(1000000))
        self.feature_engineering.process_large_dataset(large_data)
        
        # 检查内存使用是否在可接受范围内
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # 确保内存增加不超过预期值(例如100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
    
    def test_feature_engineering_boundaries(self):
        """特征工程边界测试"""
        # 测试空数据集
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError):
            self.feature_engineering._generate_combination_features(empty_df)
        
        # 测试单行数据
        single_row = pd.DataFrame({
            'red_1': [1], 'red_2': [2], 'red_3': [3],
            'red_4': [4], 'red_5': [5], 'red_6': [6],
            'blue': [1]
        })
        result = self.feature_engineering._generate_combination_features(single_row)
        self.assertIsNotNone(result)
        
        # 测试重复号码
        duplicate_numbers = pd.DataFrame({
            'red_1': [1], 'red_2': [1], 'red_3': [1],
            'red_4': [1], 'red_5': [1], 'red_6': [1],
            'blue': [1]
        })
        with self.assertRaises(ValueError):
            self.feature_engineering.validate_and_process(duplicate_numbers)
        
        # 测试超出范围的号码
        invalid_numbers = pd.DataFrame({
            'red_1': [0], 'red_2': [34], 'red_3': [3],
            'red_4': [4], 'red_5': [5], 'red_6': [6],
            'blue': [17]
        })
        with self.assertRaises(ValueError):
            self.feature_engineering.validate_and_process(invalid_numbers)
