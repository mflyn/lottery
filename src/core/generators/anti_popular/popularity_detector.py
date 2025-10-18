#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门模式检测器
检测号码组合中的热门选号模式，分数越高表示越"大众化"
"""

from typing import List, Tuple, Dict
from .sequence_analyzer import SequenceAnalyzer


class PopularityDetector:
    """热门模式检测器"""
    
    @staticmethod
    def calculate_ssq_score(red: List[int], blue: int, sum_bounds: Tuple[int, int]) -> int:
        """
        计算双色球号码的热门度分数
        
        分数越高表示越符合大众选号习惯，越容易撞号
        
        Args:
            red: 红球号码列表（已排序）
            blue: 蓝球号码
            sum_bounds: 和值范围 (下界, 上界)
            
        Returns:
            热门度分数（0-20分）
            
        评分规则：
            1. 连号偏好：5连+5分，4连+3分，3连+1分
            2. 等差偏好：全等差+5分，5个等差+3分，4个等差+1分
            3. 生日化：全部≤31 +3分，5个≤31 +2分
            4. 同尾数：4个同尾+3分，3个同尾+2分
            5. 整齐倍数：4个5倍数+3分，3个5倍数+1分
            6. 奇偶极端：全奇或全偶+1分
            7. 和值偏离：超出范围+1分
            8. 区间集中：全在一区+3分，5个在一区+1分
            9. 蓝球热门：7-10号+1分
        """
        score = 0
        
        # 1) 连号偏好
        run = SequenceAnalyzer.max_consecutive_run(red)
        if run >= 5:
            score += 5
        elif run == 4:
            score += 3
        elif run == 3:
            score += 1
        
        # 2) 等差偏好
        if SequenceAnalyzer.is_arithmetic_progression(red):
            score += 5
        elif SequenceAnalyzer.has_ap_k_of_m(red, 5):
            score += 3
        elif SequenceAnalyzer.has_ap_k_of_m(red, 4):
            score += 1
        
        # 3) 生日化（≤31 过多）
        birth_like = SequenceAnalyzer.count_birthday_like(red, 31)
        if birth_like == 6:
            score += 3
        elif birth_like >= 5:
            score += 2
        
        # 4) 同尾数过多
        ld_dist = SequenceAnalyzer.last_digit_distribution(red)
        max_same_digit = max(ld_dist.values()) if ld_dist else 0
        if max_same_digit >= 4:
            score += 3
        elif max_same_digit == 3:
            score += 2
        
        # 5) 整齐倍数（5的倍数过多）
        mult5 = SequenceAnalyzer.count_multiples(red, 5)
        if mult5 >= 4:
            score += 3
        elif mult5 == 3:
            score += 1
        
        # 6) 奇偶极端
        odd, even = SequenceAnalyzer.count_odd_even(red)
        if odd in (0, 6):
            score += 1
        
        # 7) 和值偏离
        rsum = sum(red)
        lo, hi = sum_bounds
        if rsum < lo or rsum > hi:
            score += 1
        
        # 8) 区间过度集中（三区：1-11, 12-22, 23-33）
        zone_dist = SequenceAnalyzer.zone_distribution(red, 3, 33)
        max_zone = max(zone_dist)
        if max_zone == 6:
            score += 3
        elif max_zone >= 5:
            score += 1
        
        # 9) 蓝球"撞大众"（7-10是常见选择）
        if 7 <= blue <= 10:
            score += 1
        
        return score
    
    @staticmethod
    def calculate_dlt_score(front: List[int], back: List[int]) -> int:
        """
        计算大乐透号码的热门度分数
        
        Args:
            front: 前区号码列表（已排序）
            back: 后区号码列表（已排序）
            
        Returns:
            热门度分数（0-20分）
            
        评分规则：
            1. 前区连号：4连+4分，3连+2分
            2. 等差结构：全等差+4分，4个等差+2分
            3. 生日化：全部≤31 +4分，4个≤31 +2分
            4. 尾数集中：3个同尾+2分
            5. 0/5尾数：3个以上+2分
            6. 奇偶极端：全奇或全偶+1分
            7. 和值极端：<60或>120 +1分
            8. 后区连号：+1分
        """
        score = 0
        
        # 1) 前区连号过多
        max_run = SequenceAnalyzer.max_consecutive_run(front)
        if max_run >= 4:
            score += 4
        elif max_run == 3:
            score += 2
        
        # 2) 等差结构
        if SequenceAnalyzer.is_arithmetic_progression(front):
            score += 4
        elif SequenceAnalyzer.has_ap_k_of_m(front, 4):
            score += 2
        
        # 3) 生日化
        birthday_like = SequenceAnalyzer.count_birthday_like(front, 31)
        if birthday_like == 5:
            score += 4
        elif birthday_like >= 4:
            score += 2
        
        # 4) 尾数过于集中
        ld_dist = SequenceAnalyzer.last_digit_distribution(front)
        max_same_digit = max(ld_dist.values()) if ld_dist else 0
        if max_same_digit >= 3:
            score += 2
        
        # 5) 0/5 尾数过多
        zero_five = SequenceAnalyzer.count_multiples(front, 5)
        if zero_five >= 3:
            score += 2
        
        # 6) 奇偶极端
        odd, even = SequenceAnalyzer.count_odd_even(front)
        if odd in (0, 5):
            score += 1
        
        # 7) 和值太极端
        s = sum(front)
        if s < 60 or s > 120:
            score += 1
        
        # 8) 后区连号
        if len(back) == 2 and SequenceAnalyzer.is_consecutive_pair(back[0], back[1]):
            score += 1
        
        return score
    
    @staticmethod
    def check_hard_reject_ssq(red: List[int], blue: int, config: Dict) -> bool:
        """
        双色球硬性规则检查（直接拒绝）
        
        Args:
            red: 红球号码列表
            blue: 蓝球号码
            config: 配置字典
            
        Returns:
            True表示应该拒绝，False表示通过检查
        """
        # 连号长度限制
        max_run_allowed = config.get('max_run', 2)
        if SequenceAnalyzer.max_consecutive_run(red) > max_run_allowed:
            return True
        
        # 同尾限制
        max_same_last_digit = config.get('max_same_last_digit', 2)
        ld_dist = SequenceAnalyzer.last_digit_distribution(red)
        if any(c > max_same_last_digit for c in ld_dist.values()):
            return True
        
        # 奇偶限制
        odd_bounds = config.get('odd_bounds', (2, 4))
        odd, _ = SequenceAnalyzer.count_odd_even(red)
        if not (odd_bounds[0] <= odd <= odd_bounds[1]):
            return True
        
        # 和值限制
        sum_bounds = config.get('sum_bounds', (70, 140))
        rsum = sum(red)
        if not (sum_bounds[0] <= rsum <= sum_bounds[1]):
            return True
        
        return False
    
    @staticmethod
    def check_hard_reject_dlt(front: List[int], back: List[int], config: Dict) -> bool:
        """
        大乐透硬性规则检查（直接拒绝）
        
        Args:
            front: 前区号码列表
            back: 后区号码列表
            config: 配置字典
            
        Returns:
            True表示应该拒绝，False表示通过检查
        """
        # 连号长度限制
        max_run_allowed = config.get('max_run', 2)
        if SequenceAnalyzer.max_consecutive_run(front) > max_run_allowed:
            return True
        
        # 尾数集中限制
        max_same_last_digit = config.get('max_same_last_digit', 2)
        ld_dist = SequenceAnalyzer.last_digit_distribution(front)
        if any(c > max_same_last_digit for c in ld_dist.values()):
            return True
        
        # 奇偶限制
        odd_bounds = config.get('odd_bounds', (1, 4))
        odd, _ = SequenceAnalyzer.count_odd_even(front)
        if odd < odd_bounds[0] or odd > odd_bounds[1]:
            return True
        
        # 和值限制
        sum_bounds = config.get('sum_bounds', (60, 120))
        s = sum(front)
        if s < sum_bounds[0] or s > sum_bounds[1]:
            return True
        
        # 后区是否拒绝连续
        avoid_back_consecutive = config.get('avoid_back_consecutive', False)
        if avoid_back_consecutive and len(back) == 2:
            if SequenceAnalyzer.is_consecutive_pair(back[0], back[1]):
                return True
        
        return False

