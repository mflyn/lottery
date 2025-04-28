from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
import joblib
import numpy as np
from typing import Any, Optional

class ModelTrainer:
    """模型训练器"""
    def __init__(self):
        self.model = None

    def train_random_forest(self, X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
        """训练随机森林模型"""
        model = RandomForestClassifier()
        model.fit(X, y)
        self.model = model
        return model

    def train_xgboost(self, X: np.ndarray, y: np.ndarray) -> XGBClassifier:
        """训练XGBoost模型"""
        model = XGBClassifier()
        model.fit(X, y)
        self.model = model
        return model

    def predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        """模型预测"""
        return model.predict(X)

    def evaluate_model(self, model: Any, X: np.ndarray, y: np.ndarray) -> float:
        """评估模型"""
        scores = cross_val_score(model, X, y, cv=5)
        return scores.mean()

    def save_model(self, model: Any, filepath: str) -> bool:
        """保存模型"""
        try:
            joblib.dump(model, filepath)
            return True
        except Exception as e:
            print(f"保存模型失败: {str(e)}")
            return False

    def load_model(self, filepath: str) -> Optional[Any]:
        """加载模型"""
        try:
            return joblib.load(filepath)
        except Exception as e:
            print(f"加载模型失败: {str(e)}")
            return None
