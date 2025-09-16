from typing import Dict, Any
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import make_scorer, mean_squared_error

class HyperparameterOptimizer:
    """模型参数优化器"""
    
    def __init__(self, model, param_grid: Dict[str, Any], 
                 method: str = 'grid', cv: int = 5):
        self.model = model
        self.param_grid = param_grid
        self.method = method
        self.cv = cv
        self.best_params = None
        self.best_score = None
        
    def optimize(self, X, y):
        """执行参数优化"""
        # 定义评分器
        scorer = make_scorer(mean_squared_error, greater_is_better=False)
        
        if self.method == 'grid':
            search = GridSearchCV(
                self.model,
                self.param_grid,
                scoring=scorer,
                cv=self.cv,
                n_jobs=-1,
                verbose=1
            )
        elif self.method == 'random':
            search = RandomizedSearchCV(
                self.model,
                self.param_grid,
                scoring=scorer,
                cv=self.cv,
                n_jobs=-1,
                verbose=1
            )
            
        # 执行搜索
        search.fit(X, y)
        
        self.best_params = search.best_params_
        self.best_score = search.best_score_
        
        return search.best_estimator_
        
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        return {
            'best_parameters': self.best_params,
            'best_score': self.best_score,
            'optimization_method': self.method
        }