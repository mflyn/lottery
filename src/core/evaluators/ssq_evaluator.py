#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双色球号码评价器
基于历史数据从统计角度评价双色球号码
"""

from typing import Dict, List, Tuple, Any
from collections import Counter
import numpy as np
from .base_evaluator import BaseNumberEvaluator


class SSQNumberEvaluator(BaseNumberEvaluator):
    """双色球号码评价器"""
    
    def __init__(self, history_file: str = 'data/ssq_history.json'):
        """初始化双色球评价器
        
        Args:
            history_file: 历史数据文件路径
        """
        super().__init__(history_file)
        self.red_range = (1, 33)  # 红球范围
        self.blue_range = (1, 16)  # 蓝球范围
        self.red_count = 6  # 红球数量
    
    def evaluate(self, red_numbers: List[int], blue_number: int) -> Dict[str, Any]:
        """评价双色球号码
        
        Args:
            red_numbers: 红球号码列表（6个）
            blue_number: 蓝球号码（1个）
            
        Returns:
            评价结果字典
        """
        # 加载历史数据
        history_data = self.load_history()
        
        # 1. 频率分析
        freq_result = self._analyze_frequency(red_numbers, blue_number, history_data)
        
        # 2. 遗漏分析
        missing_result = self._analyze_missing(red_numbers, blue_number, history_data)
        
        # 3. 模式分析
        pattern_result = self._analyze_patterns(red_numbers)
        
        # 4. 历史对比
        historical_result = self._check_historical(red_numbers, blue_number, history_data)
        
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
    
    def _analyze_frequency(self, red_numbers: List[int], blue_number: int, 
                          history_data: List[Dict], periods: int = 100) -> Dict:
        """频率分析
        
        Args:
            red_numbers: 红球号码列表
            blue_number: 蓝球号码
            history_data: 历史数据
            periods: 分析期数
            
        Returns:
            频率分析结果
        """
        recent_data = history_data[:periods]
        
        # 统计频率（带缓存）
        cache_key = self.get_cache_key('freq_counters', periods)
        counters = self._cache.get(cache_key)
        if counters is None:
            red_counter = Counter()
            blue_counter = Counter()
            for draw in recent_data:
                red_counter.update(draw['red_numbers'])
                blue_counter[draw['blue_number']] += 1
            counters = {'red': red_counter, 'blue': blue_counter}
            self._cache[cache_key] = counters
        else:
            red_counter = counters['red']
            blue_counter = counters['blue']

        # 计算理论频率
        red_theory = periods * 6 / 33  # 每个红球理论出现次数
        blue_theory = periods / 16     # 每个蓝球理论出现次数
        
        # 分析待评价号码的频率
        red_freq_details = []
        for num in red_numbers:
            freq = red_counter.get(num, 0)
            classification, icon = self.classify_number_by_frequency(freq, red_theory)
            deviation = ((freq - red_theory) / red_theory * 100) if red_theory > 0 else 0
            
            red_freq_details.append({
                'number': num,
                'frequency': freq,
                'theoretical': round(red_theory, 1),
                'deviation': round(deviation, 1),
                'classification': classification,
                'icon': icon
            })
        
        blue_freq = blue_counter.get(blue_number, 0)
        blue_classification, blue_icon = self.classify_number_by_frequency(blue_freq, blue_theory)
        blue_deviation = ((blue_freq - blue_theory) / blue_theory * 100) if blue_theory > 0 else 0
        
        return {
            'periods': periods,
            'red_details': red_freq_details,
            'blue_detail': {
                'number': blue_number,
                'frequency': blue_freq,
                'theoretical': round(blue_theory, 1),
                'deviation': round(blue_deviation, 1),
                'classification': blue_classification,
                'icon': blue_icon
            },
            'red_theory': red_theory,
            'blue_theory': blue_theory
        }
    
    def _analyze_missing(self, red_numbers: List[int], blue_number: int, 
                        history_data: List[Dict]) -> Dict:
        """遗漏分析
        
        Args:
            red_numbers: 红球号码列表
            blue_number: 蓝球号码
            history_data: 历史数据
            
        Returns:
            遗漏分析结果
        """
        # 计算所有号码的遗漏期数（带缓存）
        cache_key = 'missing_maps'
        missing_maps = self._cache.get(cache_key)
        if missing_maps is None:
            red_missing = {i: 0 for i in range(1, 34)}
            blue_missing = {i: 0 for i in range(1, 17)}
            # 从最新一期开始，计算每个号码的遗漏期数
            for num in range(1, 34):
                for i, draw in enumerate(history_data):
                    if num in draw['red_numbers']:
                        red_missing[num] = i
                        break
            for num in range(1, 17):
                for i, draw in enumerate(history_data):
                    if num == draw['blue_number']:
                        blue_missing[num] = i
                        break
            avg_red_missing = float(np.mean(list(red_missing.values())))
            avg_blue_missing = float(np.mean(list(blue_missing.values())))
            missing_maps = {
                'red_missing': red_missing,
                'blue_missing': blue_missing,
                'avg_red_missing': round(avg_red_missing, 1),
                'avg_blue_missing': round(avg_blue_missing, 1)
            }
            self._cache[cache_key] = missing_maps
        else:
            red_missing = missing_maps['red_missing']
            blue_missing = missing_maps['blue_missing']
            avg_red_missing = missing_maps['avg_red_missing']
            avg_blue_missing = missing_maps['avg_blue_missing']

        # 分析待评价号码的遗漏
        red_missing_details = []
        for num in red_numbers:
            missing = red_missing[num]
            classification, icon = self.classify_missing_period(missing, avg_red_missing)
            
            red_missing_details.append({
                'number': num,
                'missing': missing,
                'classification': classification,
                'icon': icon
            })
        
        blue_miss = blue_missing[blue_number]
        blue_classification, blue_icon = self.classify_missing_period(blue_miss, avg_blue_missing)
        
        return {
            'red_details': red_missing_details,
            'blue_detail': {
                'number': blue_number,
                'missing': blue_miss,
                'classification': blue_classification,
                'icon': blue_icon
            },
            'avg_red_missing': round(avg_red_missing, 1),
            'avg_blue_missing': round(avg_blue_missing, 1)
        }
    
    def _analyze_patterns(self, red_numbers: List[int]) -> Dict:
        """模式分析
        
        Args:
            red_numbers: 红球号码列表
            
        Returns:
            模式分析结果
        """
        sorted_nums = sorted(red_numbers)
        
        # 1. 奇偶比
        odd_count = sum(1 for n in red_numbers if n % 2 == 1)
        even_count = 6 - odd_count
        odd_even_ratio = f"{odd_count}:{even_count}"
        
        # 评价奇偶比
        if odd_count == 3:
            odd_even_rating = "标准奇偶比（3:3），平衡性好"
            odd_even_icon = "✅"
        elif 2 <= odd_count <= 4:
            odd_even_rating = "奇偶比合理，常见模式"
            odd_even_icon = "✓"
        else:
            odd_even_rating = "奇偶比极端，出现概率较低"
            odd_even_icon = "⚠️"
        
        # 2. 大小比（大号：18-33，小号：1-17）
        big_count = sum(1 for n in red_numbers if n >= 18)
        small_count = 6 - big_count
        big_small_ratio = f"{big_count}:{small_count}"
        
        # 评价大小比
        if big_count == 3:
            big_small_rating = "标准大小比（3:3），平衡性好"
            big_small_icon = "✅"
        elif 2 <= big_count <= 4:
            big_small_rating = "大小比合理，常见模式"
            big_small_icon = "✓"
        else:
            big_small_rating = "大小比极端，出现概率较低"
            big_small_icon = "⚠️"
        
        # 3. 区间分布（1-11, 12-22, 23-33）
        zone1 = sum(1 for n in red_numbers if 1 <= n <= 11)
        zone2 = sum(1 for n in red_numbers if 12 <= n <= 22)
        zone3 = sum(1 for n in red_numbers if 23 <= n <= 33)
        zone_distribution = f"{zone1}-{zone2}-{zone3}"
        
        # 评价区间分布
        if all(z >= 1 for z in [zone1, zone2, zone3]):
            zone_rating = "三区都有号码，分布均衡"
            zone_icon = "✅"
        elif sum(1 for z in [zone1, zone2, zone3] if z > 0) >= 2:
            zone_rating = "覆盖两个区间，分布合理"
            zone_icon = "✓"
        else:
            zone_rating = "号码集中在一个区间，分布不均"
            zone_icon = "⚠️"
        
        # 4. 连号检测
        consecutive = []
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i+1] - sorted_nums[i] == 1:
                consecutive.append((sorted_nums[i], sorted_nums[i+1]))
        
        # 评价连号
        if len(consecutive) == 0:
            consecutive_rating = "无连号，独特性较高"
            consecutive_icon = "✓"
        elif len(consecutive) == 1:
            consecutive_rating = "有连号，符合常见模式"
            consecutive_icon = "✓"
        else:
            consecutive_rating = "连号较多，可能降低独特性"
            consecutive_icon = "⚠️"
        
        # 5. 和值
        sum_value = sum(red_numbers)
        
        # 评价和值
        if 90 <= sum_value <= 130:
            sum_rating = "和值在常见范围内（90-130）"
            sum_icon = "✅"
        elif 70 <= sum_value <= 150:
            sum_rating = "和值合理（70-150）"
            sum_icon = "✓"
        else:
            sum_rating = "和值偏离常见范围"
            sum_icon = "⚠️"
        
        # 6. 跨度（最大号-最小号）
        span = max(red_numbers) - min(red_numbers)
        
        # 评价跨度
        if 15 <= span <= 28:
            span_rating = "跨度在常见范围内（15-28）"
            span_icon = "✅"
        elif 10 <= span <= 32:
            span_rating = "跨度合理（10-32）"
            span_icon = "✓"
        else:
            span_rating = "跨度偏离常见范围"
            span_icon = "⚠️"
        
        # 7. AC值（号码复杂度）
        ac_value = self._calculate_ac_value(sorted_nums)
        
        # 评价AC值
        if ac_value >= 6:
            ac_rating = "AC值较高，号码复杂度好"
            ac_icon = "✅"
        elif ac_value >= 4:
            ac_rating = "AC值中等，复杂度合理"
            ac_icon = "✓"
        else:
            ac_rating = "AC值较低，号码可能过于规律"
            ac_icon = "⚠️"
        
        return {
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
        }
    
    def _calculate_ac_value(self, numbers: List[int]) -> int:
        """计算AC值（号码复杂度）
        
        Args:
            numbers: 排序后的号码列表
            
        Returns:
            AC值
        """
        differences = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                differences.add(abs(numbers[i] - numbers[j]))
        return len(differences) - (len(numbers) - 1)
    
    def _check_historical(self, red_numbers: List[int], blue_number: int, 
                         history_data: List[Dict]) -> Dict:
        """历史对比
        
        Args:
            red_numbers: 红球号码列表
            blue_number: 蓝球号码
            history_data: 历史数据
            
        Returns:
            历史对比结果
        """
        red_set = set(red_numbers)
        
        exact_match = False
        exact_match_period = None
        red_match_counts = []
        blue_match_count = 0
        max_match_period = None
        max_match_count = 0
        
        for draw in history_data:
            draw_red_set = set(draw['red_numbers'])
            draw_blue = draw['blue_number']
            
            # 检查完全匹配
            if draw_red_set == red_set and draw_blue == blue_number:
                exact_match = True
                exact_match_period = draw['draw_num']
                break
            
            # 统计红球匹配数
            match_count = len(red_set & draw_red_set)
            red_match_counts.append(match_count)
            
            # 记录最大匹配
            if match_count > max_match_count:
                max_match_count = match_count
                max_match_period = draw['draw_num']
            
            # 统计蓝球匹配
            if draw_blue == blue_number:
                blue_match_count += 1
        
        # 评价
        if exact_match:
            rating = "警告：这注号码在历史上完全出现过"
            icon = "⚠️"
        elif max_match_count >= 5:
            rating = "与历史号码相似度较高，独特性不足"
            icon = "⚠️"
        elif max_match_count >= 4:
            rating = "与历史号码有一定相似度"
            icon = "✓"
        else:
            rating = "独特性较好，与历史号码差异明显"
            icon = "✅"
        
        return {
            'exact_match': exact_match,
            'exact_match_period': exact_match_period,
            'max_red_match': max_match_count,
            'max_match_period': max_match_period,
            'avg_red_match': round(np.mean(red_match_counts), 2) if red_match_counts else 0,
            'blue_appearance': blue_match_count,
            'rating': rating,
            'icon': icon
        }
    
    def _calculate_scores(self, freq_result: Dict, missing_result: Dict, 
                         pattern_result: Dict, historical_result: Dict) -> Dict:
        """计算各维度得分
        
        Args:
            freq_result: 频率分析结果
            missing_result: 遗漏分析结果
            pattern_result: 模式分析结果
            historical_result: 历史对比结果
            
        Returns:
            得分字典
        """
        # 1. 频率得分（0-100）
        red_freqs = [detail['frequency'] for detail in freq_result['red_details']]
        avg_red_freq = np.mean(red_freqs)
        freq_score = min(100, (avg_red_freq / freq_result['red_theory']) * 50 + 50)
        
        # 2. 遗漏得分（0-100）
        red_missings = [detail['missing'] for detail in missing_result['red_details']]
        avg_red_missing = np.mean(red_missings)
        missing_score = max(0, min(100, 100 - avg_red_missing * 2))
        
        # 3. 模式得分（0-100）
        pattern_score = 0
        
        # 奇偶比（20分）
        if pattern_result['odd_even']['icon'] == '✅':
            pattern_score += 20
        elif pattern_result['odd_even']['icon'] == '✓':
            pattern_score += 15
        
        # 大小比（20分）
        if pattern_result['big_small']['icon'] == '✅':
            pattern_score += 20
        elif pattern_result['big_small']['icon'] == '✓':
            pattern_score += 15
        
        # 区间分布（20分）
        if pattern_result['zone']['icon'] == '✅':
            pattern_score += 20
        elif pattern_result['zone']['icon'] == '✓':
            pattern_score += 15
        
        # 和值（20分）
        if pattern_result['sum']['icon'] == '✅':
            pattern_score += 20
        elif pattern_result['sum']['icon'] == '✓':
            pattern_score += 15
        
        # AC值（20分）
        if pattern_result['ac_value']['icon'] == '✅':
            pattern_score += 20
        elif pattern_result['ac_value']['icon'] == '✓':
            pattern_score += 15
        
        # 4. 独特性得分（0-100）
        uniqueness_score = max(0, 100 - historical_result['max_red_match'] * 10)
        
        # 5. 综合得分
        return self.calculate_composite_score(freq_score, missing_score, pattern_score, uniqueness_score)
    
    def _generate_suggestions(self, freq_result: Dict, missing_result: Dict, 
                             pattern_result: Dict, historical_result: Dict) -> List[str]:
        """生成专家建议
        
        Args:
            freq_result: 频率分析结果
            missing_result: 遗漏分析结果
            pattern_result: 模式分析结果
            historical_result: 历史对比结果
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 频率建议
        red_freqs = [detail['frequency'] for detail in freq_result['red_details']]
        avg_red_freq = np.mean(red_freqs)
        
        if avg_red_freq < freq_result['red_theory'] * 0.7:
            suggestions.append("红球整体偏冷，可能需要较长时间才会出现")
        elif avg_red_freq > freq_result['red_theory'] * 1.3:
            suggestions.append("红球整体偏热，短期内可能继续活跃")
        
        # 遗漏建议
        red_missings = [detail['missing'] for detail in missing_result['red_details']]
        avg_red_missing = np.mean(red_missings)
        
        if avg_red_missing > 20:
            suggestions.append("部分红球遗漏较长，可能即将回补")
        
        # 模式建议
        if pattern_result['consecutive']['count'] >= 2:
            suggestions.append("连号较多，可能降低独特性，中奖时分奖风险较高")
        
        if pattern_result['sum']['icon'] == '⚠️':
            suggestions.append("和值偏离常见范围，出现概率相对较低")
        
        if pattern_result['ac_value']['icon'] == '⚠️':
            suggestions.append("AC值较低，号码可能过于规律，建议增加复杂度")
        
        # 历史建议
        if historical_result['exact_match']:
            suggestions.append("警告：这注号码在历史上完全出现过，虽然理论上可能再次出现，但概率极低")
        elif historical_result['max_red_match'] >= 5:
            suggestions.append("与历史号码相似度较高，独特性不足")
        
        # 如果没有建议，给出正面评价
        if not suggestions:
            suggestions.append("这是一注平衡性和独特性都不错的号码")
            suggestions.append("从统计角度看，各项指标都在合理范围内")
        
        return suggestions

