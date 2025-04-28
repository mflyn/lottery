import os
import sys
import time
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.core.features.feature_pipeline import FeaturePipeline
from src.core.features.feature_validator import FeatureValidator
from src.core.utils.progress_tracker import ProgressTracker

class TestFeaturePipeline:
    def setUp(self):
        """测试前的设置"""
        self.feature_pipeline = FeaturePipeline(lottery_type='ssq')
        
    def tearDown(self):
        """测试后的清理"""
        pass

    # 由于使用pytest，我们也可以使用fixture
    @pytest.fixture(autouse=True)
    def setup_pipeline(self):
        """自动执行的测试设置"""
        self.feature_pipeline = FeaturePipeline(lottery_type='ssq')
        yield
        # 测试后清理工作可以放在这里

    def test_feature_engineering_pipeline(self):
        """测试特征工程完整流程"""
        # 准备测试数据
        test_data = pd.DataFrame({
            'number': np.random.randint(1, 100, 100),
            'value': np.random.normal(100, 10, 100)
        })
        
        # 初始化特征流水线
        pipeline = FeaturePipeline()
        
        # 生成特征
        features = pipeline.generate_features(periods=50)
        
        # 验证基本特征
        assert 'basic_features' in features
        assert isinstance(features['basic_features'], pd.DataFrame)
        assert not features['basic_features'].empty
        
        # 验证统计特征
        assert 'statistical_features' in features
        assert isinstance(features['statistical_features'], pd.DataFrame)
        assert not features['statistical_features'].empty
        
        # 验证组合特征
        assert 'combined_features' in features
        assert isinstance(features['combined_features'], pd.DataFrame)
        assert not features['combined_features'].empty
        
        # 验证特征值的有效性
        for feature_set in features.values():
            assert not feature_set.isnull().any().any(), "特征中不应该包含空值"

    def test_feature_validation(self):
        """测试特征验证功能"""
        # 准备测试数据 - 有效数据
        valid_features = pd.DataFrame({
            'number_frequency': [1, 2, 3],
            'sum_stats': [10, 20, 30],
            'mean_stats': [5, 10, 15],
            'trend_features': [-1, 0, 1],
            'pattern_features': [0.1, 0.5, 0.9],
            'statistical_features': [-0.5, 0, 0.5]
        })
        
        # 验证基础特征
        basic_results = self.feature_pipeline.validator.validate_features(
            valid_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        assert basic_results['is_valid'], f"基础特征验证失败: {basic_results}"

    def test_feature_storage(self):
        """测试特征存储和加载功能"""
        # 准备测试数据
        test_data = pd.DataFrame({
            'number_frequency': [1, 2, 3],
            'sum_stats': [4, 5, 6],
            'mean_stats': [7, 8, 9],
            'trend_features': [10, 11, 12],
            'pattern_features': [13, 14, 15],
            'statistical_features': [16, 17, 18]
        })
        
        filename = 'test_features'  # 添加test_前缀以启用测试模式
        
        try:
            self.feature_pipeline.save_features(test_data, filename)
            loaded_features = self.feature_pipeline.load_features(filename)
            pd.testing.assert_frame_equal(test_data, loaded_features)
        finally:
            # 清理测试文件
            test_file = Path(self.feature_pipeline.base_dir) / f"{filename}.pkl"
            if test_file.exists():
                test_file.unlink()

    def test_feature_validation_edge_cases(self):
        """测试特征验证的边界情况"""
        # 1. 测试空数据集
        empty_features = pd.DataFrame()
        validation_result = self.feature_pipeline.validator.validate_features(
            empty_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        assert not validation_result['is_valid']
        assert "特征数据不能为空" in validation_result['issues']
        
        # 2. 测试含有缺失值的数据集
        features_with_nan = pd.DataFrame({
            'feature1': [1.0, np.nan, 3.0],
            'feature2': [4.0, 5.0, np.nan]
        })
        validation_result = self.feature_pipeline.validator.validate_features(
            features_with_nan,
            lottery_type='ssq',
            feature_type='basic'
        )
        assert not validation_result['is_valid']
        assert "特征数据包含缺失值" in validation_result['issues']
        
        # 3. 测试极端值
        features_with_extremes = pd.DataFrame({
            'feature1': [1e9, -1e9, 1000],  # 设置为10亿，远超过1e6阈值
            'feature2': [-1000, 2000, 3000]
        })
        validation_result = self.feature_pipeline.validator.validate_features(
            features_with_extremes,
            lottery_type='ssq',
            feature_type='basic'
        )

        # 添加调试打印语句
        print("\n=== Debug Information ===")
        print("Validation result:", validation_result)
        warnings_list = validation_result.get('warnings', [])
        issues_list = validation_result.get('issues', [])
        print("Warnings:", warnings_list)
        print("Issues:", issues_list)
        print("========================\n")

        # 检查是否有包含'极端值'或'extreme'的警告
        has_extreme_value_warning = False
        for warning in warnings_list:
            if '极端值' in warning or 'extreme' in warning.lower():
                has_extreme_value_warning = True
                break
        
        # 确保验证结果标记为无效
        assert not validation_result['is_valid'], "当有极端值时，is_valid应为False"
        assert has_extreme_value_warning, "未检测到极端值警告"
        
        # 4. 测试完全相关的特征
        perfect_correlation = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 4, 6, 8, 10]  # feature1 的两倍
        })
        correlations = self.feature_pipeline.validator.validate_feature_correlations(
            perfect_correlation,
            threshold=0.8
        )
        assert len(correlations) > 0, "未检测到特征相关性"
        
        # 5. 测试常量特征
        constant_features = pd.DataFrame({
            'feature1': [1, 2, 3],
            'constant': [5, 5, 5]
        })
        validation_result = self.feature_pipeline.validator.validate_features(
            constant_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        has_constant_warning = any(
            'constant' in str(issue).lower() 
            for issue in validation_result.get('issues', [])
        )
        assert has_constant_warning, "未检测到常量特征警告"

    def test_feature_validation_performance(self):
        """测试特征验证的性能"""
        # 生成大规模测试数据
        n_samples = 10000
        n_features = 100
        large_features = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        
        # 测试验证性能
        start_time = time.time()
        validation_result = self.feature_pipeline.validator.validate_features(
            large_features,
            lottery_type='ssq',
            feature_type='basic'
        )
        end_time = time.time()
        
        # 验证执行时间
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"特征验证耗时过长: {execution_time:.2f}秒"
        
        # 验证内存使用
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            assert memory_usage < 1000, f"内存使用过高: {memory_usage:.2f}MB"
        except ImportError:
            print("警告: psutil模块未安装，跳过内存使用检查")
            # 如果psutil不可用，我们仍然可以检查验证结果
            assert validation_result is not None, "验证结果不应为None"
            print(f"验证执行时间: {execution_time:.2f}秒")

    def test_feature_stability(self):
        """测试特征稳定性检查"""
        # 准备测试数据
        test_data = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 4, 6, 8, 10]
        })
        
        # 检查特征稳定性
        stability_scores = self.feature_pipeline.validator.check_feature_stability(
            test_data,
            window_size=2
        )
        
        # 验证结果
        assert isinstance(stability_scores, dict)
        assert all(0 <= score <= 1 for score in stability_scores.values())
        assert all(feature in stability_scores for feature in test_data.columns)

if __name__ == '__main__':
    pytest.main([__file__])
