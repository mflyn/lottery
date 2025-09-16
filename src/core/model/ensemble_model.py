from typing import List
from sklearn.ensemble import VotingRegressor, StackingRegressor
from sklearn.model_selection import cross_val_score

class EnsembleModel:
    """模型集成类"""
    
    def __init__(self, base_models: List, method: str = 'voting'):
        """
        Args:
            base_models: 基础模型列表
            method: 集成方法 ('voting' 或 'stacking')
        """
        self.base_models = base_models
        self.method = method
        self.ensemble = None
        
    def build_ensemble(self, meta_model=None):
        """构建集成模型"""
        if self.method == 'voting':
            self.ensemble = VotingRegressor(
                estimators=[(f'model_{i}', model) 
                          for i, model in enumerate(self.base_models)],
                n_jobs=-1
            )
        elif self.method == 'stacking':
            if meta_model is None:
                raise ValueError("Meta model required for stacking")
            self.ensemble = StackingRegressor(
                estimators=[(f'model_{i}', model) 
                          for i, model in enumerate(self.base_models)],
                final_estimator=meta_model,
                n_jobs=-1
            )
            
    def evaluate_ensemble(self, X, y, cv=5):
        """评估集成模型性能"""
        scores = cross_val_score(
            self.ensemble, X, y, 
            cv=cv, scoring='neg_mean_squared_error'
        )
        return {
            'mse_scores': -scores,
            'mean_mse': -scores.mean(),
            'std_mse': scores.std()
        }