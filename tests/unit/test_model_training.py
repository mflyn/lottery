import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.core.model.model_training import ModelTrainer

class TestModelTraining(unittest.TestCase):
    def setUp(self):
        self.trainer = ModelTrainer()
        
        # 创建测试数据
        np.random.seed(42)
        n_samples = 100
        self.X = pd.DataFrame({
            'feature1': np.random.normal(0, 1, n_samples),
            'feature2': np.random.normal(0, 1, n_samples),
            'feature3': np.random.normal(0, 1, n_samples)
        })
        self.y = (0.5 * self.X['feature1'] + 0.3 * self.X['feature2'] > 0).astype(int)
    
    @patch('src.core.model.model_training.RandomForestClassifier')
    def test_train_random_forest(self, mock_rf):
        """测试随机森林模型训练"""
        # 设置模拟对象
        mock_model = MagicMock()
        mock_rf.return_value = mock_model
        
        # 调用方法
        model = self.trainer.train_random_forest(self.X, self.y)
        
        # 验证结果
        self.assertEqual(model, mock_model)
        mock_model.fit.assert_called_once()
    
    @patch('src.core.model.model_training.XGBClassifier')
    def test_train_xgboost(self, mock_xgb):
        """测试XGBoost模型训练"""
        # 设置模拟对象
        mock_model = MagicMock()
        mock_xgb.return_value = mock_model
        
        # 调用方法
        model = self.trainer.train_xgboost(self.X, self.y)
        
        # 验证结果
        self.assertEqual(model, mock_model)
        mock_model.fit.assert_called_once()
    
    def test_evaluate_model(self):
        """测试模型评估"""
        # 准备更多的测试数据以满足交叉验证的要求
        X = pd.DataFrame({
            'feature1': np.random.rand(20),
            'feature2': np.random.rand(20)
        })
        y = pd.Series(np.random.randint(0, 2, 20))
        
        # 训练模型
        self.trainer.train_random_forest(X, y)
        
        # 评估模型
        score = self.trainer.evaluate_model(self.trainer.model, X, y)
        
        # 验证评估结果
        self.assertIsInstance(score, (float, np.float64))  # 修改断言以匹配实际返回类型
        self.assertTrue(0 <= score <= 1)  # 验证分数在有效范围内
    
    @patch('src.core.model.model_training.joblib.dump')
    def test_save_model(self, mock_dump):
        """测试模型保存"""
        # 设置模拟对象
        mock_model = MagicMock()
        
        # 调用方法
        result = self.trainer.save_model(mock_model, 'test_model.pkl')
        
        # 验证结果
        self.assertTrue(result)
        mock_dump.assert_called_once()
    
    @patch('src.core.model.model_training.joblib.load')
    def test_load_model(self, mock_load):
        """测试模型加载"""
        # 设置模拟对象
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        
        # 调用方法
        loaded_model = self.trainer.load_model('test_model.pkl')
        
        # 验证结果
        self.assertEqual(loaded_model, mock_model)
        mock_load.assert_called_once_with('test_model.pkl')
    
    def test_predict(self):
        """测试模型预测"""
        # 准备测试数据
        X_test = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6]
        })
        
        # 创建模拟模型
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0, 1, 0])
        self.trainer.model = mock_model
        
        # 执行预测
        predictions = self.trainer.predict(mock_model, X_test)
        
        # 验证预测结果
        self.assertIsInstance(predictions, np.ndarray)
        self.assertEqual(len(predictions), len(X_test))
        
        # 验证模型方法调用
        mock_model.predict.assert_called_once_with(X_test)

if __name__ == '__main__':
    unittest.main()
