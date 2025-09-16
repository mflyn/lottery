from typing import Dict, List, Optional
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import optuna
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib

class ModelOptimizer:
    """模型优化器"""
    
    def __init__(self, model, param_grid: Optional[Dict] = None):
        self.model = model
        self.param_grid = param_grid
        self.best_params = None
        self.best_score = None
        self.best_model = None
        self.search_results = None
        
    def grid_search(self, X, y, cv=5, scoring='neg_mean_squared_error'):
        """网格搜索优化
        
        Args:
            X: 特征数据
            y: 目标数据
            cv: 交叉验证折数
            scoring: 评分标准
        """
        grid_search = GridSearchCV(
            self.model,
            self.param_grid,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X, y)
        
        self.best_params = grid_search.best_params_
        self.best_score = grid_search.best_score_
        self.best_model = grid_search.best_estimator_
        self.search_results = grid_search.cv_results_
        
        return self.best_model
        
    def random_search(self, X, y, n_iter=100, cv=5, scoring='neg_mean_squared_error'):
        """随机搜索优化"""
        random_search = RandomizedSearchCV(
            self.model,
            self.param_grid,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        random_search.fit(X, y)
        
        self.best_params = random_search.best_params_
        self.best_score = random_search.best_score_
        self.best_model = random_search.best_estimator_
        self.search_results = random_search.cv_results_
        
        return self.best_model

    def optuna_optimize(self, X, y, n_trials=100):
        """使用Optuna进行超参数优化"""
        def objective(trial):
            # 根据模型类型动态生成参数搜索空间
            params = self._create_optuna_params(trial)
            
            # 设置模型参数
            self.model.set_params(**params)
            
            # 交叉验证评估
            score = self._cross_validate(X, y)
            return score

        # 创建和运行优化研究
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        
        # 保存最佳结果
        self.best_params = study.best_params
        self.best_score = study.best_value
        self.best_model = self.model.set_params(**study.best_params)
        
        return self.best_model

    def _create_optuna_params(self, trial) -> Dict:
        """根据模型类型创建Optuna参数搜索空间"""
        params = {}
        
        # 根据模型类型添加相应的参数
        if hasattr(self.model, 'n_estimators'):
            params['n_estimators'] = trial.suggest_int('n_estimators', 50, 300)
        if hasattr(self.model, 'max_depth'):
            params['max_depth'] = trial.suggest_int('max_depth', 3, 10)
        if hasattr(self.model, 'learning_rate'):
            params['learning_rate'] = trial.suggest_loguniform('learning_rate', 1e-4, 1e-1)
        
        return params

    def feature_selection(self, X, y, method='importance', threshold=0.01):
        """特征选择"""
        if method == 'importance':
            # 基于特征重要性的选择
            importances = self._get_feature_importance(X, y)
            selected_features = [i for i, imp in enumerate(importances) 
                               if imp > threshold]
            return selected_features
        
        elif method == 'correlation':
            # 基于相关性的选择
            corr_matrix = np.corrcoef(X.T)
            selected_features = self._select_uncorrelated_features(corr_matrix)
            return selected_features

    def dimensionality_reduction(self, X, n_components=None, variance_ratio=0.95):
        """降维处理"""
        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PCA降维
        if n_components is None:
            pca = PCA(n_components=variance_ratio, svd_solver='full')
        else:
            pca = PCA(n_components=n_components)
            
        X_reduced = pca.fit_transform(X_scaled)
        
        return X_reduced, pca

    def save_model(self, filepath: str):
        """保存优化后的模型"""
        if self.best_model is None:
            raise ValueError("No optimized model available to save")
        
        model_info = {
            'model': self.best_model,
            'params': self.best_params,
            'score': self.best_score
        }
        joblib.dump(model_info, filepath)

    def load_model(self, filepath: str):
        """加载已优化的模型"""
        model_info = joblib.load(filepath)
        self.best_model = model_info['model']
        self.best_params = model_info['params']
        self.best_score = model_info['score']
        return self.best_model

    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        return {
            'best_parameters': self.best_params,
            'best_score': self.best_score,
            'model_type': str(type(self.best_model).__name__),
            'feature_importance': self._get_feature_importance() if self.best_model is not None else None,
            'cross_validation_results': self.search_results
        }

    def _get_feature_importance(self, X=None, y=None) -> np.ndarray:
        """获取特征重要性"""
        if hasattr(self.best_model, 'feature_importances_'):
            return self.best_model.feature_importances_
        elif hasattr(self.best_model, 'coef_'):
            return np.abs(self.best_model.coef_)
        else:
            return None

    def _cross_validate(self, X, y, cv=5) -> float:
        """交叉验证评估"""
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(
            self.model, X, y, 
            cv=cv, 
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        return np.mean(scores)

    def _select_uncorrelated_features(self, corr_matrix: np.ndarray, threshold=0.8) -> List[int]:
        """选择非相关特征"""
        selected = []
        n = corr_matrix.shape[0]
        
        for i in range(n):
            keep = True
            for j in selected:
                if abs(corr_matrix[i, j]) > threshold:
                    keep = False
                    break
            if keep:
                selected.append(i)
                
        return selected
