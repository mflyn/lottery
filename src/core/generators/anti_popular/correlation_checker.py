#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相关性检查器
用于检查多注号码之间的相关性，避免号码过度重叠
"""

from typing import List, Dict, Tuple
from collections import Counter
from .sequence_analyzer import SequenceAnalyzer


class CorrelationChecker:
    """号码相关性检查器"""
    
    @staticmethod
    def check_ssq_correlation(
        new_red: List[int],
        new_blue: int,
        existing_picks: List[Tuple],
        config: Dict
    ) -> bool:
        """
        检查SSQ号码与已有号码的相关性
        
        Args:
            new_red: 新的红球号码列表
            new_blue: 新的蓝球号码
            existing_picks: 已有的号码列表 [(red, blue, score), ...]
            config: 配置字典
            
        Returns:
            True表示通过检查（相关性低），False表示相关性过高应拒绝
        """
        if not existing_picks:
            return True
        
        max_red_overlap = config.get('max_red_overlap', 2)
        
        # 检查红球重叠
        for pick in existing_picks:
            existing_red = pick[0]
            overlap = SequenceAnalyzer.overlap_count(new_red, existing_red)
            if overlap > max_red_overlap:
                return False
        
        return True
    
    @staticmethod
    def check_blue_usage(
        new_blue: int,
        blue_usage: Counter,
        config: Dict
    ) -> bool:
        """
        检查蓝球使用次数
        
        Args:
            new_blue: 新的蓝球号码
            blue_usage: 蓝球使用计数器
            config: 配置字典
            
        Returns:
            True表示可以使用，False表示已达到使用上限
        """
        max_blue_dup = config.get('max_blue_dup', 1)
        return blue_usage[new_blue] < max_blue_dup
    
    @staticmethod
    def check_dlt_correlation(
        new_front: List[int],
        new_back: List[int],
        existing_picks: List[Tuple],
        config: Dict
    ) -> bool:
        """
        检查DLT号码与已有号码的相关性
        
        Args:
            new_front: 新的前区号码列表
            new_back: 新的后区号码列表
            existing_picks: 已有的号码列表 [(front, back, score), ...]
            config: 配置字典
            
        Returns:
            True表示通过检查（相关性低），False表示相关性过高应拒绝
        """
        if not existing_picks:
            return True
        
        max_front_overlap = config.get('max_front_overlap', 2)
        max_back_overlap = config.get('max_back_overlap', 1)
        
        # 检查前区和后区重叠
        for pick in existing_picks:
            existing_front = pick[0]
            existing_back = pick[1]
            
            # 前区重叠检查
            front_overlap = SequenceAnalyzer.overlap_count(new_front, existing_front)
            if front_overlap > max_front_overlap:
                return False
            
            # 后区重叠检查
            back_overlap = SequenceAnalyzer.overlap_count(new_back, existing_back)
            if back_overlap > max_back_overlap:
                return False
        
        return True
    
    @staticmethod
    def calculate_diversity_score(picks: List[Tuple], lottery_type: str = 'ssq') -> float:
        """
        计算一组号码的多样性分数
        
        Args:
            picks: 号码列表
            lottery_type: 彩票类型
            
        Returns:
            多样性分数（0-1，越高越多样）
        """
        if not picks or len(picks) < 2:
            return 1.0
        
        total_overlap = 0
        comparison_count = 0
        
        if lottery_type == 'ssq':
            # 计算所有号码对之间的平均重叠度
            for i in range(len(picks)):
                for j in range(i + 1, len(picks)):
                    red1, blue1, _ = picks[i]
                    red2, blue2, _ = picks[j]
                    
                    # 红球重叠度（0-1）
                    red_overlap = SequenceAnalyzer.overlap_count(red1, red2) / 6.0
                    total_overlap += red_overlap
                    
                    # 蓝球相同加权
                    if blue1 == blue2:
                        total_overlap += 0.5
                    
                    comparison_count += 1
        
        elif lottery_type == 'dlt':
            for i in range(len(picks)):
                for j in range(i + 1, len(picks)):
                    front1, back1, _ = picks[i]
                    front2, back2, _ = picks[j]
                    
                    # 前区重叠度
                    front_overlap = SequenceAnalyzer.overlap_count(front1, front2) / 5.0
                    total_overlap += front_overlap
                    
                    # 后区重叠度
                    back_overlap = SequenceAnalyzer.overlap_count(back1, back2) / 2.0
                    total_overlap += back_overlap * 0.5
                    
                    comparison_count += 1
        
        if comparison_count == 0:
            return 1.0
        
        avg_overlap = total_overlap / comparison_count
        diversity = 1.0 - avg_overlap
        
        return max(0.0, min(1.0, diversity))
    
    @staticmethod
    def get_correlation_report(picks: List[Tuple], lottery_type: str = 'ssq') -> Dict:
        """
        生成相关性分析报告
        
        Args:
            picks: 号码列表
            lottery_type: 彩票类型
            
        Returns:
            相关性分析报告字典
        """
        report = {
            'total_picks': len(picks),
            'diversity_score': CorrelationChecker.calculate_diversity_score(picks, lottery_type),
            'overlap_details': []
        }
        
        if lottery_type == 'ssq':
            # 统计蓝球使用情况
            blue_usage = Counter(pick[1] for pick in picks)
            report['blue_usage'] = dict(blue_usage)
            report['unique_blues'] = len(blue_usage)
            
            # 统计红球重叠情况
            overlaps = []
            for i in range(len(picks)):
                for j in range(i + 1, len(picks)):
                    overlap = SequenceAnalyzer.overlap_count(picks[i][0], picks[j][0])
                    overlaps.append(overlap)
            
            if overlaps:
                report['avg_red_overlap'] = sum(overlaps) / len(overlaps)
                report['max_red_overlap'] = max(overlaps)
                report['min_red_overlap'] = min(overlaps)
        
        elif lottery_type == 'dlt':
            # 统计前区和后区重叠情况
            front_overlaps = []
            back_overlaps = []
            
            for i in range(len(picks)):
                for j in range(i + 1, len(picks)):
                    front_overlap = SequenceAnalyzer.overlap_count(picks[i][0], picks[j][0])
                    back_overlap = SequenceAnalyzer.overlap_count(picks[i][1], picks[j][1])
                    front_overlaps.append(front_overlap)
                    back_overlaps.append(back_overlap)
            
            if front_overlaps:
                report['avg_front_overlap'] = sum(front_overlaps) / len(front_overlaps)
                report['max_front_overlap'] = max(front_overlaps)
            
            if back_overlaps:
                report['avg_back_overlap'] = sum(back_overlaps) / len(back_overlaps)
                report['max_back_overlap'] = max(back_overlaps)
        
        return report

