import os
import pandas as pd
from datetime import datetime
from typing import Optional

class FeatureStorage:
    """特征数据存储管理"""
    
    def __init__(self, base_dir: str = "data/features"):
        self.base_dir = base_dir
        self._ensure_dir_exists()
    
    def _ensure_dir_exists(self):
        """确保存储目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def save_features(self, features_df: pd.DataFrame, name: Optional[str] = None) -> str:
        """保存特征数据
        
        Args:
            features_df: 特征数据框
            name: 可选的特征集名称
            
        Returns:
            str: 保存的文件路径
        """
        if name is None:
            name = f"features_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        file_path = os.path.join(self.base_dir, f"{name}.csv")
        features_df.to_csv(file_path, index=False)
        return file_path
    
    def load_features(self, name: str) -> pd.DataFrame:
        """加载特征数据
        
        Args:
            name: 特征集名称
            
        Returns:
            pd.DataFrame: 特征数据框
        """
        file_path = os.path.join(self.base_dir, f"{name}.csv")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"特征文件不存在: {file_path}")
        
        return pd.read_csv(file_path)
    
    def list_feature_sets(self) -> list:
        """列出所有可用的特征集
        
        Returns:
            list: 特征集名称列表
        """
        files = os.listdir(self.base_dir)
        return [f.replace('.csv', '') for f in files if f.endswith('.csv')]