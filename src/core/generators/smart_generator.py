import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Union
from collections import Counter
import random
import math
from .random_generator import RandomGenerator
from ..models import LotteryNumber, SSQNumber, DLTNumber
from ..ranking import rank_and_select_best, rank_and_select_best_dlt
from ..data_manager import LotteryDataManager

class SmartNumberGenerator:
    """智能号码推荐生成器 - 支持双色球(SSQ)和大乐透(DLT)的精英选拔版"""

    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type
        self.random_generator = RandomGenerator(lottery_type)
        self.data_manager = LotteryDataManager()

        # 蓝球选择算法配置
        self.blue_algorithm_config = {
            'method': 'enhanced',  # 'simple', 'enhanced', 'ensemble'
            'weights': {
                'frequency': 0.35,    # 频率权重
                'missing': 0.30,      # 遗漏权重
                'trend': 0.20,        # 趋势权重
                'pattern': 0.10,      # 模式权重
                'random': 0.05        # 随机性权重
            },
            'analysis_periods': 50,   # 分析期数
            'trend_window': 10        # 趋势分析窗口
        }

        self.config = {
            'ssq': {
                'analysis_periods': 100,
                'batch_size_per_elite': 10,
                'recipes': [(2, 1, 3)] * 5 + [(2, 0, 4)] * 3 + [(3, 0, 3)] * 2
            },
            'dlt': {
                'analysis_periods': 100,
                'batch_size_per_elite': 10,
                'front_recipes': [(2, 1, 2)] * 5 + [(2, 2, 1)] * 3 + [(3, 1, 1)] * 2, # 5个前区号的配方
                'back_recipe': (1, 1, 0) # 2个后区号的配方 (1热,1温,0冷)
            }
        }

    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成号码（兼容接口）"""
        try:
            return self.generate_recommended(count)
        except Exception as e:
            print(f"智能生成过程发生严重错误: {e}")
            import traceback
            traceback.print_exc()
            return self.random_generator.generate(count)

    def generate_recommended(self, count: int = 1) -> List[LotteryNumber]:
        """生成精英推荐号码, 每一注都是优中选优的结果."""
        conf = self.config[self.lottery_type]
        history_data = self.data_manager.get_history_data(self.lottery_type)
        if history_data is None or history_data.empty or len(history_data) < conf['analysis_periods']:
            return self.random_generator.generate(count)
        
        hot_cold_numbers = self._analyze_hot_cold_numbers(history_data)
        
        recipes = conf.get('recipes') or conf.get('front_recipes')
        random.shuffle(recipes)

        ranking_function = rank_and_select_best if self.lottery_type == 'ssq' else rank_and_select_best_dlt

        elite_numbers = []
        for i in range(count):
            print(f"正在为[{self.lottery_type.upper()}]进行第 {i+1}/{count} 注精英号码的选拔...")
            candidates = []
            batch_size = conf['batch_size_per_elite']
            for j in range(batch_size):
                recipe = recipes[j % len(recipes)]
                candidate = self._generate_one_candidate(hot_cold_numbers, recipe)
                candidates.append(candidate)
            
            elite_number = ranking_function(candidates)
            if elite_number:
                elite_numbers.append(elite_number)
            else:
                elite_numbers.append(random.choice(candidates))

        return elite_numbers
    
    def _generate_one_candidate(self, hot_cold_numbers: Dict, recipe: Tuple[int, int, int]) -> Union[SSQNumber, DLTNumber]:
        """根据分析结果和指定配方生成一个候选号码"""
        if self.lottery_type == 'ssq':
            red_numbers = self._select_numbers_by_pattern(hot_cold_numbers['red'], recipe, (1, 33))
            # 使用改进的蓝球选择算法
            blue_number = self._select_blue_number_enhanced(hot_cold_numbers.get('blue_analysis', {}))
            return SSQNumber(red=sorted(red_numbers), blue=blue_number)

        elif self.lottery_type == 'dlt':
            front_numbers = self._select_numbers_by_pattern(hot_cold_numbers['front'], recipe, (1, 35))
            back_numbers = self._select_numbers_by_pattern(hot_cold_numbers['back'], self.config['dlt']['back_recipe'], (1, 12))
            return DLTNumber(front=sorted(front_numbers), back=sorted(back_numbers))

    def _analyze_hot_cold_numbers(self, data: pd.DataFrame) -> Dict:
        """使用Z-Score和EWMA混合模型分析冷热号分布."""
        conf = self.config[self.lottery_type]
        analysis_periods = conf['analysis_periods']
        recent_data = data.head(analysis_periods)

        def get_hybrid_pools(numbers_data, num_total, p_ratio, hot_count, cold_count):
            all_numbers = list(range(1, num_total + 1))
            n = analysis_periods
            mu = n * p_ratio
            sigma = np.sqrt(n * p_ratio * (1 - p_ratio)) if n > 0 else 1
            if sigma == 0: sigma = 1

            counts = Counter(np.concatenate(numbers_data.values))
            z_scores = {num: (counts.get(num, 0) - mu) / sigma for num in all_numbers}

            s = pd.DataFrame(0, index=recent_data.index, columns=all_numbers)
            for index, row_nums in numbers_data.items():
                if isinstance(row_nums, list):
                    s.loc[index, row_nums] = 1
            ewma_scores = s.iloc[::-1].ewm(alpha=0.1, adjust=False).mean().iloc[-1].to_dict()

            z_values = np.array(list(z_scores.values()))
            norm_z = {num: (score - z_values.min()) / (z_values.max() - z_values.min()) if (z_values.max() - z_values.min()) > 0 else 0.5 for num, score in z_scores.items()}

            ewma_values = np.array(list(ewma_scores.values()))
            norm_ewma = {num: (score - ewma_values.min()) / (ewma_values.max() - ewma_values.min()) if (ewma_values.max() - ewma_values.min()) > 0 else 0.5 for num, score in ewma_scores.items()}

            hybrid_scores = {num: 0.5 * norm_z[num] + 0.5 * norm_ewma[num] for num in all_numbers}
            sorted_by_hybrid = sorted(hybrid_scores.keys(), key=lambda num: hybrid_scores[num], reverse=True)
            
            return {
                'hot': sorted_by_hybrid[:hot_count],
                'cold': sorted_by_hybrid[-cold_count:] if cold_count > 0 else [],
                'normal': sorted_by_hybrid[hot_count:-cold_count if cold_count > 0 else len(sorted_by_hybrid)]
            }

        if self.lottery_type == 'ssq':
            red_pools = get_hybrid_pools(recent_data['red_numbers'], 33, 6/33, 7, 7)
            blue_freq = Counter(recent_data['blue_number'].tolist())
            # 添加蓝球的详细分析数据
            blue_analysis = self._analyze_blue_numbers_detailed(recent_data['blue_number'].tolist())
            return {
                'red': red_pools,
                'blue': {'frequencies': blue_freq},
                'blue_analysis': blue_analysis
            }

        elif self.lottery_type == 'dlt':
            front_pools = get_hybrid_pools(recent_data['front_numbers'], 35, 5/35, 7, 7) # 前区7热7冷
            back_pools = get_hybrid_pools(recent_data['back_numbers'], 12, 2/12, 3, 3) # 后区3热3冷
            return {'front': front_pools, 'back': back_pools}
        
        return {}

    def _select_numbers_by_pattern(self, pattern: Dict, recipe: Tuple[int, int, int], num_range: Tuple[int, int]) -> List[int]:
        """根据指定的冷热温配方选择号码"""
        hot_count, cold_count, normal_count = recipe
        numbers = []
        
        hot_pool = pattern.get('hot', [])
        cold_pool = pattern.get('cold', [])
        normal_pool = pattern.get('normal', [])

        if hot_pool and hot_count > 0:
            numbers.extend(np.random.choice(hot_pool, min(hot_count, len(hot_pool)), replace=False).tolist())
        
        if cold_pool and cold_count > 0:
            available_cold = [n for n in cold_pool if n not in numbers]
            if available_cold:
                numbers.extend(np.random.choice(available_cold, min(cold_count, len(available_cold)), replace=False).tolist())
        
        current_len = len(numbers)
        needed = (hot_count + cold_count + normal_count) - current_len
        if normal_pool and needed > 0:
            available_normal = [n for n in normal_pool if n not in numbers]
            if available_normal:
                numbers.extend(np.random.choice(available_normal, min(needed, len(available_normal)), replace=False).tolist())
        
        final_remaining = (hot_count + cold_count + normal_count) - len(numbers)
        if final_remaining > 0:
            all_numbers = list(range(num_range[0], num_range[1] + 1))
            available_numbers = [n for n in all_numbers if n not in numbers]
            if available_numbers:
                numbers.extend(np.random.choice(available_numbers, min(final_remaining, len(available_numbers)), replace=False).tolist())
        
        return numbers

    def _select_blue_number(self, blue_pattern: Dict) -> int:
        """选择SSQ蓝球号码 - 原始简单频率算法（保持兼容性）"""
        frequencies = blue_pattern.get('frequencies', {})
        if not frequencies:
            return np.random.randint(1, 17)

        numbers = list(frequencies.keys())
        probabilities = list(frequencies.values())

        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p/total_prob for p in probabilities]
            return int(np.random.choice(numbers, p=probabilities))
        else:
            return np.random.randint(1, 17)

    def _select_blue_number_enhanced(self, blue_analysis: Dict) -> int:
        """改进的蓝球选择算法 - 多因子加权模型

        算法特点：
        1. 多维度评分：频率 + 遗漏 + 趋势 + 模式 + 随机性
        2. 动态权重：可根据数据特征调整
        3. 防过拟合：适当的随机性避免过度依赖历史
        4. 鲁棒性：处理数据不足等异常情况
        """
        if not blue_analysis:
            return np.random.randint(1, 17)

        config = self.blue_algorithm_config
        method = config['method']

        if method == 'simple':
            return self._select_blue_simple(blue_analysis)
        elif method == 'enhanced':
            return self._select_blue_enhanced(blue_analysis)
        elif method == 'ensemble':
            return self._select_blue_ensemble(blue_analysis)
        else:
            return self._select_blue_enhanced(blue_analysis)

    def _analyze_blue_numbers_detailed(self, blue_numbers: List[int]) -> Dict:
        """详细分析蓝球号码的各种特征"""
        if not blue_numbers or len(blue_numbers) < 5:
            return {}

        config = self.blue_algorithm_config
        periods = min(len(blue_numbers), config['analysis_periods'])
        recent_blues = blue_numbers[:periods]

        analysis = {
            'frequency_scores': self._calculate_frequency_scores(recent_blues),
            'missing_scores': self._calculate_missing_scores(recent_blues),
            'trend_scores': self._calculate_trend_scores(recent_blues),
            'pattern_scores': self._calculate_pattern_scores(recent_blues),
            'statistics': {
                'total_periods': len(recent_blues),
                'unique_count': len(set(recent_blues)),
                'most_frequent': Counter(recent_blues).most_common(3),
                'least_frequent': Counter(recent_blues).most_common()[-3:] if len(Counter(recent_blues)) >= 3 else []
            }
        }

        return analysis

    def _calculate_frequency_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算频率评分 - 改进版本"""
        counter = Counter(blue_numbers)
        total = len(blue_numbers)
        expected_freq = total / 16  # 理论频率

        scores = {}
        for num in range(1, 17):
            actual_freq = counter.get(num, 0)

            if actual_freq == 0:
                # 从未出现的号码给予基础分
                scores[num] = 0.2
            else:
                # 使用调和平均计算偏差评分
                deviation = abs(actual_freq - expected_freq) / expected_freq
                # 频率越接近理论值，得分越高
                scores[num] = 1.0 / (1.0 + deviation * 0.5)

        return scores

    def _calculate_missing_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算遗漏评分"""
        scores = {}

        for num in range(1, 17):
            # 找到最近一次出现的位置
            last_position = -1
            for i, blue in enumerate(blue_numbers):
                if blue == num:
                    last_position = i
                    break

            if last_position == -1:
                # 从未出现，遗漏期数为总期数
                missing_periods = len(blue_numbers)
            else:
                missing_periods = last_position

            # 遗漏期数越长，得分越高，但设置上限避免过度偏向
            max_missing = len(blue_numbers) * 0.8  # 最大遗漏期数限制
            normalized_missing = min(missing_periods, max_missing) / max_missing
            scores[num] = normalized_missing

        return scores

    def _calculate_trend_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算趋势评分"""
        if len(blue_numbers) < 10:
            return {num: 0.5 for num in range(1, 17)}

        config = self.blue_algorithm_config
        window_size = min(config['trend_window'], len(blue_numbers) // 2)

        scores = {}
        for num in range(1, 17):
            # 计算近期和远期的出现频率
            recent_count = sum(1 for i in range(window_size) if blue_numbers[i] == num)
            older_start = window_size
            older_end = min(window_size * 2, len(blue_numbers))
            older_count = sum(1 for i in range(older_start, older_end) if blue_numbers[i] == num)

            recent_freq = recent_count / window_size
            older_freq = older_count / (older_end - older_start) if older_end > older_start else recent_freq

            # 计算趋势评分
            if older_freq == 0:
                trend_score = recent_freq  # 如果远期没有出现，近期频率即为趋势
            else:
                trend_ratio = recent_freq / older_freq
                # 上升趋势得高分，但限制在合理范围内
                trend_score = min(trend_ratio / 2.0, 1.0)

            scores[num] = trend_score

        return scores

    def _calculate_pattern_scores(self, blue_numbers: List[int]) -> Dict[int, float]:
        """计算模式评分 - 基于号码的数学特征"""
        scores = {}

        for num in range(1, 17):
            pattern_score = 0.5  # 基础分

            # 奇偶性评分
            if num % 2 == 1:  # 奇数
                odd_count = sum(1 for x in blue_numbers[:10] if x % 2 == 1)
                if odd_count > 5:  # 如果最近奇数较多，奇数得分略低
                    pattern_score -= 0.1
                else:
                    pattern_score += 0.1
            else:  # 偶数
                even_count = sum(1 for x in blue_numbers[:10] if x % 2 == 0)
                if even_count > 5:
                    pattern_score -= 0.1
                else:
                    pattern_score += 0.1

            # 大小号评分
            if num > 8:  # 大号
                big_count = sum(1 for x in blue_numbers[:10] if x > 8)
                if big_count > 5:
                    pattern_score -= 0.1
                else:
                    pattern_score += 0.1
            else:  # 小号
                small_count = sum(1 for x in blue_numbers[:10] if x <= 8)
                if small_count > 5:
                    pattern_score -= 0.1
                else:
                    pattern_score += 0.1

            # 质数评分
            primes = {2, 3, 5, 7, 11, 13}
            if num in primes:
                prime_count = sum(1 for x in blue_numbers[:10] if x in primes)
                if prime_count > 3:
                    pattern_score -= 0.05
                else:
                    pattern_score += 0.05

            scores[num] = max(0.1, min(1.0, pattern_score))  # 限制在[0.1, 1.0]范围内

        return scores

    def _select_blue_simple(self, blue_analysis: Dict) -> int:
        """简单频率选择方法"""
        frequency_scores = blue_analysis.get('frequency_scores', {})
        if not frequency_scores:
            return np.random.randint(1, 17)

        # 直接基于频率评分选择
        numbers = list(frequency_scores.keys())
        probabilities = list(frequency_scores.values())

        # 归一化概率
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
            return int(np.random.choice(numbers, p=probabilities))
        else:
            return np.random.randint(1, 17)

    def _select_blue_enhanced(self, blue_analysis: Dict) -> int:
        """增强多因子选择方法"""
        config = self.blue_algorithm_config
        weights = config['weights']

        # 获取各种评分
        frequency_scores = blue_analysis.get('frequency_scores', {})
        missing_scores = blue_analysis.get('missing_scores', {})
        trend_scores = blue_analysis.get('trend_scores', {})
        pattern_scores = blue_analysis.get('pattern_scores', {})

        if not frequency_scores:
            return np.random.randint(1, 17)

        # 计算综合评分
        final_scores = {}
        for num in range(1, 17):
            final_score = (
                weights['frequency'] * frequency_scores.get(num, 0.5) +
                weights['missing'] * missing_scores.get(num, 0.5) +
                weights['trend'] * trend_scores.get(num, 0.5) +
                weights['pattern'] * pattern_scores.get(num, 0.5) +
                weights['random'] * np.random.random()  # 随机性因子
            )
            final_scores[num] = final_score

        # 转换为概率分布
        scores = list(final_scores.values())
        min_score = min(scores)
        # 调整分数，确保都是正数
        adjusted_scores = [s - min_score + 0.1 for s in scores]

        # 归一化为概率
        total_score = sum(adjusted_scores)
        probabilities = [s / total_score for s in adjusted_scores]

        # 按概率选择
        return int(np.random.choice(list(range(1, 17)), p=probabilities))

    def _select_blue_ensemble(self, blue_analysis: Dict) -> int:
        """集成选择方法 - 结合多种策略"""
        # 获取不同方法的预测结果
        predictions = []

        # 方法1：简单频率
        try:
            pred1 = self._select_blue_simple(blue_analysis)
            predictions.append(('frequency', pred1, 0.3))
        except:
            pass

        # 方法2：增强多因子
        try:
            pred2 = self._select_blue_enhanced(blue_analysis)
            predictions.append(('enhanced', pred2, 0.4))
        except:
            pass

        # 方法3：遗漏优先
        try:
            missing_scores = blue_analysis.get('missing_scores', {})
            if missing_scores:
                best_missing = max(missing_scores.items(), key=lambda x: x[1])
                predictions.append(('missing', best_missing[0], 0.2))
        except:
            pass

        # 方法4：随机选择
        predictions.append(('random', np.random.randint(1, 17), 0.1))

        if not predictions:
            return np.random.randint(1, 17)

        # 加权选择最终结果
        methods, numbers, weights = zip(*predictions)
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # 按权重随机选择一个方法的结果
        selected_idx = np.random.choice(len(predictions), p=normalized_weights)
        return predictions[selected_idx][1]

    def get_blue_algorithm_info(self) -> Dict:
        """获取蓝球算法配置信息"""
        return {
            'current_method': self.blue_algorithm_config['method'],
            'weights': self.blue_algorithm_config['weights'].copy(),
            'analysis_periods': self.blue_algorithm_config['analysis_periods'],
            'available_methods': ['simple', 'enhanced', 'ensemble'],
            'description': {
                'simple': '基于历史频率的简单概率选择',
                'enhanced': '多因子加权模型（频率+遗漏+趋势+模式+随机）',
                'ensemble': '集成多种策略的综合选择方法'
            }
        }

    def set_blue_algorithm_config(self, method: str = None, weights: Dict = None, analysis_periods: int = None):
        """设置蓝球算法配置"""
        if method and method in ['simple', 'enhanced', 'ensemble']:
            self.blue_algorithm_config['method'] = method

        if weights:
            # 验证权重总和
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) < 0.01:  # 允许小的误差
                self.blue_algorithm_config['weights'].update(weights)
            else:
                print(f"警告：权重总和为 {total_weight}，应该接近1.0")

        if analysis_periods and analysis_periods > 0:
            self.blue_algorithm_config['analysis_periods'] = analysis_periods
