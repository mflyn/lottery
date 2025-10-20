#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大乐透号码评价器
基于历史数据从统计角度评价大乐透号码
"""

from typing import Dict, List, Tuple, Any
from collections import Counter
import numpy as np
from .base_evaluator import BaseNumberEvaluator


class DLTNumberEvaluator(BaseNumberEvaluator):
    """大乐透号码评价器"""
    
    def __init__(self, history_file: str = 'data/dlt_history.json'):
        """初始化大乐透评价器
        
        Args:
            history_file: 历史数据文件路径
        """
        super().__init__(history_file)
        self.front_range = (1, 35)  # 前区范围
        self.back_range = (1, 12)   # 后区范围
        self.front_count = 5  # 前区数量
        self.back_count = 2   # 后区数量
    
    def evaluate(self, front_numbers: List[int], back_numbers: List[int]) -> Dict[str, Any]:
        """评价大乐透号码
        
        Args:
            front_numbers: 前区号码列表（5个）
            back_numbers: 后区号码列表（2个）
            
        Returns:
            评价结果字典
        """
        # 加载历史数据
        history_data = self.load_history()
        
        # 1. 频率分析
        freq_result = self._analyze_frequency(front_numbers, back_numbers, history_data)
        
        # 2. 遗漏分析
        missing_result = self._analyze_missing(front_numbers, back_numbers, history_data)
        
        # 3. 模式分析
        pattern_result = self._analyze_patterns(front_numbers, back_numbers)
        
        # 4. 历史对比
        historical_result = self._check_historical(front_numbers, back_numbers, history_data)
        
        # 5. 计算得分
        scores = self._calculate_scores(freq_result, missing_result, pattern_result, historical_result)
        
        # 6. 生成建议
        suggestions = self._generate_suggestions(freq_result, missing_result, pattern_result, historical_result)
        
        return {
            'frequency': freq_result,
            'missing': missing_result,
            'pattern': pattern_result,
            'historical': historical_result,
            'scores': scores,
            'total_score': scores['total'],
            'rating': scores['rating'],
            'stars': scores['stars'],
            'suggestions': suggestions
        }
    
    def _analyze_frequency(self, front_numbers: List[int], back_numbers: List[int], 
                          history_data: List[Dict], periods: int = 100) -> Dict:
        """频率分析
        
        Args:
            front_numbers: 前区号码列表
            back_numbers: 后区号码列表
            history_data: 历史数据
            periods: 分析期数
            
        Returns:
            频率分析结果
        """
        recent_data = history_data[:periods]
        
        # 统计频率
        front_counter = Counter()
        back_counter = Counter()
        
        for draw in recent_data:
            front_counter.update(draw['front_numbers'])
            back_counter.update(draw['back_numbers'])
        
        # 计算理论频率
        front_theory = periods * 5 / 35  # 每个前区号码理论出现次数
        back_theory = periods * 2 / 12   # 每个后区号码理论出现次数
        
        # 分析待评价号码的频率
        front_freq_details = []
        for num in front_numbers:
            freq = front_counter.get(num, 0)
            classification, icon = self.classify_number_by_frequency(freq, front_theory)
            deviation = ((freq - front_theory) / front_theory * 100) if front_theory > 0 else 0
            
            front_freq_details.append({
                'number': num,
                'frequency': freq,
                'theoretical': round(front_theory, 1),
                'deviation': round(deviation, 1),
                'classification': classification,
                'icon': icon
            })
        
        back_freq_details = []
        for num in back_numbers:
            freq = back_counter.get(num, 0)
            classification, icon = self.classify_number_by_frequency(freq, back_theory)
            deviation = ((freq - back_theory) / back_theory * 100) if back_theory > 0 else 0
            
            back_freq_details.append({
                'number': num,
                'frequency': freq,
                'theoretical': round(back_theory, 1),
                'deviation': round(deviation, 1),
                'classification': classification,
                'icon': icon
            })
        
        return {
            'periods': periods,
            'front_details': front_freq_details,
            'back_details': back_freq_details,
            'front_theory': front_theory,
            'back_theory': back_theory
        }
    
    def _analyze_missing(self, front_numbers: List[int], back_numbers: List[int], 
                        history_data: List[Dict]) -> Dict:
        """遗漏分析
        
        Args:
            front_numbers: 前区号码列表
            back_numbers: 后区号码列表
            history_data: 历史数据
            
        Returns:
            遗漏分析结果
        """
        # 计算所有号码的遗漏期数
        front_missing = {i: 0 for i in range(1, 36)}
        back_missing = {i: 0 for i in range(1, 13)}
        
        # 从最新一期开始，计算每个号码的遗漏期数
        for num in range(1, 36):
            for i, draw in enumerate(history_data):
                if num in draw['front_numbers']:
                    front_missing[num] = i
                    break
        
        for num in range(1, 13):
            for i, draw in enumerate(history_data):
                if num in draw['back_numbers']:
                    back_missing[num] = i
                    break
        
        # 计算平均遗漏
        avg_front_missing = np.mean(list(front_missing.values()))
        avg_back_missing = np.mean(list(back_missing.values()))
        
        # 分析待评价号码的遗漏
        front_missing_details = []
        for num in front_numbers:
            missing = front_missing[num]
            classification, icon = self.classify_missing_period(missing, avg_front_missing)
            
            front_missing_details.append({
                'number': num,
                'missing': missing,
                'classification': classification,
                'icon': icon
            })
        
        back_missing_details = []
        for num in back_numbers:
            missing = back_missing[num]
            classification, icon = self.classify_missing_period(missing, avg_back_missing)
            
            back_missing_details.append({
                'number': num,
                'missing': missing,
                'classification': classification,
                'icon': icon
            })
        
        return {
            'front_details': front_missing_details,
            'back_details': back_missing_details,
            'avg_front_missing': round(avg_front_missing, 1),
            'avg_back_missing': round(avg_back_missing, 1)
        }
    
    def _analyze_patterns(self, front_numbers: List[int], back_numbers: List[int]) -> Dict:
        """模式分析
        
        Args:
            front_numbers: 前区号码列表
            back_numbers: 后区号码列表
            
        Returns:
            模式分析结果
        """
        sorted_front = sorted(front_numbers)
        sorted_back = sorted(back_numbers)
        
        # 前区分析
        # 1. 奇偶比
        odd_count = sum(1 for n in front_numbers if n % 2 == 1)
        even_count = 5 - odd_count
        odd_even_ratio = f"{odd_count}:{even_count}"
        
        if 2 <= odd_count <= 3:
            odd_even_rating = "奇偶比合理，常见模式"
            odd_even_icon = "✅"
        elif 1 <= odd_count <= 4:
            odd_even_rating = "奇偶比可接受"
            odd_even_icon = "✓"
        else:
            odd_even_rating = "奇偶比极端"
            odd_even_icon = "⚠️"
        
        # 2. 大小比（大号：18-35，小号：1-17）
        big_count = sum(1 for n in front_numbers if n >= 18)
        small_count = 5 - big_count
        big_small_ratio = f"{big_count}:{small_count}"
        
        if 2 <= big_count <= 3:
            big_small_rating = "大小比合理，常见模式"
            big_small_icon = "✅"
        elif 1 <= big_count <= 4:
            big_small_rating = "大小比可接受"
            big_small_icon = "✓"
        else:
            big_small_rating = "大小比极端"
            big_small_icon = "⚠️"
        
        # 3. 区间分布（1-12, 13-24, 25-35）
        zone1 = sum(1 for n in front_numbers if 1 <= n <= 12)
        zone2 = sum(1 for n in front_numbers if 13 <= n <= 24)
        zone3 = sum(1 for n in front_numbers if 25 <= n <= 35)
        zone_distribution = f"{zone1}-{zone2}-{zone3}"
        
        if all(z >= 1 for z in [zone1, zone2, zone3]):
            zone_rating = "三区都有号码，分布均衡"
            zone_icon = "✅"
        elif sum(1 for z in [zone1, zone2, zone3] if z > 0) >= 2:
            zone_rating = "覆盖两个区间，分布合理"
            zone_icon = "✓"
        else:
            zone_rating = "号码集中在一个区间"
            zone_icon = "⚠️"
        
        # 4. 连号检测
        consecutive = []
        for i in range(len(sorted_front) - 1):
            if sorted_front[i+1] - sorted_front[i] == 1:
                consecutive.append((sorted_front[i], sorted_front[i+1]))
        
        if len(consecutive) == 0:
            consecutive_rating = "无连号，独特性较高"
            consecutive_icon = "✓"
        elif len(consecutive) == 1:
            consecutive_rating = "有连号，符合常见模式"
            consecutive_icon = "✓"
        else:
            consecutive_rating = "连号较多"
            consecutive_icon = "⚠️"
        
        # 5. 和值
        sum_value = sum(front_numbers)
        
        if 70 <= sum_value <= 110:
            sum_rating = "和值在常见范围内（70-110）"
            sum_icon = "✅"
        elif 50 <= sum_value <= 130:
            sum_rating = "和值合理（50-130）"
            sum_icon = "✓"
        else:
            sum_rating = "和值偏离常见范围"
            sum_icon = "⚠️"
        
        # 6. 跨度
        span = max(front_numbers) - min(front_numbers)
        
        if 15 <= span <= 30:
            span_rating = "跨度在常见范围内（15-30）"
            span_icon = "✅"
        elif 10 <= span <= 34:
            span_rating = "跨度合理（10-34）"
            span_icon = "✓"
        else:
            span_rating = "跨度偏离常见范围"
            span_icon = "⚠️"
        
        # 7. AC值
        ac_value = self._calculate_ac_value(sorted_front)
        
        if ac_value >= 5:
            ac_rating = "AC值较高，号码复杂度好"
            ac_icon = "✅"
        elif ac_value >= 3:
            ac_rating = "AC值中等，复杂度合理"
            ac_icon = "✓"
        else:
            ac_rating = "AC值较低"
            ac_icon = "⚠️"
        
        # 后区分析
        back_odd_count = sum(1 for n in back_numbers if n % 2 == 1)
        back_even_count = 2 - back_odd_count
        back_odd_even_ratio = f"{back_odd_count}:{back_even_count}"
        
        if back_odd_count == 1:
            back_odd_even_rating = "后区奇偶比均衡"
            back_odd_even_icon = "✅"
        else:
            back_odd_even_rating = "后区奇偶比可接受"
            back_odd_even_icon = "✓"
        
        return {
            'front': {
                'odd_even': {
                    'ratio': odd_even_ratio,
                    'rating': odd_even_rating,
                    'icon': odd_even_icon
                },
                'big_small': {
                    'ratio': big_small_ratio,
                    'rating': big_small_rating,
                    'icon': big_small_icon
                },
                'zone': {
                    'distribution': zone_distribution,
                    'rating': zone_rating,
                    'icon': zone_icon
                },
                'consecutive': {
                    'count': len(consecutive),
                    'pairs': consecutive,
                    'rating': consecutive_rating,
                    'icon': consecutive_icon
                },
                'sum': {
                    'value': sum_value,
                    'rating': sum_rating,
                    'icon': sum_icon
                },
                'span': {
                    'value': span,
                    'rating': span_rating,
                    'icon': span_icon
                },
                'ac_value': {
                    'value': ac_value,
                    'rating': ac_rating,
                    'icon': ac_icon
                }
            },
            'back': {
                'odd_even': {
                    'ratio': back_odd_even_ratio,
                    'rating': back_odd_even_rating,
                    'icon': back_odd_even_icon
                }
            }
        }
    
    def _calculate_ac_value(self, numbers: List[int]) -> int:
        """计算AC值（号码复杂度）"""
        differences = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                differences.add(abs(numbers[i] - numbers[j]))
        return len(differences) - (len(numbers) - 1)
    
    def _check_historical(self, front_numbers: List[int], back_numbers: List[int], 
                         history_data: List[Dict]) -> Dict:
        """历史对比"""
        front_set = set(front_numbers)
        back_set = set(back_numbers)
        
        exact_match = False
        exact_match_period = None
        front_match_counts = []
        back_match_counts = []
        max_match_count = 0
        max_match_period = None
        
        for draw in history_data:
            draw_front_set = set(draw['front_numbers'])
            draw_back_set = set(draw['back_numbers'])
            
            # 检查完全匹配
            if draw_front_set == front_set and draw_back_set == back_set:
                exact_match = True
                exact_match_period = draw['draw_num']
                break
            
            # 统计前区匹配数
            front_match = len(front_set & draw_front_set)
            front_match_counts.append(front_match)
            
            # 统计后区匹配数
            back_match = len(back_set & draw_back_set)
            back_match_counts.append(back_match)
            
            # 记录最大匹配
            total_match = front_match + back_match
            if total_match > max_match_count:
                max_match_count = total_match
                max_match_period = draw['draw_num']
        
        # 评价
        if exact_match:
            rating = "警告：这注号码在历史上完全出现过"
            icon = "⚠️"
        elif max_match_count >= 6:
            rating = "与历史号码相似度较高"
            icon = "⚠️"
        elif max_match_count >= 5:
            rating = "与历史号码有一定相似度"
            icon = "✓"
        else:
            rating = "独特性较好"
            icon = "✅"
        
        return {
            'exact_match': exact_match,
            'exact_match_period': exact_match_period,
            'max_front_match': max(front_match_counts) if front_match_counts else 0,
            'max_back_match': max(back_match_counts) if back_match_counts else 0,
            'max_total_match': max_match_count,
            'max_match_period': max_match_period,
            'avg_front_match': round(np.mean(front_match_counts), 2) if front_match_counts else 0,
            'avg_back_match': round(np.mean(back_match_counts), 2) if back_match_counts else 0,
            'rating': rating,
            'icon': icon
        }
    
    def _calculate_scores(self, freq_result: Dict, missing_result: Dict, 
                         pattern_result: Dict, historical_result: Dict) -> Dict:
        """计算各维度得分"""
        # 1. 频率得分
        front_freqs = [detail['frequency'] for detail in freq_result['front_details']]
        avg_front_freq = np.mean(front_freqs)
        freq_score = min(100, (avg_front_freq / freq_result['front_theory']) * 50 + 50)
        
        # 2. 遗漏得分
        front_missings = [detail['missing'] for detail in missing_result['front_details']]
        avg_front_missing = np.mean(front_missings)
        missing_score = max(0, min(100, 100 - avg_front_missing * 2))
        
        # 3. 模式得分
        pattern_score = 0
        front_pattern = pattern_result['front']
        
        if front_pattern['odd_even']['icon'] in ['✅', '✓']:
            pattern_score += 15
        if front_pattern['big_small']['icon'] in ['✅', '✓']:
            pattern_score += 15
        if front_pattern['zone']['icon'] in ['✅', '✓']:
            pattern_score += 20
        if front_pattern['sum']['icon'] in ['✅', '✓']:
            pattern_score += 20
        if front_pattern['ac_value']['icon'] in ['✅', '✓']:
            pattern_score += 15
        if pattern_result['back']['odd_even']['icon'] in ['✅', '✓']:
            pattern_score += 15
        
        # 4. 独特性得分
        uniqueness_score = max(0, 100 - historical_result['max_total_match'] * 12)
        
        # 5. 综合得分
        return self.calculate_composite_score(freq_score, missing_score, pattern_score, uniqueness_score)
    
    def _generate_suggestions(self, freq_result: Dict, missing_result: Dict, 
                             pattern_result: Dict, historical_result: Dict) -> List[str]:
        """生成专家建议"""
        suggestions = []
        
        # 频率建议
        front_freqs = [detail['frequency'] for detail in freq_result['front_details']]
        avg_front_freq = np.mean(front_freqs)
        
        if avg_front_freq < freq_result['front_theory'] * 0.7:
            suggestions.append("前区号码整体偏冷")
        elif avg_front_freq > freq_result['front_theory'] * 1.3:
            suggestions.append("前区号码整体偏热")
        
        # 遗漏建议
        front_missings = [detail['missing'] for detail in missing_result['front_details']]
        if max(front_missings) > 30:
            suggestions.append("部分前区号码遗漏较长")
        
        # 模式建议
        front_pattern = pattern_result['front']
        if front_pattern['consecutive']['count'] >= 2:
            suggestions.append("连号较多，可能降低独特性")
        
        if front_pattern['sum']['icon'] == '⚠️':
            suggestions.append("和值偏离常见范围")
        
        # 历史建议
        if historical_result['exact_match']:
            suggestions.append("警告：这注号码在历史上完全出现过")
        elif historical_result['max_total_match'] >= 6:
            suggestions.append("与历史号码相似度较高")
        
        # 如果没有建议
        if not suggestions:
            suggestions.append("这是一注平衡性和独特性都不错的号码")
        
        return suggestions

