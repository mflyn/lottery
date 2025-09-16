import pytest
import numpy as np
import pandas as pd
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering
from src.data.data_manager import DataManager

class BenchmarkTests:
    """性能基准测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.data_manager = DataManager()
        self.number_generator = LotteryNumberGenerator()
        self.feature_engineering = FeatureEngineering()
        
        # 生成测试数据
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self, size=1000):
        """生成测试数据"""
        return {
            'numbers': np.random.randint(1, 36, (size, 5)),
            'dates': pd.date_range(start='2020-01-01', periods=size),
            'results': np.random.randint(0, 2, size)
        }
    
    def test_number_generation_performance(self, benchmark):
        """测试号码生成性能"""
        def generate_numbers():
            for _ in range(100):
                self.number_generator.generate_random()
        
        # 运行基准测试
        result = benchmark(generate_numbers)
        
        # 验证性能指标
        assert result.stats.mean < 0.1  # 平均执行时间应小于0.1秒
    
    def test_feature_engineering_performance(self, benchmark):
        """测试特征工程性能"""
        def process_features():
            self.feature_engineering.generate_basic_features(self.test_data)
        
        result = benchmark(process_features)
        assert result.stats.mean < 1.0  # 平均执行时间应小于1秒
    
    def test_data_loading_performance(self, benchmark):
        """测试数据加载性能"""
        def load_data():
            self.data_manager.load_lottery_data('dlt')
        
        result = benchmark(load_data)
        assert result.stats.mean < 2.0  # 平均执行时间应小于2秒
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 执行密集操作
        large_data = self._generate_test_data(size=10000)
        self.feature_engineering.generate_advanced_features(large_data)
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        assert memory_increase < 100  # 内存增长应小于100MB