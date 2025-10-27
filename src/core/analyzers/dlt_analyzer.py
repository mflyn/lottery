from typing import List, Dict, Optional, Any
from collections import Counter
import numpy as np
import random
import itertools
from scipy import stats
from .lottery_analyzer import LotteryAnalyzer

class DLTAnalyzer(LotteryAnalyzer):
    """大乐透数据分析器（增强版）"""

    def __init__(self):
        """初始化分析器"""
        super().__init__()
        self.front_range = (1, 35)
        self.back_range = (1, 12)
        self.front_count = 5
        self.back_count = 2

    def analyze_frequency(self, history_data: List[Dict], periods: int = 100) -> Dict:
        """分析号码出现频率

        Args:
            history_data: 历史开奖数据
            periods: 分析的期数

        Returns:
            频率分析结果
        """
        recent_data = history_data[:periods]
        front_numbers = []
        back_numbers = []
        total_draws = len(recent_data)

        for draw in recent_data:
            front_numbers.extend(draw['front_numbers'])
            back_numbers.extend(draw['back_numbers'])

        front_freq = Counter(front_numbers)
        back_freq = Counter(back_numbers)

        # 计算理论出现次数
        front_theory = periods * 5 / 35
        back_theory = periods * 2 / 12

        # 计算频率（出现次数/总期数）
        front_frequency = {num: count/total_draws for num, count in front_freq.items()}
        back_frequency = {num: count/total_draws for num, count in back_freq.items()}

        return {
            'front_frequency': front_frequency,
            'back_frequency': back_frequency,
            'front_counts': dict(front_freq),
            'back_counts': dict(back_freq),
            'front_theory': front_theory,
            'back_theory': back_theory,
            'periods': periods,
            'total_draws': total_draws
        }

    def analyze_trends(self, history_data: List[Dict], periods: int = 30) -> Dict:
        """分析号码走势

        Args:
            history_data: 历史开奖数据
            periods: 分析的期数

        Returns:
            走势分析结果
        """
        recent_data = history_data[:periods]
        front_matrix = np.zeros((periods, 35))
        back_matrix = np.zeros((periods, 12))

        for i, draw in enumerate(recent_data):
            for num in draw['front_numbers']:
                front_matrix[i][num-1] = 1
            for num in draw['back_numbers']:
                back_matrix[i][num-1] = 1

        return {
            'front_trends': front_matrix.tolist(),
            'back_trends': back_matrix.tolist(),
            'periods': periods
        }

    def analyze_hot_cold_numbers(self, history_data: List[Dict], recent_draws: int = 30) -> Dict:
        """分析热门和冷门号码

        Args:
            history_data: 历史开奖数据
            recent_draws: 最近几期作为参考

        Returns:
            热冷号分析结果
        """
        recent_data = history_data[:recent_draws]
        front_counts = Counter()
        back_counts = Counter()

        for draw in recent_data:
            front_counts.update(draw['front_numbers'])
            back_counts.update(draw['back_numbers'])

        # 定义热冷标准
        def get_temperature(count: int, total_draws: int, numbers_per_draw: int, total_numbers: int) -> str:
            """根据出现次数判断号码温度"""
            expected_rate = numbers_per_draw / total_numbers
            actual_rate = count / total_draws

            if actual_rate >= expected_rate * 1.5:  # 超过期望值50%为热号
                return 'hot'
            elif actual_rate <= expected_rate * 0.5:  # 低于期望值50%为冷号
                return 'cold'
            return 'normal'

        # 分类前区号码
        front_temperature = {}
        for num in range(1, 36):
            count = front_counts.get(num, 0)
            front_temperature[num] = get_temperature(count, recent_draws, 5, 35)

        # 分类后区号码
        back_temperature = {}
        for num in range(1, 13):
            count = back_counts.get(num, 0)
            back_temperature[num] = get_temperature(count, recent_draws, 2, 12)

        # 统计各类号码
        front_hot = [num for num, temp in front_temperature.items() if temp == 'hot']
        front_cold = [num for num, temp in front_temperature.items() if temp == 'cold']
        back_hot = [num for num, temp in back_temperature.items() if temp == 'hot']
        back_cold = [num for num, temp in back_temperature.items() if temp == 'cold']

        return {
            'front_temperature': front_temperature,
            'back_temperature': back_temperature,
            'front_hot': front_hot,
            'front_cold': front_cold,
            'back_hot': back_hot,
            'back_cold': back_cold,
            'front_counts': dict(front_counts),
            'back_counts': dict(back_counts),
            'reference_draws': recent_draws
        }

    def analyze_missing_numbers(self, history_data: List[Dict]) -> Dict:
        """分析号码遗漏值

        Args:
            history_data: 历史开奖数据

        Returns:
            遗漏值分析结果
        """
        front_missing = {i: 0 for i in range(1, 36)}
        back_missing = {i: 0 for i in range(1, 13)}

        # 计算当前遗漏值（从最新一期开始往前）
        for draw in history_data:
            front_numbers = draw['front_numbers']
            back_numbers = draw['back_numbers']

            # 更新前区遗漏值
            for num in front_missing:
                if num in front_numbers:
                    front_missing[num] = 0
                else:
                    front_missing[num] += 1

            # 更新后区遗漏值
            for num in back_missing:
                if num in back_numbers:
                    back_missing[num] = 0
                else:
                    back_missing[num] += 1

        # 找出最长遗漏号码
        front_max_missing = sorted(front_missing.items(), key=lambda x: x[1], reverse=True)[:5]
        back_max_missing = sorted(back_missing.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            'front_missing': front_missing,
            'back_missing': back_missing,
            'front_max_missing': front_max_missing,
            'back_max_missing': back_max_missing
        }

    def analyze_combinations(self, history_data: List[Dict], top_n: int = 10) -> Dict:
        """分析号码组合特征

        Args:
            history_data: 历史开奖数据
            top_n: 返回前N个最常见组合

        Returns:
            组合分析结果
        """
        combinations_data = {
            'sum_distribution': self._analyze_sum_distribution(history_data),
            'odd_even_ratio': self._analyze_odd_even_ratio(history_data),
            'span_analysis': self._analyze_number_span(history_data),
            'consecutive_numbers': self._analyze_consecutive_numbers(history_data),
            'common_pairs': self._find_common_pairs(history_data, top_n),
            'zone_distribution': self._analyze_zone_distribution(history_data)
        }

        return combinations_data

    def _analyze_sum_distribution(self, history_data: List[Dict]) -> Dict:
        """分析号码和值分布"""
        front_sums = []
        back_sums = []

        for draw in history_data:
            front_sums.append(sum(draw['front_numbers']))
            back_sums.append(sum(draw['back_numbers']))

        return {
            'front': {
                'min_sum': min(front_sums),
                'max_sum': max(front_sums),
                'avg_sum': sum(front_sums) / len(front_sums),
                'most_common_sums': Counter(front_sums).most_common(5)
            },
            'back': {
                'min_sum': min(back_sums),
                'max_sum': max(back_sums),
                'avg_sum': sum(back_sums) / len(back_sums),
                'most_common_sums': Counter(back_sums).most_common(5)
            }
        }

    def _analyze_odd_even_ratio(self, history_data: List[Dict]) -> Dict:
        """分析奇偶比例"""
        front_ratios = []
        back_ratios = []

        for draw in history_data:
            # 前区奇偶比
            front_odd = sum(1 for x in draw['front_numbers'] if x % 2 == 1)
            front_even = len(draw['front_numbers']) - front_odd
            front_ratios.append(f"{front_odd}:{front_even}")

            # 后区奇偶比
            back_odd = sum(1 for x in draw['back_numbers'] if x % 2 == 1)
            back_even = len(draw['back_numbers']) - back_odd
            back_ratios.append(f"{back_odd}:{back_even}")

        return {
            'front': {
                'ratio_distribution': Counter(front_ratios).most_common(),
                'most_common_ratio': Counter(front_ratios).most_common(1)[0]
            },
            'back': {
                'ratio_distribution': Counter(back_ratios).most_common(),
                'most_common_ratio': Counter(back_ratios).most_common(1)[0]
            }
        }

    def _analyze_number_span(self, history_data: List[Dict]) -> Dict:
        """分析号码跨度"""
        front_spans = []
        back_spans = []

        for draw in history_data:
            front_spans.append(max(draw['front_numbers']) - min(draw['front_numbers']))
            back_spans.append(max(draw['back_numbers']) - min(draw['back_numbers']))

        return {
            'front': {
                'min_span': min(front_spans),
                'max_span': max(front_spans),
                'avg_span': sum(front_spans) / len(front_spans),
                'common_spans': Counter(front_spans).most_common(5)
            },
            'back': {
                'min_span': min(back_spans),
                'max_span': max(back_spans),
                'avg_span': sum(back_spans) / len(back_spans),
                'common_spans': Counter(back_spans).most_common(5)
            }
        }

    def _analyze_consecutive_numbers(self, history_data: List[Dict]) -> Dict:
        """分析连号情况"""
        front_consecutive_stats = []
        back_consecutive_stats = []

        for draw in history_data:
            # 前区连号
            front_sorted = sorted(draw['front_numbers'])
            front_consecutive = 0
            for i in range(len(front_sorted) - 1):
                if front_sorted[i + 1] - front_sorted[i] == 1:
                    front_consecutive += 1
            front_consecutive_stats.append(front_consecutive)

            # 后区连号
            back_sorted = sorted(draw['back_numbers'])
            back_consecutive = 0
            for i in range(len(back_sorted) - 1):
                if back_sorted[i + 1] - back_sorted[i] == 1:
                    back_consecutive += 1
            back_consecutive_stats.append(back_consecutive)

        return {
            'front': {
                'consecutive_distribution': Counter(front_consecutive_stats).most_common(),
                'max_consecutive_found': max(front_consecutive_stats)
            },
            'back': {
                'consecutive_distribution': Counter(back_consecutive_stats).most_common(),
                'max_consecutive_found': max(back_consecutive_stats)
            }
        }

    def _find_common_pairs(self, history_data: List[Dict], top_n: int) -> Dict:
        """查找常见号码对"""
        front_pairs = Counter()
        back_pairs = Counter()

        for draw in history_data:
            # 统计前区号码对
            for pair in itertools.combinations(sorted(draw['front_numbers']), 2):
                front_pairs[pair] += 1

            # 统计后区号码对（如果有2个号码）
            if len(draw['back_numbers']) == 2:
                back_pair = tuple(sorted(draw['back_numbers']))
                back_pairs[back_pair] += 1

        return {
            'front_common_pairs': front_pairs.most_common(top_n),
            'back_common_pairs': back_pairs.most_common(top_n)
        }

    def _analyze_zone_distribution(self, history_data: List[Dict]) -> Dict:
        """分析号码区间分布"""
        # 前区分为3个区间
        front_zones = {
            'low': (1, 12),
            'mid': (13, 24),
            'high': (25, 35)
        }

        # 后区分为3个区间
        back_zones = {
            'low': (1, 4),
            'mid': (5, 8),
            'high': (9, 12)
        }

        front_zone_stats = []
        back_zone_stats = []

        for draw in history_data:
            # 前区区间分布
            front_zone_count = {'low': 0, 'mid': 0, 'high': 0}
            for num in draw['front_numbers']:
                for zone, (start, end) in front_zones.items():
                    if start <= num <= end:
                        front_zone_count[zone] += 1
                        break
            front_zone_stats.append(tuple(front_zone_count.values()))

            # 后区区间分布
            back_zone_count = {'low': 0, 'mid': 0, 'high': 0}
            for num in draw['back_numbers']:
                for zone, (start, end) in back_zones.items():
                    if start <= num <= end:
                        back_zone_count[zone] += 1
                        break
            back_zone_stats.append(tuple(back_zone_count.values()))

        return {
            'front': {
                'zone_distribution': Counter(front_zone_stats).most_common(),
                'zones_defined': front_zones
            },
            'back': {
                'zone_distribution': Counter(back_zone_stats).most_common(),
                'zones_defined': back_zones
            }
        }

    def extract_advanced_features(self, history_data: List[Dict]) -> Dict:
        """提取高级特征

        Args:
            history_data: 历史开奖数据

        Returns:
            高级特征字典
        """
        features = {
            'number_patterns': self._analyze_number_patterns(history_data),
            'statistical_moments': self._calculate_statistical_moments(history_data),
            'repeat_patterns': self._analyze_repeat_patterns(history_data),
            'prime_composite_ratio': self._analyze_prime_composite_ratio(history_data)
        }

        return features

    def _analyze_number_patterns(self, history_data: List[Dict]) -> Dict:
        """分析号码模式特征"""
        patterns = {
            'front': {
                'consecutive': [],
                'repeats': [],
                'gaps': [],
                'odd_even': [],
                'high_low': []
            },
            'back': {
                'consecutive': [],
                'repeats': [],
                'gaps': [],
                'odd_even': [],
                'high_low': []
            }
        }

        for i, draw in enumerate(history_data):
            # 前区模式
            front_sorted = sorted(draw['front_numbers'])

            # 连号
            front_consecutive = sum(1 for j in range(len(front_sorted) - 1)
                                   if front_sorted[j + 1] - front_sorted[j] == 1)
            patterns['front']['consecutive'].append(front_consecutive)

            # 重号（与上一期比较）
            if i > 0:
                prev_front = set(history_data[i - 1]['front_numbers'])
                curr_front = set(front_sorted)
                repeat_count = len(curr_front & prev_front)
                patterns['front']['repeats'].append(repeat_count)

            # 间隔
            gaps = [front_sorted[j] - front_sorted[j - 1] for j in range(1, len(front_sorted))]
            patterns['front']['gaps'].append(sum(gaps) / len(gaps) if gaps else 0)

            # 奇偶
            odd_count = sum(1 for x in front_sorted if x % 2 == 1)
            patterns['front']['odd_even'].append(odd_count)

            # 大小（以18为分界）
            high_count = sum(1 for x in front_sorted if x > 18)
            patterns['front']['high_low'].append(high_count)

            # 后区模式
            back_sorted = sorted(draw['back_numbers'])

            # 连号
            back_consecutive = sum(1 for j in range(len(back_sorted) - 1)
                                  if back_sorted[j + 1] - back_sorted[j] == 1)
            patterns['back']['consecutive'].append(back_consecutive)

            # 重号
            if i > 0:
                prev_back = set(history_data[i - 1]['back_numbers'])
                curr_back = set(back_sorted)
                repeat_count = len(curr_back & prev_back)
                patterns['back']['repeats'].append(repeat_count)

            # 间隔
            gaps = [back_sorted[j] - back_sorted[j - 1] for j in range(1, len(back_sorted))]
            patterns['back']['gaps'].append(sum(gaps) / len(gaps) if gaps else 0)

            # 奇偶
            odd_count = sum(1 for x in back_sorted if x % 2 == 1)
            patterns['back']['odd_even'].append(odd_count)

            # 大小（以7为分界）
            high_count = sum(1 for x in back_sorted if x > 6)
            patterns['back']['high_low'].append(high_count)

        return patterns

    def _calculate_statistical_moments(self, history_data: List[Dict]) -> Dict:
        """计算统计矩特征"""
        moments = {
            'front': {
                'mean': [],
                'variance': [],
                'skewness': [],
                'kurtosis': []
            },
            'back': {
                'mean': [],
                'variance': [],
                'skewness': [],
                'kurtosis': []
            }
        }

        for draw in history_data:
            # 前区统计矩
            front_numbers = draw['front_numbers']
            moments['front']['mean'].append(np.mean(front_numbers))
            moments['front']['variance'].append(np.var(front_numbers))
            moments['front']['skewness'].append(stats.skew(front_numbers))
            moments['front']['kurtosis'].append(stats.kurtosis(front_numbers))

            # 后区统计矩
            back_numbers = draw['back_numbers']
            moments['back']['mean'].append(np.mean(back_numbers))
            moments['back']['variance'].append(np.var(back_numbers))
            moments['back']['skewness'].append(stats.skew(back_numbers))
            moments['back']['kurtosis'].append(stats.kurtosis(back_numbers))

        return moments

    def _analyze_repeat_patterns(self, history_data: List[Dict]) -> Dict:
        """分析重复号码模式"""
        front_repeat_patterns = []
        back_repeat_patterns = []

        for i in range(len(history_data) - 1):
            # 前区重复
            current_front = set(history_data[i]['front_numbers'])
            next_front = set(history_data[i + 1]['front_numbers'])
            front_repeat_count = len(current_front & next_front)
            front_repeat_patterns.append(front_repeat_count)

            # 后区重复
            current_back = set(history_data[i]['back_numbers'])
            next_back = set(history_data[i + 1]['back_numbers'])
            back_repeat_count = len(current_back & next_back)
            back_repeat_patterns.append(back_repeat_count)

        return {
            'front': {
                'repeat_distribution': Counter(front_repeat_patterns).most_common(),
                'avg_repeat_count': sum(front_repeat_patterns) / len(front_repeat_patterns) if front_repeat_patterns else 0
            },
            'back': {
                'repeat_distribution': Counter(back_repeat_patterns).most_common(),
                'avg_repeat_count': sum(back_repeat_patterns) / len(back_repeat_patterns) if back_repeat_patterns else 0
            }
        }

    def _analyze_prime_composite_ratio(self, history_data: List[Dict]) -> Dict:
        """分析质数和合数比例"""
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True

        front_ratios = []
        back_ratios = []

        for draw in history_data:
            # 前区质合比
            front_prime = sum(1 for x in draw['front_numbers'] if is_prime(x))
            front_composite = len(draw['front_numbers']) - front_prime
            front_ratios.append(f"{front_prime}:{front_composite}")

            # 后区质合比
            back_prime = sum(1 for x in draw['back_numbers'] if is_prime(x))
            back_composite = len(draw['back_numbers']) - back_prime
            back_ratios.append(f"{back_prime}:{back_composite}")

        return {
            'front': {
                'ratio_distribution': Counter(front_ratios).most_common(),
                'most_common_ratio': Counter(front_ratios).most_common(1)[0] if front_ratios else None
            },
            'back': {
                'ratio_distribution': Counter(back_ratios).most_common(),
                'most_common_ratio': Counter(back_ratios).most_common(1)[0] if back_ratios else None
            }
        }

    def analyze_all(self, history_data: List[Dict], periods: int = 100) -> Dict:
        """执行全面分析

        Args:
            history_data: 历史开奖数据
            periods: 分析的期数

        Returns:
            包含所有分析结果的字典
        """
        # 限制数据量
        data_to_analyze = history_data[:periods]

        results = {
            'frequency': self.analyze_frequency(data_to_analyze, periods),
            'hot_cold': self.analyze_hot_cold_numbers(data_to_analyze),
            'missing': self.analyze_missing_numbers(data_to_analyze),
            'trends': self.analyze_trends(data_to_analyze),
            'combinations': self.analyze_combinations(data_to_analyze),
            'advanced_features': self.extract_advanced_features(data_to_analyze),
            'metadata': {
                'periods_analyzed': len(data_to_analyze),
                'requested_periods': periods
            }
        }

        return results

    def generate_smart_numbers(self, history_data: List[Dict], count: int = 5) -> List[Dict]:
        """基于分析结果智能生成号码

        Args:
            history_data: 历史开奖数据
            count: 生成号码组数

        Returns:
            生成的号码列表
        """
        # 进行全面分析
        analysis = self.analyze_all(history_data, 100)

        generated_numbers = []
        for _ in range(count):
            # 根据分析结果生成符合规律的号码
            front_numbers = self._generate_front_numbers(analysis)
            back_numbers = self._generate_back_numbers(analysis)

            generated_numbers.append({
                'front': sorted(front_numbers),
                'back': sorted(back_numbers)
            })

        return generated_numbers

    def _generate_front_numbers(self, analysis: Dict) -> List[int]:
        """根据分析结果生成前区号码"""
        # 获取热门号码
        hot_numbers = analysis['hot_cold']['front_hot']

        # 获取最长遗漏号码
        missing_numbers = [num for num, _ in analysis['missing']['front_max_missing']]

        # 综合考虑各种因素生成号码
        selected = []

        # 从热门号码中选择2-3个
        if hot_numbers:
            selected.extend(random.sample(hot_numbers, min(random.randint(2, 3), len(hot_numbers))))

        # 从遗漏号码中选择1-2个
        if missing_numbers:
            selected.extend(random.sample(missing_numbers, min(random.randint(1, 2), len(missing_numbers))))

        # 剩余号码随机选择
        remaining = list(set(range(1, 36)) - set(selected))
        if len(selected) < 5:
            selected.extend(random.sample(remaining, 5 - len(selected)))

        return selected[:5]

    def _generate_back_numbers(self, analysis: Dict) -> List[int]:
        """根据分析结果生成后区号码"""
        # 获取热门号码
        hot_numbers = analysis['hot_cold']['back_hot']

        # 获取最长遗漏号码
        missing_numbers = [num for num, _ in analysis['missing']['back_max_missing']]

        # 综合考虑各种因素生成号码
        selected = []

        # 70%概率选择热门号码，30%概率选择遗漏号码
        if random.random() < 0.7 and hot_numbers:
            selected.append(random.choice(hot_numbers))
        elif missing_numbers:
            selected.append(random.choice(missing_numbers))
        else:
            selected.append(random.randint(1, 12))

        # 选择第二个号码
        remaining = list(set(range(1, 13)) - set(selected))
        if remaining:
            selected.append(random.choice(remaining))
        else:
            # 如果没有剩余号码，随机选择
            selected.append(random.randint(1, 12))

        return selected[:2]

    def predict_trends(self, history_data: List[Dict], periods: int = 10) -> Dict:
        """预测号码趋势

        Args:
            history_data: 历史开奖数据
            periods: 预测的期数

        Returns:
            趋势预测结果
        """
        # 分析最近的趋势
        analysis = self.analyze_all(history_data, 50)

        # 基于统计特征预测
        predictions = {
            'front_recommended': [],
            'back_recommended': [],
            'front_avoid': [],
            'back_avoid': [],
            'confidence': 'medium'
        }

        # 推荐热门号码和长遗漏号码
        hot_cold = analysis['hot_cold']
        missing = analysis['missing']

        # 前区推荐
        predictions['front_recommended'].extend(hot_cold['front_hot'][:5])
        predictions['front_recommended'].extend([num for num, _ in missing['front_max_missing'][:3]])
        predictions['front_recommended'] = list(set(predictions['front_recommended']))[:10]

        # 前区避免
        predictions['front_avoid'] = hot_cold['front_cold'][:5]

        # 后区推荐
        predictions['back_recommended'].extend(hot_cold['back_hot'][:3])
        predictions['back_recommended'].extend([num for num, _ in missing['back_max_missing'][:2]])
        predictions['back_recommended'] = list(set(predictions['back_recommended']))[:5]

        # 后区避免
        predictions['back_avoid'] = hot_cold['back_cold'][:3]

        return predictions
