from typing import Dict, List
import numpy as np
import pandas as pd
import shap
from lime import lime_tabular
import matplotlib.pyplot as plt

class ModelInterpreter:
    """模型解释器"""
    
    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.shap_values = None
        
    def explain_global(self, X: pd.DataFrame) -> Dict:
        """全局解释"""
        # 计算SHAP值
        explainer = shap.TreeExplainer(self.model)
        self.shap_values = explainer.shap_values(X)
        
        # 特征重要性
        feature_importance = np.abs(self.shap_values).mean(0)
        importance_dict = dict(zip(self.feature_names, feature_importance))
        
        return {
            'feature_importance': importance_dict,
            'shap_values': self.shap_values
        }
        
    def explain_local(self, X: pd.DataFrame, 
                     instance_index: int) -> Dict:
        """局部解释"""
        # 使用LIME进行局部解释
        explainer = lime_tabular.LimeTabularExplainer(
            X.values,
            feature_names=self.feature_names,
            mode="regression"
        )
        
        exp = explainer.explain_instance(
            X.iloc[instance_index].values, 
            self.model.predict
        )
        
        return {
            'lime_explanation': exp,
            'local_importance': dict(exp.as_list())
        }
        
    def plot_feature_importance(self, ax: plt.Axes):
        """绘制特征重要性图"""
        if self.shap_values is None:
            raise ValueError("Run explain_global first")
            
        shap.summary_plot(self.shap_values, 
                         feature_names=self.feature_names,
                         plot_type="bar",
                         show=False)
        plt.tight_layout()