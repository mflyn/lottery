import unittest
from unittest.mock import Mock, patch
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering
from src.data.data_manager import DataManager

class NumberGeneratorTests(unittest.TestCase):
    """号码生成器测试"""
    
    def setUp(self):
        self.generator = LotteryNumberGenerator()
    
    def test_random_generation(self):
        """测试随机号码生成"""
        numbers = self.generator.generate_random()
        self.assertEqual(len(numbers['front']), 5)
        self.assertEqual(len(numbers['back']), 2)
        self.assertTrue(all(1 <= n <= 35 for n in numbers['front']))
        self.assertTrue(all(1 <= n <= 12 for n in numbers['back']))
    
    def test_smart_generation(self):
        """测试智能号码生成"""
        mock_history = [{'numbers': [1, 2, 3, 4, 5]}]
        numbers = self.generator.generate_smart(mock_history)
        self.assertIsNotNone(numbers)
        self.assertTrue(isinstance(numbers, dict))

class FeatureEngineeringTests(unittest.TestCase):
    """特征工程测试"""
    
    def setUp(self):
        self.fe = FeatureEngineering()
    
    def test_basic_features(self):
        """测试基本特征生成"""
        mock_data = pd.DataFrame({
            'numbers': [[1, 2, 3, 4, 5]],
            'date': ['2023-01-01']
        })
        features = self.fe.generate_basic_features(mock_data)
        self.assertGreater(len(features.columns), 1)
    
    def test_advanced_features(self):
        """测试高级特征生成"""
        mock_features = pd.DataFrame({
            'basic_feature': [1, 2, 3]
        })
        advanced = self.fe.generate_advanced_features(mock_features)
        self.assertGreater(len(advanced.columns), 1)

class FeatureEngineeringTests(unittest.TestCase):
    """特征工程测试补充"""
    
    def setUp(self):
        self.fe = FeatureEngineering()
    
    def test_interval_features(self):
        """测试区间特征计算"""
        mock_numbers = np.array([[1, 11, 21, 31, 32, 33]])
        features = self.fe._calculate_interval_features(mock_numbers)
        
        self.assertIn('interval_1_count', features)
        self.assertIn('interval_pattern', features)
        self.assertIn('interval_balance', features)
        self.assertEqual(features['interval_1_count'][0], 2)  # 第一区间应有2个号码
    
    def test_number_properties(self):
        """测试数字特性计算"""
        mock_numbers = np.array([[2, 3, 4, 5, 6, 7]])
        features = self.fe._calculate_number_properties(mock_numbers)
        
        self.assertIn('odd_even_ratio', features)
        self.assertIn('prime_count', features)
        self.assertIn('big_small_ratio', features)
        self.assertEqual(features['prime_count'][0], 4)  # 应有4个质数
    
    def test_historical_combinations(self):
        """测试历史组合特征"""
        mock_numbers = np.array([
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 7],
            [7, 8, 9, 10, 11, 12]
        ])
        features = self.fe._calculate_historical_combinations(mock_numbers)
        
        self.assertIn('combination_repeat_1', features)
        self.assertIn('combination_frequency', features)
        self.assertEqual(features['combination_repeat_1'][1], 5)  # 第二行应与第一行重复5个号码
    
    def test_cache_mechanism(self):
        """测试缓存机制"""
        # 首次计算
        result1 = self.fe.generate_features(100)
        
        # 使用缓存
        result2 = self.fe.generate_features(100)
        
        # 验证缓存命中
        self.assertTrue(np.array_equal(result1, result2))
        
        # 验证缓存过期
        import time
        time.sleep(1)  # 模拟时间流逝
        self.fe._cache_ttl = pd.Timedelta(seconds=0.5)  # 设置较短的TTL
        result3 = self.fe.generate_features(100)
        self.assertFalse(id(result1) == id(result3))  # 应该重新计算而不是使用缓存

class DataManagerTests(unittest.TestCase):
    """数据管理器测试"""
    
    @patch('src.data.data_manager.sqlite3')
    def setUp(self, mock_sqlite):
        self.data_manager = DataManager()
        self.mock_sqlite = mock_sqlite
    
    def test_load_data(self):
        """测试数据加载"""
        mock_data = pd.DataFrame({'test': [1, 2, 3]})
        self.mock_sqlite.connect().cursor().fetchall.return_value = [(1,), (2,), (3,)]
        data = self.data_manager.load_lottery_data('dlt')
        self.assertIsNotNone(data)
    
    def test_save_data(self):
        """测试数据保存"""
        mock_data = {'numbers': [1, 2, 3]}
        result = self.data_manager.save_lottery_data(mock_data, 'dlt')
        self.assertTrue(result)

class ModelInterpreterTests(unittest.TestCase):
    """模型解释器测试"""
    
    def setUp(self):
        self.mock_model = Mock()
        self.interpreter = ModelInterpreter(self.mock_model, ['feature1', 'feature2'])
    
    def test_global_explanation(self):
        """测试全局解释"""
        mock_data = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6]
        })
        explanation = self.interpreter.explain_global(mock_data)
        self.assertIn('feature_importance', explanation)
    
    def test_local_explanation(self):
        """测试局部解释"""
        mock_instance = pd.Series({'feature1': 1, 'feature2': 2})
        explanation = self.interpreter.explain_local(mock_instance)
        self.assertIsNotNone(explanation)
