#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础号码评价器
提供通用的评价方法和接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import json


class BaseNumberEvaluator(ABC):
    """基础号码评价器抽象类"""
    
    def __init__(self, history_file: str):
        """初始化评价器
        
        Args:
            history_file: 历史数据文件路径
        """
        self.history_file = history_file
        self.history_data = None
        self._cache = {}
    
    def load_history(self) -> List[Dict]:
        """加载历史数据
        
        Returns:
            历史数据列表
        """
        if self.history_data is None:
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.history_data = data.get('data', [])
            except FileNotFoundError:
                raise FileNotFoundError(f"历史数据文件不存在: {self.history_file}")
            except json.JSONDecodeError:
                raise ValueError(f"历史数据文件格式错误: {self.history_file}")
        
        return self.history_data
    
    @abstractmethod
    def evaluate(self, *args, **kwargs) -> Dict[str, Any]:
        """评价号码（子类必须实现）
        
        Returns:
            评价结果字典，包含：
            - frequency: 频率分析结果
            - missing: 遗漏分析结果
            - pattern: 模式分析结果
            - historical: 历史对比结果
            - scores: 各维度得分
            - total_score: 综合得分
            - rating: 评级
            - suggestions: 建议列表
        """
        pass
    
    def calculate_composite_score(self, freq_score: float, missing_score: float, 
                                  pattern_score: float, uniqueness_score: float) -> Dict[str, Any]:
        """计算综合得分
        
        Args:
            freq_score: 频率得分 (0-100)
            missing_score: 遗漏得分 (0-100)
            pattern_score: 模式得分 (0-100)
            uniqueness_score: 独特性得分 (0-100)
            
        Returns:
            包含各维度得分、总分和评级的字典
        """
        # 权重配置
        weights = {
            'frequency': 0.25,    # 频率权重 25%
            'missing': 0.25,      # 遗漏权重 25%
            'pattern': 0.30,      # 模式权重 30%
            'uniqueness': 0.20    # 独特性权重 20%
        }
        
        # 计算加权总分
        total_score = (
            freq_score * weights['frequency'] +
            missing_score * weights['missing'] +
            pattern_score * weights['pattern'] +
            uniqueness_score * weights['uniqueness']
        )
        
        # 确定评级
        if total_score >= 90:
            rating = '优秀'
            stars = '⭐⭐⭐⭐⭐'
        elif total_score >= 80:
            rating = '良好'
            stars = '⭐⭐⭐⭐'
        elif total_score >= 70:
            rating = '中等'
            stars = '⭐⭐⭐'
        elif total_score >= 60:
            rating = '一般'
            stars = '⭐⭐'
        else:
            rating = '较差'
            stars = '⭐'
        
        return {
            'frequency': round(freq_score, 1),
            'missing': round(missing_score, 1),
            'pattern': round(pattern_score, 1),
            'uniqueness': round(uniqueness_score, 1),
            'total': round(total_score, 1),
            'rating': rating,
            'stars': stars
        }
    
    def get_rating_icon(self, score: float) -> str:
        """根据得分获取评级图标
        
        Args:
            score: 得分 (0-100)
            
        Returns:
            评级图标
        """
        if score >= 90:
            return '✅'
        elif score >= 80:
            return '✅'
        elif score >= 70:
            return '✓'
        elif score >= 60:
            return '⚠️'
        else:
            return '❌'
    
    def classify_number_by_frequency(self, count: int, theoretical: float) -> tuple:
        """根据频率分类号码
        
        Args:
            count: 实际出现次数
            theoretical: 理论出现次数
            
        Returns:
            (分类名称, 图标)
        """
        ratio = count / theoretical if theoretical > 0 else 0
        
        if ratio >= 1.15:
            return '热门', '🔥'
        elif ratio >= 0.85:
            return '温号', '🟡'
        else:
            return '冷号', '🧊'
    
    def classify_missing_period(self, missing: int, avg_missing: float) -> tuple:
        """根据遗漏期数分类
        
        Args:
            missing: 当前遗漏期数
            avg_missing: 平均遗漏期数
            
        Returns:
            (分类名称, 图标)
        """
        if missing == 0:
            return '刚出现', '⭐'
        elif missing <= avg_missing * 0.5:
            return '短期遗漏', '✅'
        elif missing <= avg_missing * 1.5:
            return '中期遗漏', '⚠️'
        else:
            return '长期遗漏', '❌'
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_cache_key(self, *args) -> str:
        """生成缓存键
        
        Args:
            *args: 用于生成键的参数
            
        Returns:
            缓存键字符串
        """
        return '_'.join(str(arg) for arg in args)

