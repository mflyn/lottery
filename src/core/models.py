#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票数据模型
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class LotteryNumber:
    """彩票号码基础类"""
    lottery_type: str  # 'dlt' 或 'ssq'
    numbers: List[int] = field(default_factory=list)
    score: float = 0.0

    def __post_init__(self):
        """初始化后处理"""
        # 基本验证
        if not self.validate():
            raise ValueError(f"号码不合法: {self.numbers}")

    def validate(self) -> bool:
        """验证号码（子类应重写此方法）"""
        return True

@dataclass
class DLTNumber:
    """大乐透号码（优化版）"""
    front: List[int]
    back: List[int]
    score: float = 0.0

    def __post_init__(self):
        """初始化后处理"""
        # 先验证，再排序
        # 这样可以在输入无效时立即抛出异常
        if not self._validate_before_sort():
            raise ValueError(
                f"大乐透号码不合法: 前区={self.front}, 后区={self.back}"
            )

        # 排序
        self.front = sorted(self.front)
        self.back = sorted(self.back)

    def _validate_before_sort(self) -> bool:
        """排序前验证（检查基本规则）"""
        # 验证前区
        if not isinstance(self.front, (list, tuple)) or len(self.front) != 5:
            return False
        if not all(isinstance(n, int) and 1 <= n <= 35 for n in self.front):
            return False
        if len(set(self.front)) != 5:  # 检查重复
            return False

        # 验证后区
        if not isinstance(self.back, (list, tuple)) or len(self.back) != 2:
            return False
        if not all(isinstance(n, int) and 1 <= n <= 12 for n in self.back):
            return False
        if len(set(self.back)) != 2:  # 检查重复
            return False

        return True

    def validate(self) -> bool:
        """验证号码（排序后）"""
        return self._validate_before_sort()

    @property
    def numbers(self) -> List[int]:
        """获取所有号码"""
        return self.front + self.back

    @property
    def lottery_type(self) -> str:
        """获取彩票类型"""
        return 'dlt'

@dataclass
class SSQNumber:
    """双色球号码（优化版）"""
    red: List[int]
    blue: int
    score: float = 0.0

    def __post_init__(self):
        """初始化后处理"""
        # 先验证，再排序
        # 这样可以在输入无效时立即抛出异常
        if not self._validate_before_sort():
            raise ValueError(
                f"双色球号码不合法: 红球={self.red}, 蓝球={self.blue}"
            )

        # 排序
        self.red = sorted(self.red)

    def _validate_before_sort(self) -> bool:
        """排序前验证（检查基本规则）"""
        # 验证红球
        if not isinstance(self.red, (list, tuple)) or len(self.red) != 6:
            return False
        if not all(isinstance(n, int) and 1 <= n <= 33 for n in self.red):
            return False
        if len(set(self.red)) != 6:  # 检查重复
            return False

        # 验证蓝球
        if not isinstance(self.blue, int) or not 1 <= self.blue <= 16:
            return False

        return True

    def validate(self) -> bool:
        """验证号码（排序后）"""
        return self._validate_before_sort()

    @property
    def numbers(self) -> List[int]:
        """获取所有号码"""
        return self.red + [self.blue]

    @property
    def lottery_type(self) -> str:
        """获取彩票类型"""
        return 'ssq'
