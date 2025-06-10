import pandas as pd
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np

from .base_analyzer import BaseAnalyzer
from ..exceptions import AnalysisError

class FrequencyAnalyzer(BaseAnalyzer):
    """频率分析器"""
    
    def analyze(self, data: Optional[pd.DataFrame] = None, periods: int = 100, **kwargs) -> Dict[str, Any]:
        """执行频率分析
        
        Args:
            data: 历史数据，如果为None则自动获取
            periods: 分析期数
            **kwargs: 其他参数
            
        Returns:
            频率分析结果
        """
        try:
            # 获取数据
            if data is None:
                data = self.get_recent_data(periods)
            
            if not self.validate_data(data):
                raise AnalysisError("数据验证失败")
            
            result = {}
            
            # 分析主要号码区域
            if self.lottery_type == 'ssq':
                result.update(self._analyze_ssq_frequency(data))
            elif self.lottery_type == 'dlt':
                result.update(self._analyze_dlt_frequency(data))
            
            return self.format_analysis_result(result)
            
        except Exception as e:
            self.logger.error(f"频率分析失败: {str(e)}")
            raise AnalysisError(f"频率分析失败: {str(e)}")
    
    def _analyze_ssq_frequency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析双色球频率"""
        result = {}
        
        # 红球分析
        red_numbers = self.extract_numbers(data, 'red_numbers')
        if red_numbers:
            red_frequency = self.calculate_frequency(red_numbers, self.config['red_range'])
            red_missing = self.calculate_missing_values(red_numbers, self.config['red_range'])
            red_classification = self.classify_hot_cold_numbers(red_frequency)
            red_stats = self.calculate_statistics(red_numbers)
            red_patterns = self.analyze_patterns(red_numbers)
            
            result['red_ball'] = {
                'frequency': red_frequency,
                'missing_values': red_missing,
                'classification': red_classification,
                'statistics': red_stats,
                'patterns': red_patterns,
                'top_10_hot': self._get_top_numbers(red_frequency, 10, reverse=True),
                'top_10_cold': self._get_top_numbers(red_frequency, 10, reverse=False)
            }
        
        # 蓝球分析
        if 'blue_number' in data.columns:
            blue_numbers = [[int(row['blue_number'])] for _, row in data.iterrows() 
                           if pd.notna(row['blue_number'])]
            if blue_numbers:
                blue_frequency = self.calculate_frequency(blue_numbers, self.config['blue_range'])
                blue_missing = self.calculate_missing_values(blue_numbers, self.config['blue_range'])
                blue_classification = self.classify_hot_cold_numbers(blue_frequency)
                blue_stats = self.calculate_statistics(blue_numbers)
                
                result['blue_ball'] = {
                    'frequency': blue_frequency,
                    'missing_values': blue_missing,
                    'classification': blue_classification,
                    'statistics': blue_stats,
                    'top_5_hot': self._get_top_numbers(blue_frequency, 5, reverse=True),
                    'top_5_cold': self._get_top_numbers(blue_frequency, 5, reverse=False)
                }
        
        return result
    
    def _analyze_dlt_frequency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析大乐透频率"""
        result = {}
        
        # 前区分析
        front_numbers = self.extract_numbers(data, 'front_numbers')
        if front_numbers:
            front_frequency = self.calculate_frequency(front_numbers, self.config['front_range'])
            front_missing = self.calculate_missing_values(front_numbers, self.config['front_range'])
            front_classification = self.classify_hot_cold_numbers(front_frequency)
            front_stats = self.calculate_statistics(front_numbers)
            front_patterns = self.analyze_patterns(front_numbers)
            
            result['front_area'] = {
                'frequency': front_frequency,
                'missing_values': front_missing,
                'classification': front_classification,
                'statistics': front_stats,
                'patterns': front_patterns,
                'top_10_hot': self._get_top_numbers(front_frequency, 10, reverse=True),
                'top_10_cold': self._get_top_numbers(front_frequency, 10, reverse=False)
            }
        
        # 后区分析
        back_numbers = self.extract_numbers(data, 'back_numbers')
        if back_numbers:
            back_frequency = self.calculate_frequency(back_numbers, self.config['back_range'])
            back_missing = self.calculate_missing_values(back_numbers, self.config['back_range'])
            back_classification = self.classify_hot_cold_numbers(back_frequency)
            back_stats = self.calculate_statistics(back_numbers)
            back_patterns = self.analyze_patterns(back_numbers)
            
            result['back_area'] = {
                'frequency': back_frequency,
                'missing_values': back_missing,
                'classification': back_classification,
                'statistics': back_stats,
                'patterns': back_patterns,
                'top_5_hot': self._get_top_numbers(back_frequency, 5, reverse=True),
                'top_5_cold': self._get_top_numbers(back_frequency, 5, reverse=False)
            }
        
        return result
    
    def _get_top_numbers(self, frequency: Dict[int, int], count: int, reverse: bool = True) -> List[Dict[str, Any]]:
        """获取频率最高/最低的号码
        
        Args:
            frequency: 频率字典
            count: 返回数量
            reverse: True为最高频率，False为最低频率
            
        Returns:
            排序后的号码列表
        """
        sorted_items = sorted(frequency.items(), key=lambda x: x[1], reverse=reverse)
        return [{'number': num, 'frequency': freq} for num, freq in sorted_items[:count]]
    
    def analyze_frequency_trends(self, data: Optional[pd.DataFrame] = None, 
                               periods: int = 100, window_size: int = 10) -> Dict[str, Any]:
        """分析频率趋势
        
        Args:
            data: 历史数据
            periods: 分析期数
            window_size: 滑动窗口大小
            
        Returns:
            频率趋势分析结果
        """
        try:
            if data is None:
                data = self.get_recent_data(periods)
            
            if not self.validate_data(data):
                raise AnalysisError("数据验证失败")
            
            result = {}
            
            if self.lottery_type == 'ssq':
                red_numbers = self.extract_numbers(data, 'red_numbers')
                if red_numbers:
                    red_trends = self.analyze_trends(red_numbers, window_size)
                    result['red_ball_trends'] = red_trends
                
                if 'blue_number' in data.columns:
                    blue_numbers = [[int(row['blue_number'])] for _, row in data.iterrows() 
                                   if pd.notna(row['blue_number'])]
                    if blue_numbers:
                        blue_trends = self.analyze_trends(blue_numbers, window_size)
                        result['blue_ball_trends'] = blue_trends
            
            elif self.lottery_type == 'dlt':
                front_numbers = self.extract_numbers(data, 'front_numbers')
                if front_numbers:
                    front_trends = self.analyze_trends(front_numbers, window_size)
                    result['front_area_trends'] = front_trends
                
                back_numbers = self.extract_numbers(data, 'back_numbers')
                if back_numbers:
                    back_trends = self.analyze_trends(back_numbers, window_size)
                    result['back_area_trends'] = back_trends
            
            return self.format_analysis_result(result)
            
        except Exception as e:
            self.logger.error(f"频率趋势分析失败: {str(e)}")
            raise AnalysisError(f"频率趋势分析失败: {str(e)}")
    
    def get_recommendation(self, data: Optional[pd.DataFrame] = None, 
                          periods: int = 50) -> Dict[str, Any]:
        """基于频率分析获取推荐号码
        
        Args:
            data: 历史数据
            periods: 分析期数
            
        Returns:
            推荐号码
        """
        try:
            analysis_result = self.analyze(data, periods)
            recommendations = {}
            
            if self.lottery_type == 'ssq':
                if 'red_ball' in analysis_result['data']:
                    red_data = analysis_result['data']['red_ball']
                    
                    # 推荐策略：热号+冷号+正常号的组合
                    hot_numbers = red_data['classification']['hot'][:8]
                    cold_numbers = red_data['classification']['cold'][:8]
                    normal_numbers = red_data['classification']['normal'][:10]
                    
                    recommendations['red_ball'] = {
                        'hot_candidates': hot_numbers,
                        'cold_candidates': cold_numbers,
                        'normal_candidates': normal_numbers,
                        'suggested_combination': self._suggest_red_combination(
                            hot_numbers, cold_numbers, normal_numbers
                        )
                    }
                
                if 'blue_ball' in analysis_result['data']:
                    blue_data = analysis_result['data']['blue_ball']
                    hot_blue = blue_data['classification']['hot'][:3]
                    normal_blue = blue_data['classification']['normal'][:5]
                    
                    recommendations['blue_ball'] = {
                        'hot_candidates': hot_blue,
                        'normal_candidates': normal_blue,
                        'suggested_numbers': hot_blue + normal_blue
                    }
            
            elif self.lottery_type == 'dlt':
                if 'front_area' in analysis_result['data']:
                    front_data = analysis_result['data']['front_area']
                    
                    hot_front = front_data['classification']['hot'][:8]
                    cold_front = front_data['classification']['cold'][:8]
                    normal_front = front_data['classification']['normal'][:10]
                    
                    recommendations['front_area'] = {
                        'hot_candidates': hot_front,
                        'cold_candidates': cold_front,
                        'normal_candidates': normal_front,
                        'suggested_combination': self._suggest_front_combination(
                            hot_front, cold_front, normal_front
                        )
                    }
                
                if 'back_area' in analysis_result['data']:
                    back_data = analysis_result['data']['back_area']
                    hot_back = back_data['classification']['hot'][:4]
                    normal_back = back_data['classification']['normal'][:6]
                    
                    recommendations['back_area'] = {
                        'hot_candidates': hot_back,
                        'normal_candidates': normal_back,
                        'suggested_combination': hot_back + normal_back
                    }
            
            return self.format_analysis_result(recommendations)
            
        except Exception as e:
            self.logger.error(f"获取推荐号码失败: {str(e)}")
            raise AnalysisError(f"获取推荐号码失败: {str(e)}")
    
    def _suggest_red_combination(self, hot: List[int], cold: List[int], normal: List[int]) -> List[int]:
        """推荐红球组合"""
        import random
        
        # 策略：2-3个热号，1-2个冷号，1-3个正常号
        selected = []
        
        # 选择热号
        hot_count = min(random.randint(2, 3), len(hot))
        selected.extend(random.sample(hot, hot_count))
        
        # 选择冷号
        remaining_count = 6 - len(selected)
        cold_count = min(random.randint(1, 2), len(cold), remaining_count)
        selected.extend(random.sample(cold, cold_count))
        
        # 用正常号补足
        remaining_count = 6 - len(selected)
        if remaining_count > 0 and normal:
            normal_count = min(remaining_count, len(normal))
            selected.extend(random.sample(normal, normal_count))
        
        return sorted(selected[:6])
    
    def _suggest_front_combination(self, hot: List[int], cold: List[int], normal: List[int]) -> List[int]:
        """推荐前区组合"""
        import random
        
        # 策略：2个热号，1个冷号，2个正常号
        selected = []
        
        # 选择热号
        hot_count = min(2, len(hot))
        selected.extend(random.sample(hot, hot_count))
        
        # 选择冷号
        remaining_count = 5 - len(selected)
        cold_count = min(1, len(cold), remaining_count)
        selected.extend(random.sample(cold, cold_count))
        
        # 用正常号补足
        remaining_count = 5 - len(selected)
        if remaining_count > 0 and normal:
            normal_count = min(remaining_count, len(normal))
            selected.extend(random.sample(normal, normal_count))
        
        return sorted(selected[:5])
