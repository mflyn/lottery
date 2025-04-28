import unittest
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering
from src.data.data_manager import DataManager
import pandas as pd
import numpy as np

class ErrorHandlingTests(unittest.TestCase):
    """错误处理测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.data_manager = DataManager()
        self.number_generator = LotteryNumberGenerator()
        self.feature_engineering = FeatureEngineering()
    
    def test_invalid_data_input(self):
        """测试无效数据输入"""
        # 测试空数据
        with self.assertRaises(ValueError):
            self.data_manager.process_data(None)
        
        # 测试格式错误的数据
        invalid_data = pd.DataFrame({'invalid_column': ['a', 'b', 'c']})
        with self.assertRaises(ValueError):
            self.feature_engineering.generate_basic_features(invalid_data)
    
    def test_file_operations(self):
        """测试文件操作错误处理"""
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.data_manager.load_data('nonexistent.csv')
        
        # 测试无效文件格式
        with self.assertRaises(ValueError):
            self.data_manager.load_data('invalid.xyz')
    
    def test_model_errors(self):
        """测试模型相关错误处理"""
        # 测试无效模型参数
        with self.assertRaises(ValueError):
            self.number_generator.train_model(None)
        
        # 测试模型预测错误
        invalid_features = np.random.rand(10, 5)
        with self.assertRaises(ValueError):
            self.number_generator.predict(invalid_features)
    
    def test_database_errors(self):
        """测试数据库错误处理"""
        # 测试无效数据库连接
        with self.assertRaises(ConnectionError):
            self.data_manager.connect_db('invalid_host')
        
        # 测试无效查询
        with self.assertRaises(ValueError):
            self.data_manager.execute_query('invalid SQL')
    
    def test_feature_engineering_errors(self):
        """测试特征工程错误处理"""
        # 测试无效特征参数
        with self.assertRaises(ValueError):
            self.feature_engineering.generate_advanced_features(None)
        
        # 测试特征选择错误
        invalid_data = pd.DataFrame()
        with self.assertRaises(ValueError):
            self.feature_engineering.select_features(invalid_data)
    
    def test_recovery_mechanisms(self):
        """测试错误恢复机制"""
        # 测试数据备份恢复
        try:
            self.data_manager.process_data(None)
        except ValueError:
            recovery_success = self.data_manager.recover_from_backup()
            self.assertTrue(recovery_success)
        
        # 测试模型回滚
        try:
            self.number_generator.train_model(None)
        except ValueError:
            rollback_success = self.number_generator.rollback_model()
            self.assertTrue(rollback_success)