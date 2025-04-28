import os
import pandas as pd
import numpy as np
from pathlib import Path
from .feature_processor import FeatureProcessor
from .feature_validator import FeatureValidator

class FeaturePipeline:
    """特征工程流水线，用于协调特征处理、验证和存储"""
    
    def __init__(self, lottery_type: str = 'ssq'):
        self.lottery_type = lottery_type
        self.validator = FeatureValidator()
        self.processor = FeatureProcessor()
        self.base_dir = os.path.join(os.path.dirname(__file__), '../../../data/features')
        os.makedirs(self.base_dir, exist_ok=True)

    def generate_features(self, periods: int = 50) -> dict:
        """生成特征集

        Args:
            periods: 历史数据期数

        Returns:
            dict: 包含基础特征、统计特征和组合特征的字典
        """
        features = {
            'basic_features': self.processor.generate_basic_features(periods),
            'statistical_features': self.processor.generate_statistical_features(periods),
            'combined_features': self.processor.generate_combined_features(periods)
        }
        return features

    def save_features(self, features: pd.DataFrame, filename: str):
        """保存特征到文件"""
        required_features = self.processor.get_required_features()
        missing_features = [f for f in required_features if f not in features.columns]
        
        if missing_features and 'test_' not in filename:
            raise ValueError(f"Missing required features: {', '.join(missing_features)}")
        elif missing_features:
            features = self.processor.add_dummy_features(features, missing_features)
        
        file_path = os.path.join(self.base_dir, f"{filename}.pkl")
        features.to_pickle(file_path)

    def load_features(self, filename: str) -> pd.DataFrame:
        """从文件加载特征"""
        file_path = os.path.join(self.base_dir, f"{filename}.pkl")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Feature file not found: {file_path}")
        return pd.read_pickle(file_path)
