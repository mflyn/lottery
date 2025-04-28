import pandas as pd
import numpy as np
from typing import Dict, Any
from ..models.lottery_types import SSQNumber

# 定义错误类
class SSQError(Exception):
    """双色球错误类"""
    pass

class ErrorCode:
    """错误代码"""
    UNKNOWN_ERROR = 1000
    DATA_ERROR = 1001

class DataExplorationAnalyzer:
    """数据探索分析器"""
    
    def analyze_distribution(self, data: pd.DataFrame, 
                           date_range: tuple = None,
                           number_range: tuple = None) -> Dict[str, Any]:
        """分析号码分布
        
        Args:
            data: 开奖数据DataFrame
            date_range: 日期范围元组 (start_date, end_date)
            number_range: 号码范围元组 (min_num, max_num)
        """
        try:
            filtered_data = self._apply_filters(data, date_range, number_range)
            
            return {
                'frequency_dist': self._analyze_frequency(filtered_data),
                'time_trend': self._analyze_trend(filtered_data),
                'correlations': self._analyze_correlation(filtered_data),
                'number_dist': self._analyze_number_distribution(filtered_data),
                'summary_stats': self._get_summary_stats(filtered_data)
            }
            
        except Exception as e:
            raise SSQError("数据探索分析失败") from e
            
    def _apply_filters(self, data: pd.DataFrame,
                      date_range: tuple = None,
                      number_range: tuple = None) -> pd.DataFrame:
        """应用数据过滤"""
        filtered_data = data.copy()
        
        if date_range:
            start_date, end_date = date_range
            filtered_data = filtered_data[
                (filtered_data['date'] >= start_date) &
                (filtered_data['date'] <= end_date)
            ]
            
        if number_range:
            min_num, max_num = number_range
            filtered_data = filtered_data[
                (filtered_data >= min_num) & (filtered_data <= max_num)
            ]
            
        return filtered_data
        
    def _analyze_frequency(self, data: pd.DataFrame) -> Dict:
        """分析频率分布"""
        return {
            'red_numbers': data['red_numbers'].value_counts().to_dict(),
            'blue_numbers': data['blue_number'].value_counts().to_dict()
        }
        
    def _analyze_trend(self, data: pd.DataFrame) -> Dict:
        """分析时间趋势"""
        return {
            'red_trend': data.groupby('date')['red_numbers'].mean().to_dict(),
            'blue_trend': data.groupby('date')['blue_number'].mean().to_dict()
        }
        
    def _analyze_correlation(self, data: pd.DataFrame) -> Dict:
        """分析相关性"""
        return data[['red_numbers', 'blue_number']].corr().to_dict()
        
    def _analyze_number_distribution(self, data: pd.DataFrame) -> Dict:
        """分析号码分布"""
        return {
            'red_dist': data['red_numbers'].describe().to_dict(),
            'blue_dist': data['blue_number'].describe().to_dict()
        }
        
    def _get_summary_stats(self, data: pd.DataFrame) -> Dict:
        """获取统计摘要"""
        return {
            'red_stats': data['red_numbers'].describe().to_dict(),
            'blue_stats': data['blue_number'].describe().to_dict(),
            'total_draws': len(data),
            'date_range': (data['date'].min(), data['date'].max())
        }

class DataVisualizer:
    def __init__(self):
        self.plt_style = 'seaborn'
        self.default_figsize = (10, 6)
        
    def create_interactive_dashboard(self, data: pd.DataFrame) -> Dict:
        """创建交互式仪表板"""
        figures = {}
        
        # 频率分布图
        figures['frequency'] = self._create_frequency_plot(data)
        
        # 时间趋势图
        figures['trend'] = self._create_trend_plot(data)
        
        # 相关性热图
        figures['correlation'] = self._create_correlation_heatmap(data)
        
        # 预测结果对比图
        figures['prediction'] = self._create_prediction_plot(data)
        
        return figures
        
    def _create_frequency_plot(self, data: pd.DataFrame):
        """创建频率分布交互图"""
        fig = go.Figure()
        
        # 添加柱状图
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['frequency'],
            name='出现频率'
        ))
        
        # 添加移动平均线
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['frequency'].rolling(5).mean(),
            name='5期移动平均'
        ))
        
        # 设置交互选项
        fig.update_layout(
            title='号码出现频率分布',
            xaxis_title='号码',
            yaxis_title='频率',
            hovermode='x'
        )
        
        return fig
