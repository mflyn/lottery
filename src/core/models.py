#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票数据模型
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LotteryNumber:
    """彩票号码基础类"""
    lottery_type: str  # 'dlt' 或 'ssq'
    numbers: List[int]
    score: float = 0.0
    
@dataclass
class DLTNumber(LotteryNumber):
    """大乐透号码"""
    def __init__(self, front: List[int], back: List[int], score: float = 0.0):
        super().__init__(
            lottery_type='dlt',
            numbers=front + back,
            score=score
        )
        self.front = sorted(front)
        self.back = sorted(back)

@dataclass
class SSQNumber(LotteryNumber):
    """双色球号码"""
    def __init__(self, red: List[int], blue: int, score: float = 0.0):
        super().__init__(
            lottery_type='ssq',
            numbers=red + [blue],
            score=score
        )
        self.red = sorted(red)
        self.blue = blue
