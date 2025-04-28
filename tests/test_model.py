import unittest
import numpy as np
import pandas as pd
from src.core.model.ensemble_model import EnsembleModel
from src.core.preprocessing.data_preprocessor import DataPreprocessor
from src.core.model.model_interpreter import ModelInterpreter
from sklearn.ensemble import RandomForestRegressor

class TestModelPipeline(unittest.TestCase):
    """模型流水线测试"""
    
    def setUp(self):
        """测试初始化"""
        # 准备测试数据
        np.random.seed(42)
        self.X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.choice(['A', 'B', 'C'], 100)
        })
        self.y = np.random.randn(100)
        
        # 初始化组件
        self.preprocessor = DataPreprocessor()
        self.base_models = [
            RandomForestRegressor(n_estimators=10),
            RandomForestRegressor(n_estimators=20)
        ]
        self.ensemble = EnsembleModel(self.base_models)
        
    def test_preprocessing(self):
        """测试数据预处理"""
        # 添加缺失值
        X_missing = self.X.copy()
        X_missing.iloc[0, 0] = np.nan
        
        # 测试预处理
        processed_data = self.preprocessor.preprocess_data(
            X_missing,
            categorical_columns=['feature3'],
            numerical_columns=['feature1', 'feature2']
        )
        
        self.assertFalse(processed_data.isnull().any().any())
        self.assertTrue(isinstance(processed_data['feature3'].iloc[0], (int, np.integer)))
        
    def test_ensemble_model(self):
        """测试模型集成"""
        # 构建集成模型
        self.ensemble.build_ensemble()
        
        # 评估模型
        scores = self.ensemble.evaluate_ensemble(self.X, self.y)
        
        self.assertIn('mean_mse', scores)
        self.assertIn('std_mse', scores)
        
    def test_model_interpretation(self):
        """测试模型解释"""
        # 训练单个模型用于测试
        model = RandomForestRegressor(n_estimators=10)
        model.fit(self.X.drop('feature3', axis=1), self.y)
        
        interpreter = ModelInterpreter(
            model, 
            feature_names=['feature1', 'feature2']
        )
        
        # 测试全局解释
        global_explanation = interpreter.explain_global(
            self.X.drop('feature3', axis=1)
        )
        
        self.assertIn('feature_importance', global_explanation)
        self.assertEqual(
            len(global_explanation['feature_importance']), 
            2  # 特征数量
        )

if __name__ == '__main__':
    unittest.main()