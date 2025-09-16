#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票计算器
"""

from abc import ABC, abstractmethod
from typing import Dict
import itertools
from .models import DLTNumber, SSQNumber

class LotteryCalculator(ABC):
    """彩票计算器基类"""
    
    @abstractmethod
    def calculate_complex_bet(self, numbers: any) -> Dict:
        """计算复式投注注数和金额"""
        pass
    
    @abstractmethod
    def calculate_dantuo_bet(self, dan: any, tuo: any) -> Dict:
        """计算胆拖投注注数和金额"""
        pass

class DLTCalculator(LotteryCalculator):
    """大乐透计算器"""
    
    def calculate_complex_bet(self, numbers: DLTNumber) -> Dict:
        """计算复式投注注数和金额"""
        if not numbers.validate():
            raise ValueError("号码不合法")
            
        front_count = len(numbers.front)
        back_count = len(numbers.back)
        
        # 计算注数
        front_combinations = len(list(itertools.combinations(numbers.front, 5)))
        back_combinations = len(list(itertools.combinations(numbers.back, 2)))
        total_bets = front_combinations * back_combinations
        
        return {
            'bets': total_bets,
            'amount': total_bets * 2,  # 每注2元
            'front_count': front_count,
            'back_count': back_count
        }
    
    def calculate_dantuo_bet(self, dan: DLTNumber, tuo: DLTNumber) -> Dict:
        """计算胆拖投注注数和金额"""
        # 验证胆码数量
        if len(dan.front) >= 5 or len(dan.back) >= 2:
            raise ValueError("胆码数量超出限制")
            
        # 计算注数
        front_combinations = len(list(itertools.combinations(tuo.front, 5 - len(dan.front))))
        back_combinations = len(list(itertools.combinations(tuo.back, 2 - len(dan.back))))
        total_bets = front_combinations * back_combinations
        
        return {
            'bets': total_bets,
            'amount': total_bets * 2,
            'front_dan_count': len(dan.front),
            'front_tuo_count': len(tuo.front),
            'back_dan_count': len(dan.back),
            'back_tuo_count': len(tuo.back)
        }

class SSQCalculator(LotteryCalculator):
    """双色球计算器"""
    
    def calculate_complex_bet(self, numbers: SSQNumber) -> Dict:
        """计算复式投注注数和金额"""
        if not numbers.validate():
            raise ValueError("号码不合法")
            
        red_count = len(numbers.red)
        blue_count = 1 if isinstance(numbers.blue, int) else len(numbers.blue)
        
        # 计算注数
        red_combinations = len(list(itertools.combinations(numbers.red, 6)))
        total_bets = red_combinations * blue_count
        
        return {
            'bets': total_bets,
            'amount': total_bets * 2,
            'red_count': red_count,
            'blue_count': blue_count
        }
    
    def calculate_dantuo_bet(self, dan: SSQNumber, tuo: SSQNumber) -> Dict:
        """计算胆拖投注注数和金额"""
        # 验证胆码数量
        if len(dan.red) >= 6:
            raise ValueError("胆码数量超出限制")
            
        # 计算注数
        red_combinations = len(list(itertools.combinations(tuo.red, 6 - len(dan.red))))
        blue_count = 1 if isinstance(tuo.blue, int) else len(tuo.blue)
        total_bets = red_combinations * blue_count
        
        return {
            'bets': total_bets,
            'amount': total_bets * 2,
            'red_dan_count': len(dan.red),
            'red_tuo_count': len(tuo.red),
            'blue_count': blue_count
        }