from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler

class BaseFeatureProcessor(ABC):
    """特征工程基类"""
    
    def __init__(self):
        self.feature_importance: Dict[str, float] = {}
        self.selected_features: List[str] = []
        self.scaler = StandardScaler()
        
    @abstractmethod
    def extract_basic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """提取基础特征"""
        pass
        
    @abstractmethod
    def extract_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """提取高级特征"""
        pass
    
    def normalize_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """特征标准化"""
        normalized = pd.DataFrame(
            self.scaler.fit_transform(features),
            columns=features.columns,
            index=features.index
        )
        return normalized
    
    def calculate_feature_importance(self, features: pd.DataFrame, 
                                   target: pd.Series) -> Dict[str, float]:
        """计算特征重要性"""
        importance_dict = {}
        
        # 使用互信息法计算特征重要性
        for column in features.columns:
            mi_score = mutual_info_regression(
                features[[column]], 
                target, 
                random_state=42
            )[0]
            importance_dict[column] = mi_score
            
        self.feature_importance = dict(
            sorted(importance_dict.items(), 
                  key=lambda x: x[1], 
                  reverse=True)
        )
        return self.feature_importance