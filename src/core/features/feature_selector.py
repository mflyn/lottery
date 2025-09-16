from typing import Dict
import pandas as pd
from sklearn.feature_selection import mutual_info_regression, SelectKBest
from sklearn.preprocessing import StandardScaler

class FeatureSelector:
    """特征选择器"""
    
    def __init__(self, method: str = 'combined'):
        """初始化特征选择器
        
        Args:
            method: 特征选择方法 ('mutual_info', 'correlation', 'combined')
        """
        self.method = method
        self.selected_features = []
        
    def select_features(self, X: pd.DataFrame, y: pd.Series, n_features: int = 10) -> pd.DataFrame:
        """选择最重要的特征
        
        Args:
            X: 特征矩阵
            y: 目标变量
            n_features: 要选择的特征数量
            
        Returns:
            选择后的特征矩阵
        """
        if self.method == 'mutual_info':
            return self._mutual_info_selection(X, y, n_features)
        elif self.method == 'correlation':
            return self._correlation_selection(X, y, n_features)
        else:  # combined
            return self._combined_selection(X, y, n_features)
            
    def _mutual_info_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> pd.DataFrame:
        """基于互信息的特征选择"""
        # 标准化特征
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 计算互信息得分
        selector = SelectKBest(score_func=mutual_info_regression, k=n_features)
        selector.fit(X_scaled, y)
        
        # 获取选中的特征
        selected_mask = selector.get_support()
        selected_features = X.columns[selected_mask].tolist()
        self.selected_features = selected_features
        
        return X[selected_features]
        
    def _correlation_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> pd.DataFrame:
        """基于相关性的特征选择"""
        # 计算与目标变量的相关性
        correlations = X.apply(lambda x: x.corr(y))
        
        # 选择相关性最高的特征
        selected_features = correlations.abs().nlargest(n_features).index.tolist()
        self.selected_features = selected_features
        
        return X[selected_features]
        
    def _combined_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> pd.DataFrame:
        """组合特征选择方法"""
        # 获取互信息选择的特征
        mi_features = self._mutual_info_selection(X, y, n_features)
        
        # 获取相关性选择的特征
        corr_features = self._correlation_selection(X, y, n_features)
        
        # 合并两种方法选择的特征
        combined_features = list(set(mi_features.columns) | set(corr_features.columns))
        self.selected_features = combined_features[:n_features]
        
        return X[self.selected_features]
        
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性得分"""
        if not self.selected_features:
            return {}
            
        importance = {feature: 1.0 - i/len(self.selected_features) 
                     for i, feature in enumerate(self.selected_features)}
        return importance
