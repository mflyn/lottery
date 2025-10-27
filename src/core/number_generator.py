from typing import List, Dict, Union, Optional
import random
import numpy as np
from .models import DLTNumber, SSQNumber
from .config_manager import ConfigManager

class LotteryNumberGenerator:
    def __init__(self, lottery_type='dlt', config_manager: Optional[ConfigManager] = None):
        self.lottery_type = lottery_type
        self.config = config_manager or ConfigManager()
        self.strategies = {
            'random': self.generate_random,
            'smart': self.generate_smart,
            'hybrid': self.generate_hybrid
        }

        # 从配置获取号码范围和数量
        if lottery_type == 'dlt':
            front_range = self.config.get_lottery_range('dlt', 'front')
            back_range = self.config.get_lottery_range('dlt', 'back')
            self.front_min, self.front_max = front_range
            self.back_min, self.back_max = back_range
            self.front_count = self.config.get_lottery_count('dlt', 'front')
            self.back_count = self.config.get_lottery_count('dlt', 'back')
        else:  # ssq
            red_range = self.config.get_lottery_range('ssq', 'red')
            blue_range = self.config.get_lottery_range('ssq', 'blue')
            self.red_min, self.red_max = red_range
            self.blue_min, self.blue_max = blue_range
            self.red_count = self.config.get_lottery_count('ssq', 'red')
            self.blue_count = self.config.get_lottery_count('ssq', 'blue')

    def generate_random(self):
        """随机生成号码"""
        if self.lottery_type == 'dlt':
            # 大乐透：从配置读取范围和数量
            front = sorted(random.sample(range(self.front_min, self.front_max + 1), self.front_count))
            back = sorted(random.sample(range(self.back_min, self.back_max + 1), self.back_count))
            return DLTNumber(front, back)
        else:
            # 双色球：从配置读取范围和数量
            red = sorted(random.sample(range(self.red_min, self.red_max + 1), self.red_count))
            blue = random.randint(self.blue_min, self.blue_max)
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
        """基于频率生成号码

        使用频率分析结果，优先选择热号和温号
        """
        try:
            from src.core.analyzers.frequency_analyzer import FrequencyAnalyzer

            # 执行频率分析
            analyzer = FrequencyAnalyzer(self.lottery_type, self.config)
            freq_result = analyzer.analyze(history_data, periods=min(100, len(history_data)))

            if 'data' not in freq_result:
                # 如果分析失败，回退到随机生成
                return self.generate_random()

            data = freq_result['data']

            if self.lottery_type == 'dlt':
                # 大乐透：基于频率选择前区和后区
                front = self._select_numbers_by_frequency(
                    data.get('front_area', {}).get('frequency', {}),
                    data.get('front_area', {}).get('classification', {}),
                    self.front_count,
                    (self.front_min, self.front_max)
                )
                back = self._select_numbers_by_frequency(
                    data.get('back_area', {}).get('frequency', {}),
                    data.get('back_area', {}).get('classification', {}),
                    self.back_count,
                    (self.back_min, self.back_max)
                )
                return DLTNumber(front=front, back=back)
            else:
                # 双色球：基于频率选择红球和蓝球
                red = self._select_numbers_by_frequency(
                    data.get('red_ball', {}).get('frequency', {}),
                    data.get('red_ball', {}).get('classification', {}),
                    self.red_count,
                    (self.red_min, self.red_max)
                )
                blue = self._select_single_number_by_frequency(
                    data.get('blue_ball', {}).get('frequency', {}),
                    data.get('blue_ball', {}).get('classification', {}),
                    (self.blue_min, self.blue_max)
                )
                return SSQNumber(red=red, blue=blue)

        except Exception as e:
            # 如果出错，回退到随机生成
            print(f"频率生成失败: {e}")
            return self.generate_random()

    def _generate_by_pattern(self, history_data):
        """基于模式生成号码

        考虑奇偶比、连号、跨度等模式特征
        """
        try:
            from src.core.analyzers.frequency_analyzer import FrequencyAnalyzer

            # 执行频率分析（包含模式信息）
            analyzer = FrequencyAnalyzer(self.lottery_type, self.config)
            freq_result = analyzer.analyze(history_data, periods=min(100, len(history_data)))

            if 'data' not in freq_result:
                return self.generate_random()

            data = freq_result['data']

            if self.lottery_type == 'dlt':
                # 大乐透：基于模式选择号码
                front = self._select_numbers_by_pattern(
                    data.get('front_area', {}).get('frequency', {}),
                    data.get('front_area', {}).get('patterns', {}),
                    self.front_count,
                    (self.front_min, self.front_max)
                )
                back = self._select_numbers_by_pattern(
                    data.get('back_area', {}).get('frequency', {}),
                    data.get('back_area', {}).get('patterns', {}),
                    self.back_count,
                    (self.back_min, self.back_max)
                )
                return DLTNumber(front=front, back=back)
            else:
                # 双色球：基于模式选择号码
                red = self._select_numbers_by_pattern(
                    data.get('red_ball', {}).get('frequency', {}),
                    data.get('red_ball', {}).get('patterns', {}),
                    self.red_count,
                    (self.red_min, self.red_max)
                )
                blue = self._select_single_number_by_frequency(
                    data.get('blue_ball', {}).get('frequency', {}),
                    data.get('blue_ball', {}).get('classification', {}),
                    (self.blue_min, self.blue_max)
                )
                return SSQNumber(red=red, blue=blue)

        except Exception as e:
            print(f"模式生成失败: {e}")
            return self.generate_random()

    def _select_numbers_by_frequency(self, frequency, classification, count, number_range):
        """基于频率选择号码

        Args:
            frequency: 频率字典
            classification: 分类字典 (hot/cold/normal)
            count: 需要选择的号码数量
            number_range: 号码范围 (min, max)

        Returns:
            排序后的号码列表
        """
        if not frequency:
            # 如果没有频率数据，随机选择
            return sorted(random.sample(range(number_range[0], number_range[1] + 1), count))

        # 获取热号和温号
        hot_numbers = classification.get('hot', [])
        normal_numbers = classification.get('normal', [])
        cold_numbers = classification.get('cold', [])

        # 策略：60% 热号，30% 温号，10% 冷号
        hot_count = int(count * 0.6)
        normal_count = int(count * 0.3)
        cold_count = count - hot_count - normal_count

        selected = []

        # 选择热号
        if hot_numbers and hot_count > 0:
            selected.extend(random.sample(hot_numbers, min(hot_count, len(hot_numbers))))

        # 选择温号
        if normal_numbers and normal_count > 0:
            selected.extend(random.sample(normal_numbers, min(normal_count, len(normal_numbers))))

        # 选择冷号
        if cold_numbers and cold_count > 0:
            selected.extend(random.sample(cold_numbers, min(cold_count, len(cold_numbers))))

        # 如果数量不够，从所有号码中随机补充
        if len(selected) < count:
            all_numbers = list(range(number_range[0], number_range[1] + 1))
            remaining = [n for n in all_numbers if n not in selected]
            selected.extend(random.sample(remaining, count - len(selected)))

        return sorted(selected[:count])

    def _select_single_number_by_frequency(self, frequency, classification, number_range):
        """基于频率选择单个号码（用于蓝球）

        Args:
            frequency: 频率字典
            classification: 分类字典
            number_range: 号码范围

        Returns:
            选中的号码
        """
        if not frequency:
            return random.randint(number_range[0], number_range[1])

        # 获取热号
        hot_numbers = classification.get('hot', [])
        normal_numbers = classification.get('normal', [])

        # 70% 概率选择热号，30% 概率选择温号
        if hot_numbers and random.random() < 0.7:
            return random.choice(hot_numbers)
        elif normal_numbers:
            return random.choice(normal_numbers)
        else:
            return random.randint(number_range[0], number_range[1])

    def _select_numbers_by_pattern(self, frequency, patterns, count, number_range):
        """基于模式选择号码

        考虑奇偶比、连号等模式特征

        Args:
            frequency: 频率字典
            patterns: 模式分析结果
            count: 需要选择的号码数量
            number_range: 号码范围

        Returns:
            排序后的号码列表
        """
        if not frequency:
            return sorted(random.sample(range(number_range[0], number_range[1] + 1), count))

        # 获取历史平均奇偶比
        avg_odd_ratio = patterns.get('avg_odd_ratio', 0.5)

        # 计算需要的奇数和偶数数量
        odd_count = int(count * avg_odd_ratio)
        even_count = count - odd_count

        # 分离奇数和偶数
        all_numbers = list(range(number_range[0], number_range[1] + 1))
        odd_numbers = [n for n in all_numbers if n % 2 == 1]
        even_numbers = [n for n in all_numbers if n % 2 == 0]

        # 基于频率加权选择
        selected = []

        # 选择奇数
        if odd_numbers:
            odd_weights = [frequency.get(n, 1) for n in odd_numbers]
            selected_odds = random.choices(odd_numbers, weights=odd_weights, k=min(odd_count, len(odd_numbers)))
            selected.extend(selected_odds)

        # 选择偶数
        if even_numbers:
            even_weights = [frequency.get(n, 1) for n in even_numbers]
            selected_evens = random.choices(even_numbers, weights=even_weights, k=min(even_count, len(even_numbers)))
            selected.extend(selected_evens)

        # 去重并补充
        selected = list(set(selected))
        if len(selected) < count:
            remaining = [n for n in all_numbers if n not in selected]
            selected.extend(random.sample(remaining, count - len(selected)))

        return sorted(selected[:count])

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
        # 从FrequencyAnalyzer的结果中提取频率数据
        if 'data' not in freq_results:
            print("错误：频率分析结果格式不正确，缺少'data'键")
            return []
        
        data = freq_results['data']
        
        if lottery_type == 'ssq':
            # 提取双色球频率数据
            red_freq = data.get('red_ball', {}).get('frequency', {})
            blue_freq = data.get('blue_ball', {}).get('frequency', {})

            if not red_freq or not blue_freq:
                print("错误：双色球频率数据不足")
                print(f"红球频率数据: {len(red_freq)} 项")
                print(f"蓝球频率数据: {len(blue_freq)} 项")
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
            # 提取大乐透频率数据
            front_freq = data.get('front_area', {}).get('frequency', {})
            back_freq = data.get('back_area', {}).get('frequency', {})

            if not front_freq or not back_freq:
                print("错误：大乐透频率数据不足")
                print(f"前区频率数据: {len(front_freq)} 项")
                print(f"后区频率数据: {len(back_freq)} 项")
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
        import traceback
        traceback.print_exc() # 打印详细错误信息用于调试
        return [] # 出错时返回空列表

    return generated_sets
