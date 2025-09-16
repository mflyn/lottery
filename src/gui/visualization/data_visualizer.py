import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict
from matplotlib.figure import Figure

class LotteryDataVisualizer:
    """彩票数据可视化器"""
    
    def __init__(self):
        self.plt_style = 'seaborn'
        plt.style.use(self.plt_style)
        
    def create_dashboard(self, data: pd.DataFrame) -> Dict[str, Figure]:
        """创建可视化仪表板"""
        figures = {}
        
        # 号码分布图
        figures['distribution'] = self.plot_number_distribution(data)
        
        # 时间趋势图
        figures['trend'] = self.plot_time_trend(data)
        
        # 相关性热图
        figures['correlation'] = self.plot_correlation_heatmap(data)
        
        # 中奖规律图
        figures['pattern'] = self.plot_winning_patterns(data)
        
        return figures
        
    def plot_number_distribution(self, data: pd.DataFrame) -> Figure:
        """绘制号码分布图"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 红球分布
        red_counts = data['red_numbers'].value_counts().sort_index()
        ax1.bar(red_counts.index, red_counts.values, color='red', alpha=0.6)
        ax1.set_title('红球分布')
        
        # 蓝球分布
        blue_counts = data['blue_number'].value_counts().sort_index()
        ax2.bar(blue_counts.index, blue_counts.values, color='blue', alpha=0.6)
        ax2.set_title('蓝球分布')
        
        return fig
        
    def plot_time_trend(self, data: pd.DataFrame) -> Figure:
        """绘制时间趋势图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 计算移动平均
        rolling_mean = data['red_sum'].rolling(window=10).mean()
        
        # 绘制趋势线
        ax.plot(data['date'], data['red_sum'], 'o-', alpha=0.4, label='原始数据')
        ax.plot(data['date'], rolling_mean, 'r-', label='移动平均')
        
        ax.set_title('红球和值走势')
        ax.legend()
        
        return fig
        
    def plot_winning_patterns(self, data: pd.DataFrame) -> Figure:
        """绘制中奖规律图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 12))
        
        # 奇偶比例
        self._plot_odd_even_ratio(data, ax1)
        
        # 区间分布
        self._plot_zone_distribution(data, ax2)
        
        # 连号分布
        self._plot_consecutive_distribution(data, ax3)
        
        # 和值分布
        self._plot_sum_distribution(data, ax4)
        
        return fig