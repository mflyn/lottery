import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import Counter
from .random_generator import RandomGenerator
from ..models import LotteryNumber
from ..features.feature_engineering import FeatureEngineering
from ..data_manager import LotteryDataManager

class SmartNumberGenerator:
    """智能号码推荐生成器"""
    
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type
        self.random_generator = RandomGenerator(lottery_type)
        self.data_manager = LotteryDataManager()
        self.feature_engineering = FeatureEngineering()
        
        # 配置参数
        self.config = {
            'dlt': {
                'front_range': (1, 35),
                'back_range': (1, 12),
                'hot_threshold': 0.6,  # 热号出现频率阈值
                'cold_threshold': 0.3,  # 冷号出现频率阈值
                'analysis_periods': 30  # 分析最近期数
            },
            'ssq': {
                'red_range': (1, 33),
                'blue_range': (1, 16),
                'hot_threshold': 0.6,
                'cold_threshold': 0.3,
                'analysis_periods': 30
            }
        }

    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成号码（兼容接口）
        
        Args:
            count: 需要生成的号码组数
            **kwargs: 其他参数
            
        Returns:
            生成的号码列表
        """
        try:
            return self.generate_recommended(count)
        except Exception:
            # 如果智能生成失败，回退到随机生成
            return self.random_generator.generate(count)

    def generate_recommended(self, count: int = 1) -> List[LotteryNumber]:
        """生成推荐号码
        
        Args:
            count: 需要生成的号码组数
        """
        try:
            # 获取历史数据
            history_data = self.data_manager.get_history_data(self.lottery_type)
            
            # 如果没有历史数据，使用随机生成
            if history_data is None or history_data.empty:
                return self.random_generator.generate(count)
            
            # 特征工程
            features = self.feature_engineering.generate_features(history_data)
            
            # 分析热冷号
            hot_cold_numbers = self._analyze_hot_cold_numbers(history_data)
            
            # 分析号码间隔
            gap_patterns = self._analyze_gap_patterns(history_data)
            
            # 生成符合模式的号码
            numbers = []
            for _ in range(count):
                number = self._generate_smart_number(
                    hot_cold_numbers,
                    gap_patterns,
                    features
                )
                numbers.append(number)
                
            return numbers
        except Exception:
            # 如果智能生成失败，回退到随机生成
            return self.random_generator.generate(count)
    
    def _generate_smart_number(self, 
                             hot_cold_numbers: Dict,
                             gap_patterns: Dict,
                             features: Dict) -> LotteryNumber:
        """根据分析结果生成智能号码"""
        if self.lottery_type == 'dlt':
            # 根据热冷号比例选择前区号码
            front_numbers = self._select_numbers_by_pattern(
                hot_cold_numbers['front'],
                5,
                (1, 35)
            )
            
            # 根据热冷号比例选择后区号码
            back_numbers = self._select_numbers_by_pattern(
                hot_cold_numbers['back'],
                2,
                (1, 12)
            )
            
            return LotteryNumber(front=sorted(front_numbers), 
                               back=sorted(back_numbers))
        
        else:  # ssq
            # 根据热冷号比例选择红球号码
            red_numbers = self._select_numbers_by_pattern(
                hot_cold_numbers['red'],
                6,
                (1, 33)
            )
            
            # 选择蓝球号码
            blue_number = self._select_blue_number(hot_cold_numbers['blue'])
            
            return LotteryNumber(red=sorted(red_numbers), 
                               blue=blue_number)

    def _analyze_hot_cold_numbers(self, data: pd.DataFrame) -> Dict:
        """分析热冷号分布
        
        Args:
            data: 历史开奖数据DataFrame
        
        Returns:
            Dict: 包含热冷号分析结果的字典
        """
        recent_data = data.head(self.config[self.lottery_type]['analysis_periods'])
        
        if self.lottery_type == 'dlt':
            # 分析前区号码
            front_numbers = []
            for _, row in recent_data.iterrows():
                front_numbers.extend(row['front_numbers'])
            front_counter = Counter(front_numbers)
            
            # 计算出现频率
            front_freq = {
                num: count / self.config[self.lottery_type]['analysis_periods']
                for num, count in front_counter.items()
            }
            
            # 分类热冷号
            front_hot = [num for num, freq in front_freq.items() 
                        if freq >= self.config[self.lottery_type]['hot_threshold']]
            front_cold = [num for num, freq in front_freq.items()
                         if freq <= self.config[self.lottery_type]['cold_threshold']]
            front_normal = [num for num in range(1, 36)
                          if num not in front_hot and num not in front_cold]
            
            # 后区分析
            back_numbers = []
            for _, row in recent_data.iterrows():
                back_numbers.extend(row['back_numbers'])
            back_counter = Counter(back_numbers)
            
            back_freq = {
                num: count / self.config[self.lottery_type]['analysis_periods']
                for num, count in back_counter.items()
            }
            
            back_hot = [num for num, freq in back_freq.items()
                       if freq >= self.config[self.lottery_type]['hot_threshold']]
            back_cold = [num for num, freq in back_freq.items()
                        if freq <= self.config[self.lottery_type]['cold_threshold']]
            back_normal = [num for num in range(1, 13)
                         if num not in back_hot and num not in back_cold]
            
            return {
                'front': {
                    'hot': front_hot,
                    'cold': front_cold,
                    'normal': front_normal,
                    'frequencies': front_freq
                },
                'back': {
                    'hot': back_hot,
                    'cold': back_cold,
                    'normal': back_normal,
                    'frequencies': back_freq
                }
            }
            
        else:  # ssq
            # 红球分析
            red_numbers = []
            for _, row in recent_data.iterrows():
                red_numbers.extend(row['red_numbers'])
            red_counter = Counter(red_numbers)
            
            red_freq = {
                num: count / self.config[self.lottery_type]['analysis_periods']
                for num, count in red_counter.items()
            }
            
            red_hot = [num for num, freq in red_freq.items()
                      if freq >= self.config[self.lottery_type]['hot_threshold']]
            red_cold = [num for num, freq in red_freq.items()
                       if freq <= self.config[self.lottery_type]['cold_threshold']]
            red_normal = [num for num in range(1, 34)
                         if num not in red_hot and num not in red_cold]
            
            # 蓝球分析
            blue_numbers = recent_data['blue_number'].tolist()
            blue_counter = Counter(blue_numbers)
            
            blue_freq = {
                num: count / self.config[self.lottery_type]['analysis_periods']
                for num, count in blue_counter.items()
            }
            
            return {
                'red': {
                    'hot': red_hot,
                    'cold': red_cold,
                    'normal': red_normal,
                    'frequencies': red_freq
                },
                'blue': {
                    'frequencies': blue_freq
                }
            }

    def _analyze_gap_patterns(self, data: pd.DataFrame) -> Dict:
        """分析号码间隔模式
        
        Args:
            data: 历史开奖数据DataFrame
        
        Returns:
            Dict: 包含号码间隔模式的字典
        """
        recent_data = data.head(self.config[self.lottery_type]['analysis_periods'])
        
        if self.lottery_type == 'dlt':
            # 分析前区号码间隔
            front_gaps = []
            for _, row in recent_data.iterrows():
                numbers = sorted(row['front_numbers'])
                gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
                front_gaps.extend(gaps)
            
            # 计算间隔统计
            front_gap_counter = Counter(front_gaps)
            front_gap_prob = {
                gap: count/sum(front_gap_counter.values())
                for gap, count in front_gap_counter.items()
            }
            
            # 后区间隔分析
            back_gaps = []
            for _, row in recent_data.iterrows():
                numbers = sorted(row['back_numbers'])
                if len(numbers) > 1:
                    gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
                    back_gaps.extend(gaps)
            
            back_gap_counter = Counter(back_gaps)
            back_gap_prob = {
                gap: count/sum(back_gap_counter.values())
                for gap, count in back_gap_counter.items()
            }
            
            return {
                'front': {
                    'gaps': front_gap_prob,
                    'avg_gap': np.mean(front_gaps),
                    'std_gap': np.std(front_gaps)
                },
                'back': {
                    'gaps': back_gap_prob,
                    'avg_gap': np.mean(back_gaps),
                    'std_gap': np.std(back_gaps)
                }
            }
            
        else:  # ssq
            # 红球间隔分析
            red_gaps = []
            for _, row in recent_data.iterrows():
                numbers = sorted(row['red_numbers'])
                gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
                red_gaps.extend(gaps)
            
            red_gap_counter = Counter(red_gaps)
            red_gap_prob = {
                gap: count/sum(red_gap_counter.values())
                for gap, count in red_gap_counter.items()
            }
            
            return {
                'red': {
                    'gaps': red_gap_prob,
                    'avg_gap': np.mean(red_gaps),
                    'std_gap': np.std(red_gaps)
                }
            }

    def _select_numbers_by_pattern(self,
                                 pattern: Dict,
                                 count: int,
                                 num_range: Tuple[int, int]) -> List[int]:
        """根据模式选择号码
        
        Args:
            pattern: 号码模式字典
            count: 需要选择的号码个数
            num_range: 号码范围元组 (min, max)
        
        Returns:
            List[int]: 选择的号码列表
        """
        numbers = []
        all_numbers = list(range(num_range[0], num_range[1] + 1))
        
        # 根据热冷号比例选择
        hot_count = int(count * 0.4)  # 40%热号
        cold_count = int(count * 0.2)  # 20%冷号
        normal_count = count - hot_count - cold_count  # 剩余正常号
        
        # 选择热号
        if pattern['hot'] and hot_count > 0:
            hot_numbers = np.random.choice(
                pattern['hot'],
                min(hot_count, len(pattern['hot'])),
                replace=False
            ).tolist()
            numbers.extend(hot_numbers)
        
        # 选择冷号
        if pattern['cold'] and cold_count > 0:
            cold_numbers = np.random.choice(
                pattern['cold'],
                min(cold_count, len(pattern['cold'])),
                replace=False
            ).tolist()
            numbers.extend(cold_numbers)
        
        # 选择正常号
        remaining_count = count - len(numbers)
        if remaining_count > 0:
            available_numbers = [n for n in pattern['normal'] 
                               if n not in numbers]
            if available_numbers:
                normal_numbers = np.random.choice(
                    available_numbers,
                    min(remaining_count, len(available_numbers)),
                    replace=False
                ).tolist()
                numbers.extend(normal_numbers)
        
        # 如果还不够数，从所有可用号码中随机选择
        remaining_count = count - len(numbers)
        if remaining_count > 0:
            available_numbers = [n for n in all_numbers 
                               if n not in numbers]
            additional_numbers = np.random.choice(
                available_numbers,
                remaining_count,
                replace=False
            ).tolist()
            numbers.extend(additional_numbers)
        
        return numbers

    def _select_blue_number(self, blue_pattern: Dict) -> int:
        """选择蓝球号码
        
        Args:
            blue_pattern: 蓝球频率字典
        
        Returns:
            int: 选择的蓝球号码
        """
        frequencies = blue_pattern['frequencies']
        numbers = list(frequencies.keys())
        probabilities = list(frequencies.values())
        
        # 归一化概率
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p/total_prob for p in probabilities]
            
            # 根据概率选择号码
            return int(np.random.choice(numbers, p=probabilities))
        else:
            # 如果没有频率数据，随机选择
            if self.lottery_type == 'dlt':
                return np.random.randint(1, 13)
            else:  # ssq
                return np.random.randint(1, 17)
