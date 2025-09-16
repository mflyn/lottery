from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

class PredictionValidator:
    """预测结果验证器"""
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_predictions(self, y_true: np.ndarray, 
                           y_pred: np.ndarray) -> Dict[str, float]:
        """验证预测结果"""
        results = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'r2': r2_score(y_true, y_pred),
            'mae': np.mean(np.abs(y_true - y_pred))
        }
        
        self.validation_results = results
        return results
        
    def plot_validation_results(self, y_true: np.ndarray, 
                              y_pred: np.ndarray, ax: plt.Axes):
        """绘制验证结果图表"""
        # 绘制散点图
        ax.scatter(y_true, y_pred, alpha=0.5)
        
        # 添加对角线
        ax_min = min(y_true.min(), y_pred.min())
        ax_max = max(y_true.max(), y_pred.max())
        ax.plot([ax_min, ax_max], [ax_min, ax_max], 'r--', lw=2)
        
        ax.set_xlabel('实际值')
        ax.set_ylabel('预测值')
        ax.set_title('预测值 vs 实际值')
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        if not self.validation_results:
            raise ValueError("No validation results available.")
            
        return {
            'metrics': self.validation_results,
            'summary': self._generate_summary(),
            'recommendations': self._generate_recommendations()
        }
        
    def _generate_summary(self) -> str:
        """生成结果总结"""
        mse = self.validation_results['mse']
        r2 = self.validation_results['r2']
        
        if r2 > 0.8:
            quality = "优秀"
        elif r2 > 0.6:
            quality = "良好"
        else:
            quality = "需要改进"
            
        return f"模型预测质量{quality}, R²得分为{r2:.3f}, MSE为{mse:.3f}"
        
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        r2 = self.validation_results['r2']
        
        if r2 < 0.6:
            recommendations.extend([
                "考虑添加更多相关特征",
                "尝试使用更复杂的模型架构",
                "增加训练数据量"
            ])
        elif r2 < 0.8:
            recommendations.extend([
                "尝试特征工程优化",
                "调整模型超参数"
            ])
            
        return recommendations