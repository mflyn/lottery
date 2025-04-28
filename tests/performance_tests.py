import unittest
import time
import psutil
import pandas as pd
import numpy as np
from src.core.features.feature_engineering import FeatureEngineering

class PerformanceTests(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        self.fe = FeatureEngineering()
        self.process = psutil.Process()
    
    def test_feature_generation_performance(self):
        """测试特征生成性能"""
        # 准备大量测试数据
        n_samples = 10000
        data = pd.DataFrame({
            'red_1': np.random.randint(1, 34, n_samples),
            'red_2': np.random.randint(1, 34, n_samples),
            'red_3': np.random.randint(1, 34, n_samples),
            'red_4': np.random.randint(1, 34, n_samples),
            'red_5': np.random.randint(1, 34, n_samples),
            'red_6': np.random.randint(1, 34, n_samples),
            'blue': np.random.randint(1, 17, n_samples)
        })
        
        # 记录初始内存
        initial_memory = self.process.memory_info().rss
        
        # 测试执行时间
        start_time = time.time()
        features = self.fe.generate_features(data)
        end_time = time.time()
        
        # 记录最终内存
        final_memory = self.process.memory_info().rss
        
        # 验证性能指标
        execution_time = end_time - start_time
        memory_increase = final_memory - initial_memory
        
        # 断言性能要求
        self.assertLess(execution_time, 10.0)  # 执行时间应小于10秒
        self.assertLess(memory_increase, 500 * 1024 * 1024)  # 内存增加应小于500MB
    
    def test_cache_performance(self):
        """测试缓存性能"""
        data = pd.DataFrame({
            'red_1': np.random.randint(1, 34, 1000),
            'red_2': np.random.randint(1, 34, 1000),
            'red_3': np.random.randint(1, 34, 1000),
            'red_4': np.random.randint(1, 34, 1000),
            'red_5': np.random.randint(1, 34, 1000),
            'red_6': np.random.randint(1, 34, 1000),
            'blue': np.random.randint(1, 17, 1000)
        })
        
        # 首次执行（无缓存）
        start_time = time.time()
        self.fe.generate_features(data)
        first_execution = time.time() - start_time
        
        # 第二次执行（有缓存）
        start_time = time.time()
        self.fe.generate_features(data)
        cached_execution = time.time() - start_time
        
        # 验证缓存加速效果
        self.assertLess(cached_execution, first_execution * 0.1)  # 缓存应该至少快10倍