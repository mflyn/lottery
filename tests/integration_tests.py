import unittest
import pandas as pd
from matplotlib.figure import Figure
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering
from src.data.data_manager import DataManager
from src.core.model.model_interpreter import ModelInterpreter
from src.core.features.feature_validator import FeatureValidator

class IntegrationTests(unittest.TestCase):
    """集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.data_manager = DataManager()
        cls.number_generator = LotteryNumberGenerator()
        cls.feature_engineering = FeatureEngineering()
        cls.feature_validator = FeatureValidator()
    
    def test_end_to_end_workflow(self):
        """测试完整工作流程"""
        try:
            # 1. 加载数据
            data = self.data_manager.load_lottery_data('dlt')
            self.assertIsNotNone(data)
            
            # 2. 特征工程
            features = self.feature_engineering.generate_basic_features(data)
            advanced_features = self.feature_engineering.generate_advanced_features(features)
            self.assertGreater(len(advanced_features.columns), len(features.columns))
            
            # 3. 模型训练和预测
            model = self.number_generator.train_model(advanced_features)
            predictions = model.predict(advanced_features)
            self.assertEqual(len(predictions), len(data))
            
            # 4. 模型解释
            interpreter = ModelInterpreter(model, advanced_features.columns)
            explanation = interpreter.explain_global(advanced_features)
            self.assertIn('feature_importance', explanation)
            
        except Exception as e:
            self.fail(f"集成测试失败: {str(e)}")
    
    def test_data_pipeline(self):
        """测试数据处理管道"""
        # 1. 数据导入
        data = self.data_manager.import_data('test_data.csv')
        self.assertIsNotNone(data)
        
        # 2. 数据预处理
        processed_data = self.data_manager.preprocess_data(data)
        self.assertIsNotNone(processed_data)
        
        # 3. 数据验证
        validation_result = self.data_manager.validate_data(processed_data)
        self.assertTrue(validation_result)
        
        # 4. 数据导出
        export_success = self.data_manager.export_data(processed_data, 'processed.csv')
        self.assertTrue(export_success)
    
    def test_model_pipeline(self):
        """测试模型处理管道"""
        # 1. 准备训练数据
        data = self.data_manager.load_lottery_data('dlt')
        features = self.feature_engineering.generate_all_features(data)
        
        # 2. 模型训练
        model = self.number_generator.train_model(features)
        self.assertIsNotNone(model)
        
        # 3. 模型评估
        evaluation = self.number_generator.evaluate_model(model, features)
        self.assertGreater(evaluation['accuracy'], 0.5)
        
        # 4. 模型保存和加载
        self.number_generator.save_model(model, 'test_model.pkl')
        loaded_model = self.number_generator.load_model('test_model.pkl')
        self.assertIsNotNone(loaded_model)

    def test_feature_engineering_pipeline(self):
        """测试特征工程完整流程"""
        # 1. 数据准备
        data = self.data_manager.get_history_data('ssq', 1000)
        
        # 2. 基础特征生成
        basic_features = self.feature_engineering.generate_basic_features(data)
        self.assertIsNotNone(basic_features)
        
        # 3. 组合特征生成
        combination_features = self.feature_engineering._generate_combination_features(data)
        self.assertIsNotNone(combination_features)
        
        # 4. 特征选择
        selected_features = self.feature_engineering.select_features(
            pd.concat([basic_features, combination_features], axis=1),
            data['blue'],
            method='mutual_info',
            n_features=20
        )
        self.assertEqual(len(selected_features.columns), 20)
        
        # 5. 特征验证
        validation_result = self.feature_validator.validate_features(selected_features)
        self.assertTrue(validation_result['is_valid'])
        
        # 6. 特征存储和加载
        self.feature_engineering.save_features(selected_features, 'test_features.pkl')
        loaded_features = self.feature_engineering.load_features('test_features.pkl')
        self.assertTrue(loaded_features.equals(selected_features))

    def test_feature_visualization(self):
        """测试特征可视化功能"""
        # 生成测试数据和特征
        data = self.data_manager.get_history_data('ssq', 100)
        features = self.feature_engineering.generate_features(data)
        
        # 测试相关性热力图
        correlation_fig = self.feature_engineering.visualize_feature_correlation(
            features,
            method='pearson',
            threshold=0.8
        )
        self.assertIsInstance(correlation_fig, Figure)
        
        # 测试特征重要性图
        importance_fig = self.feature_engineering.visualize_feature_importance(
            features,
            data['blue']
        )
        self.assertIsInstance(importance_fig, Figure)
        
        # 测试特征分布图
        distribution_fig = self.feature_engineering.visualize_feature_distribution(
            features,
            n_cols=3
        )
        self.assertIsInstance(distribution_fig, Figure)
