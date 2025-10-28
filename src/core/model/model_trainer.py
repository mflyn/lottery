from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import joblib

class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, model_type: str = 'random_forest'):
        self.model_type = model_type
        self.model = self._create_model()
        self.feature_importance = None
        
    def train(self, X: pd.DataFrame, y: pd.Series,
              test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """训练模型"""
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # 训练模型
        self.model.fit(X_train, y_train)
        
        # 预测和评估
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        # 计算特征重要性
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                X.columns, self.model.feature_importances_
            ))
        
        # 返回评估结果
        return {
            'train_mse': mean_squared_error(y_train, train_pred),
            'test_mse': mean_squared_error(y_test, test_pred),
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_test, test_pred),
            'feature_importance': self.feature_importance
        }
        
    def cross_validate(self, X: pd.DataFrame, y: pd.Series,
                      cv: int = 5) -> Dict[str, float]:
        """交叉验证"""
        if cv > len(X):
            cv = len(X)
        if cv > len(X):
            cv = len(X)
        cv_scores = cross_val_score(self.model, X, y, cv=cv)
        
        return {
            'mean_cv_score': cv_scores.mean(),
            'std_cv_score': cv_scores.std()
        }
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        return self.model.predict(X)
        
    def save_model(self, filepath: str):
        """保存模型"""
        joblib.dump(self.model, filepath)
        
    def load_model(self, filepath: str):
        """加载模型"""
        self.model = joblib.load(filepath)
        
    def _create_model(self) -> Any:
        """创建模型实例"""
        if self.model_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")