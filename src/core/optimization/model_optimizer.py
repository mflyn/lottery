from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.feature_selection import SelectKBest, mutual_info_classif, RFE
from sklearn.metrics import make_scorer, accuracy_score, precision_score, recall_score
import numpy as np
from typing import Dict, Any, Tuple, List
import matplotlib.pyplot as plt

class ModelOptimizer:
    def __init__(self, base_model, feature_selector='auto'):
        self.base_model = base_model
        self.feature_selector = feature_selector
        self.best_model = None
        self.selected_features = None
        self.optimization_history = []
        
    def optimize(self, X: pd.DataFrame, y: pd.Series,
                param_grid: Dict[str, Any],
                cv_folds: int = 5,
                scoring: str = 'accuracy') -> Tuple[Any, Dict[str, Any]]:
        """优化模型
        
        Args:
            X: 特征数据
            y: 目标变量
            param_grid: 参数网格
            cv_folds: 交叉验证折数
            scoring: 评分方式
            
        Returns:
            优化后的模型和最佳参数
        """
        # 特征选择
        X_selected = self._select_features(X, y)
        
        # 定义评分指标
        scoring_metrics = {
            'accuracy': make_scorer(accuracy_score),
            'precision': make_scorer(precision_score, average='weighted'),
            'recall': make_scorer(recall_score, average='weighted')
        }
        
        # 网格搜索
        grid_search = GridSearchCV(
            estimator=self.base_model,
            param_grid=param_grid,
            cv=cv_folds,
            scoring=scoring_metrics,
            refit=scoring,
            n_jobs=-1,
            verbose=1
        )
        
        # 执行优化
        grid_search.fit(X_selected, y)
        
        # 记录优化历史
        self.optimization_history.append({
            'params': grid_search.best_params_,
            'score': grid_search.best_score_,
            'features': self.selected_features
        })
        
        self.best_model = grid_search.best_estimator_
        
        return self.best_model, grid_search.best_params_
    
    def _select_features(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """特征选择
        
        支持多种特征选择方法:
        - 'auto': 自动选择最佳方法
        - 'mutual_info': 互信息
        - 'rfe': 递归特征消除
        """
        if self.feature_selector == 'auto':
            # 根据数据特征自动选择最佳方法
            if X.shape[1] > 100:  # 高维特征使用RFE
                selector = RFE(self.base_model, n_features_to_select=50)
            else:  # 低维特征使用互信息
                selector = SelectKBest(score_func=mutual_info_classif, k='all')
                
        elif self.feature_selector == 'mutual_info':
            selector = SelectKBest(score_func=mutual_info_classif, k='all')
            
        elif self.feature_selector == 'rfe':
            selector = RFE(self.base_model, n_features_to_select=50)
            
        # 执行特征选择
        X_selected = selector.fit_transform(X, y)
        self.selected_features = X.columns[selector.get_support()].tolist()
        
        return X_selected
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if hasattr(self.best_model, 'feature_importances_'):
            importance = self.best_model.feature_importances_
            return dict(zip(self.selected_features, importance))
        return {}
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化过程摘要"""
        return {
            'best_score': self.optimization_history[-1]['score'],
            'best_params': self.optimization_history[-1]['params'],
            'selected_features': self.selected_features,
            'optimization_history': self.optimization_history
        }
    
    def plot_optimization_history(self):
        """绘制优化过程历史"""
        scores = [h['score'] for h in self.optimization_history]
        plt.figure(figsize=(10, 6))
        plt.plot(scores, marker='o')
        plt.title('Model Optimization History')
        plt.xlabel('Optimization Step')
        plt.ylabel('Score')
        plt.grid(True)
        plt.show()
