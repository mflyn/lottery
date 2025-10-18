#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
序列分析工具
用于检测号码序列中的各种模式
"""

from typing import List, Tuple
from itertools import combinations


class SequenceAnalyzer:
    """序列分析工具类"""
    
    @staticmethod
    def max_consecutive_run(nums: List[int]) -> int:
        """
        计算最大连号长度
        
        Args:
            nums: 已排序的号码列表
            
        Returns:
            最大连续号码的长度
            
        Examples:
            >>> SequenceAnalyzer.max_consecutive_run([1, 2, 3, 5, 7])
            3
            >>> SequenceAnalyzer.max_consecutive_run([1, 3, 5, 7])
            1
        """
        if not nums:
            return 0
        
        run, best = 1, 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                run += 1
                best = max(best, run)
            else:
                run = 1
        return best
    
    @staticmethod
    def is_arithmetic_progression(seq: List[int]) -> bool:
        """
        判断序列是否为等差数列
        
        Args:
            seq: 已排序的号码列表
            
        Returns:
            是否为等差数列
            
        Examples:
            >>> SequenceAnalyzer.is_arithmetic_progression([2, 4, 6, 8])
            True
            >>> SequenceAnalyzer.is_arithmetic_progression([1, 2, 4, 8])
            False
        """
        if len(seq) <= 2:
            return True
        
        d = seq[1] - seq[0]
        for i in range(2, len(seq)):
            if seq[i] - seq[i-1] != d:
                return False
        return True
    
    @staticmethod
    def has_ap_k_of_m(seq: List[int], k: int) -> bool:
        """
        检查是否存在长度>=k的等差子序列
        
        Args:
            seq: 已排序的号码列表
            k: 子序列最小长度
            
        Returns:
            是否存在满足条件的等差子序列
            
        Examples:
            >>> SequenceAnalyzer.has_ap_k_of_m([1, 2, 3, 7, 9], 3)
            True  # [1, 2, 3]
        """
        if len(seq) < k:
            return False
        
        for comb in combinations(seq, k):
            s = sorted(comb)
            if SequenceAnalyzer.is_arithmetic_progression(s):
                return True
        return False
    
    @staticmethod
    def zone_distribution(nums: List[int], zones: int, max_num: int) -> List[int]:
        """
        计算号码在各区间的分布
        
        Args:
            nums: 号码列表
            zones: 区间数量
            max_num: 最大号码值
            
        Returns:
            各区间的号码数量列表
            
        Examples:
            >>> SequenceAnalyzer.zone_distribution([1, 5, 12, 20, 25, 30], 3, 33)
            [2, 2, 2]  # SSQ三区分布：1-11, 12-22, 23-33
        """
        zone_size = max_num // zones
        distribution = [0] * zones
        
        for num in nums:
            zone_idx = min((num - 1) // zone_size, zones - 1)
            distribution[zone_idx] += 1
        
        return distribution
    
    @staticmethod
    def overlap_count(a: List[int], b: List[int]) -> int:
        """
        计算两组号码的重叠数量
        
        Args:
            a: 第一组号码
            b: 第二组号码
            
        Returns:
            重叠的号码数量
            
        Examples:
            >>> SequenceAnalyzer.overlap_count([1, 2, 3], [2, 3, 4])
            2
        """
        return len(set(a) & set(b))
    
    @staticmethod
    def last_digit_distribution(nums: List[int]) -> dict:
        """
        统计尾数分布
        
        Args:
            nums: 号码列表
            
        Returns:
            尾数分布字典 {尾数: 出现次数}
            
        Examples:
            >>> SequenceAnalyzer.last_digit_distribution([11, 21, 13, 23])
            {1: 2, 3: 2}
        """
        from collections import Counter
        return Counter(x % 10 for x in nums)
    
    @staticmethod
    def count_multiples(nums: List[int], divisor: int) -> int:
        """
        统计某个数的倍数数量
        
        Args:
            nums: 号码列表
            divisor: 除数
            
        Returns:
            倍数的数量
            
        Examples:
            >>> SequenceAnalyzer.count_multiples([5, 10, 15, 17, 20], 5)
            4
        """
        return sum(1 for x in nums if x % divisor == 0)
    
    @staticmethod
    def count_odd_even(nums: List[int]) -> Tuple[int, int]:
        """
        统计奇偶数数量
        
        Args:
            nums: 号码列表
            
        Returns:
            (奇数数量, 偶数数量)
            
        Examples:
            >>> SequenceAnalyzer.count_odd_even([1, 2, 3, 4, 5])
            (3, 2)
        """
        odd = sum(1 for x in nums if x % 2 == 1)
        even = len(nums) - odd
        return odd, even
    
    @staticmethod
    def count_birthday_like(nums: List[int], threshold: int = 31) -> int:
        """
        统计生日化号码数量（<=31的号码）
        
        Args:
            nums: 号码列表
            threshold: 生日化阈值，默认31
            
        Returns:
            生日化号码数量
            
        Examples:
            >>> SequenceAnalyzer.count_birthday_like([5, 12, 25, 32, 33])
            3
        """
        return sum(1 for x in nums if x <= threshold)
    
    @staticmethod
    def is_consecutive_pair(a: int, b: int) -> bool:
        """
        判断两个号码是否连续
        
        Args:
            a: 第一个号码
            b: 第二个号码
            
        Returns:
            是否连续
            
        Examples:
            >>> SequenceAnalyzer.is_consecutive_pair(5, 6)
            True
            >>> SequenceAnalyzer.is_consecutive_pair(5, 7)
            False
        """
        return abs(a - b) == 1

