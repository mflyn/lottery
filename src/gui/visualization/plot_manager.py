import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
import pandas as pd
import numpy as np

class PlotManager:
    """绘图管理器"""
    
    @staticmethod
    def plot_number_frequency(ax: plt.Axes, data: pd.DataFrame, 
                            lottery_type: str):
        """绘制号码频率分布图"""
        if lottery_type == 'dlt':
            front_numbers = data['front_numbers'].explode()
            back_numbers = data['back_numbers'].explode()
            
            # 绘制前区频率
            front_freq = front_numbers.value_counts().sort_index()
            ax.bar(front_freq.index, front_freq.values, 
                  alpha=0.6, label='前区')
            
            # 绘制后区频率
            back_freq = back_numbers.value_counts().sort_index()
            ax.bar(back_freq.index, back_freq.values, 
                  alpha=0.6, label='后区')
            
        else:  # ssq
            red_numbers = data['red_numbers'].explode()
            blue_numbers = data['blue_number']
            
            # 绘制红球频率
            red_freq = red_numbers.value_counts().sort_index()
            ax.bar(red_freq.index, red_freq.values, 
                  color='red', alpha=0.6, label='红球')
            
            # 绘制蓝球频率
            blue_freq = blue_numbers.value_counts().sort_index()
            ax.bar(blue_freq.index, blue_freq.values, 
                  color='blue', alpha=0.6, label='蓝球')
            
        ax.set_title('号码出现频率分布')
        ax.set_xlabel('号码')
        ax.set_ylabel('出现次数')
        ax.legend()
        
    @staticmethod
    def plot_trend_analysis(ax: plt.Axes, data: pd.DataFrame,
                          feature: str, window: int = 10):
        """绘制走势分析图"""
        # 计算移动平均
        rolling_mean = data[feature].rolling(window=window).mean()
        
        # 绘制原始数据和趋势线
        ax.plot(data.index, data[feature], 
                alpha=0.6, label='原始数据')
        ax.plot(data.index, rolling_mean, 
                'r-', label=f'{window}期移动平均')
        
        ax.set_title(f'{feature}走势分析')
        ax.set_xlabel('期号')
        ax.set_ylabel('值')
        ax.legend()
        
    @staticmethod
    def plot_correlation_matrix(ax: plt.Axes, data: pd.DataFrame):
        """绘制相关性矩阵热图"""
        corr_matrix = data.corr()
        sns.heatmap(corr_matrix, ax=ax, cmap='coolwarm', 
                   annot=True, fmt='.2f')
        ax.set_title('特征相关性矩阵')
        
    @staticmethod
    def plot_feature_importance(ax: plt.Axes, 
                              importance_dict: Dict[str, float]):
        """绘制特征重要性图"""
        features = list(importance_dict.keys())
        importance = list(importance_dict.values())
        
        # 排序
        sorted_idx = np.argsort(importance)
        pos = np.arange(sorted_idx.shape[0]) + .5
        
        ax.barh(pos, importance[sorted_idx])
        ax.set_yticks(pos)
        ax.set_yticklabels(features[sorted_idx])
        ax.set_title('特征重要性排序')
        ax.set_xlabel('重要性得分')