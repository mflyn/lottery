import unittest
import pandas as pd
from matplotlib.figure import Figure
from src.core.number_generator import LotteryNumberGenerator
from src.core.features.feature_engineering import FeatureEngineering
from src.data.data_manager import DataManager
from src.core.model.model_trainer import ModelTrainer
from src.core.features.feature_validator import FeatureValidator

class IntegrationTests(unittest.TestCase):
    """集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.data_manager = DataManager()
        cls.feature_validator = FeatureValidator()
    
    def test_end_to_end_workflow(self):
        """测试完整工作流程"""
        try:
            # 1. 加载数据
            data = self.data_manager.load_lottery_data('dlt')
            self.assertIsNotNone(data)
            
            # 2. 特征工程
            feature_engineering = FeatureEngineering(lottery_type='dlt')
            features = feature_engineering.generate_features(data)
            features.fillna(0, inplace=True)
            self.assertIsNotNone(features)
            
            # 3. 模型训练和预测
            target_series = data['back_numbers'].apply(lambda nums: nums[0] if isinstance(nums, list) and nums else None)
            model_trainer = ModelTrainer()
            train_results = model_trainer.train(features, target_series)
            self.assertIn('train_mse', train_results)
            
            # 4. 模型解释
            self.assertIsNotNone(model_trainer.feature_importance)
            
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
        feature_engineering = FeatureEngineering(lottery_type='dlt')
        features = feature_engineering.generate_features(data)
        features.fillna(0, inplace=True)

        target_series = data['back_numbers'].apply(lambda nums: nums[0] if isinstance(nums, list) and nums else None)

        # 2. 模型训练
        model_trainer = ModelTrainer()
        model_trainer.train(features, target_series)
        self.assertIsNotNone(model_trainer.model)
        
        # 3. 模型评估
        evaluation = model_trainer.cross_validate(features, target_series)
        self.assertIsNotNone(evaluation['mean_cv_score'])
        
        # 4. 模型保存和加载
        model_trainer.save_model('test_model.pkl')
        loaded_model_trainer = ModelTrainer()
        loaded_model_trainer.load_model('test_model.pkl')
        self.assertIsNotNone(loaded_model_trainer.model)

    def test_feature_engineering_pipeline(self):
        """测试特征工程完整流程"""
        # 1. 数据准备
        data = pd.DataFrame(self.data_manager.get_history_data('ssq', limit=1000))
        
        # 2. 特征生成
        feature_engineering = FeatureEngineering(lottery_type='ssq')
        features = feature_engineering.generate_features(data)
        features.fillna(0, inplace=True)
        self.assertIsNotNone(features)
        
        # 3. 特征选择
        selected_features = feature_engineering.select_features(
            features,
            data['blue_1'],
            method='mutual_info',
            n_features=5
        )
        self.assertEqual(len(selected_features.columns), 5)
        
        # 4. 特征验证
        validation_result = self.feature_validator.validate_features(selected_features, lottery_type='ssq', feature_type='basic')
        self.assertTrue(validation_result['is_valid'])
        
        # 5. 特征存储和加载
        feature_engineering.save_features(selected_features, 'test_features.pkl')
        loaded_features = feature_engineering.load_features('test_features.pkl')
        self.assertTrue(loaded_features.equals(selected_features))

    def test_feature_visualization(self):
        """测试特征可视化功能"""
        # 生成测试数据和特征
        data = pd.DataFrame(self.data_manager.get_history_data('ssq', limit=100))
        feature_engineering = FeatureEngineering(lottery_type='ssq')
        features = feature_engineering.generate_features(data)
        features.fillna(0, inplace=True)
        
        # 测试相关性热力图
        correlation_fig = feature_engineering.visualize_feature_correlation(
            features,
            method='pearson',
            threshold=0.8,
            show_plot=False
        )
        self.assertIsInstance(correlation_fig, Figure)
        
        # 测试特征重要性图
        feature_engineering.analyze_feature_importance(features, data['blue_1'])
        importance_fig = feature_engineering.visualize_feature_importance(
            top_n=5,
            show_plot=False
        )
        self.assertIsInstance(importance_fig, Figure)
        
        # 测试特征分布图
        distribution_fig = feature_engineering.visualize_feature_distribution(
            features,
            n_cols=3,
            show_plot=False
        )
        self.assertIsInstance(distribution_fig, Figure)
