from typing import List, Dict, Union
import random
import numpy as np
import pandas as pd
from .models import DLTNumber, SSQNumber, LotteryNumber
from .analyzers import PatternAnalyzer, FrequencyAnalyzer

class LotteryNumberGenerator:
    def __init__(self, lottery_type='dlt'):
        self.lottery_type = lottery_type
        self.strategies = {
            'random': self.generate_random,
            'smart': self.generate_smart,
            'hybrid': self.generate_hybrid
        }

    def generate_random(self):
        """随机生成号码"""
        if self.lottery_type == 'dlt':
            # 大乐透：前区5个号码(1-35)，后区2个号码(1-12)
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            return DLTNumber(front, back)
        else:
            # 双色球：红球6个号码(1-33)，蓝球1个号码(1-16)
            red = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)
            return SSQNumber(red, blue)

    def generate_smart(self, history_data=None, pattern_data=None, frequency_data=None, weights=None):
        """智能生成号码
        
        Args:
            history_data: 历史数据
            pattern_data: 模式分析数据
            frequency_data: 频率分析数据
            weights: 各策略权重字典
        """
        if weights is None:
            weights = {
                'frequency': 0.4,
                'pattern': 0.3,
                'random': 0.3
            }
        
        if history_data is None:
            return self.generate_random()
        
        # 根据权重使用不同策略生成号码
        strategy_choice = random.choices(
            ['frequency', 'pattern', 'random'],
            weights=[weights.get(k, 0.33) for k in ['frequency', 'pattern', 'random']]
        )[0]
        
        if strategy_choice == 'random':
            return self.generate_random()
        elif strategy_choice == 'frequency':
            return self._generate_by_frequency(history_data)
        else:  # pattern
            return self._generate_by_pattern(history_data)

    def generate_hybrid(self, history_data=None):
        """混合策略生成号码"""
        # 结合随机和智能策略
        if random.random() < 0.5:
            return self.generate_random()
        else:
            return self.generate_smart(history_data)

    def generate_numbers(self, count=1, strategy='random', **kwargs):
        """生成指定数量的号码"""
        if strategy not in self.strategies:
            raise ValueError(f"不支持的策略: {strategy}")
            
        numbers = []
        for _ in range(count):
            number = self.strategies[strategy](**kwargs)
            numbers.append(number)
            
        return numbers

    def _generate_by_frequency(self, history_data):
        """基于频率生成号码"""
        if self.lottery_type == 'dlt':
            front = sorted(random.sample(range(1, 36), 5))  # 临时使用随机生成
            back = sorted(random.sample(range(1, 13), 2))
            return DLTNumber(front=front, back=back)
        else:
            red = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)
            return SSQNumber(red=red, blue=blue)

    def _generate_by_pattern(self, history_data):
        """基于模式生成号码"""
        if self.lottery_type == 'dlt':
            front = sorted(random.sample(range(1, 36), 5))  # 临时使用随机生成
            back = sorted(random.sample(range(1, 13), 2))
            return DLTNumber(front=front, back=back)
        else:
            red = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)
            return SSQNumber(red=red, blue=blue)

def generate_random_numbers(lottery_type: str, num_sets: int = 1) -> List[Dict[str, Union[List[int], int]]]:
    """生成指定数量的随机彩票号码
    
    Args:
        lottery_type: 'ssq' 或 'dlt'
        num_sets: 要生成的注数
        
    Returns:
        包含号码的字典列表，例如:
        [{'red': [1, 5, 10, 15, 20, 25], 'blue': 8}] 或
        [{'front': [2, 8, 15, 22, 30], 'back': [3, 9]}]
    """
    generated_sets = []
    for _ in range(num_sets):
        if lottery_type == 'ssq':
            red_balls = sorted(random.sample(range(1, 34), 6))
            blue_ball = random.randint(1, 16)
            generated_sets.append({'red': red_balls, 'blue': blue_ball})
        elif lottery_type == 'dlt':
            front_balls = sorted(random.sample(range(1, 36), 5))
            back_balls = sorted(random.sample(range(1, 13), 2))
            generated_sets.append({'front': front_balls, 'back': back_balls})
        else:
            # 可以选择抛出错误或返回空列表
            pass
    return generated_sets

def generate_hot_cold_numbers(lottery_type: str, num_sets: int, freq_results: Dict) -> List[Dict[str, Union[List[int], int]]]:
    """根据号码冷热度 (频率) 生成号码

    Args:
        lottery_type: 'ssq' 或 'dlt'
        num_sets: 要生成的注数
        freq_results: FrequencyAnalyzer.analyze() 返回的结果字典

    Returns:
        包含号码的字典列表，失败则返回空列表
    """
    generated_sets = []

    try:
        if lottery_type == 'ssq':
            red_freq = freq_results.get('red', {}).get('frequencies', {})
            blue_freq = freq_results.get('blue', {}).get('frequencies', {})

            if not red_freq or not blue_freq:
                 print("错误：双色球频率数据不足")
                 return []

            red_numbers = np.array([int(k) for k in red_freq.keys()])
            red_counts = np.array([v for v in red_freq.values()])
            red_probs = red_counts / red_counts.sum() if red_counts.sum() > 0 else None

            blue_numbers = np.array([int(k) for k in blue_freq.keys()])
            blue_counts = np.array([v for v in blue_freq.values()])
            blue_probs = blue_counts / blue_counts.sum() if blue_counts.sum() > 0 else None

            for _ in range(num_sets):
                # 如果概率无效（例如历史数据中某些号码从未出现），则退回随机选择
                selected_red = sorted(list(np.random.choice(red_numbers, 6, replace=False, p=red_probs if red_probs is not None else None)))
                selected_blue = np.random.choice(blue_numbers, 1, replace=False, p=blue_probs if blue_probs is not None else None)[0]
                generated_sets.append({'red': selected_red, 'blue': selected_blue})

        elif lottery_type == 'dlt':
            front_freq = freq_results.get('front', {}).get('frequencies', {})
            back_freq = freq_results.get('back', {}).get('frequencies', {})

            if not front_freq or not back_freq:
                 print("错误：大乐透频率数据不足")
                 return []

            front_numbers = np.array([int(k) for k in front_freq.keys()])
            front_counts = np.array([v for v in front_freq.values()])
            front_probs = front_counts / front_counts.sum() if front_counts.sum() > 0 else None

            back_numbers = np.array([int(k) for k in back_freq.keys()])
            back_counts = np.array([v for v in back_freq.values()])
            back_probs = back_counts / back_counts.sum() if back_counts.sum() > 0 else None

            for _ in range(num_sets):
                selected_front = sorted(list(np.random.choice(front_numbers, 5, replace=False, p=front_probs if front_probs is not None else None)))
                selected_back = sorted(list(np.random.choice(back_numbers, 2, replace=False, p=back_probs if back_probs is not None else None)))
                generated_sets.append({'front': selected_front, 'back': selected_back})
        else:
             print(f"错误：不支持的彩票类型 {lottery_type}")
             return []

    except Exception as e:
        print(f"生成冷热号码时出错: {e}")
        # import traceback
        # traceback.print_exc() # 调试时可以取消注释打印详细错误
        return [] # 出错时返回空列表

    return generated_sets
