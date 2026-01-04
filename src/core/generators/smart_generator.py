import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Union, Optional
from collections import Counter
import random
import math
from .random_generator import RandomGenerator
from ..models import LotteryNumber, SSQNumber, DLTNumber
from ..ranking import rank_and_select_best, rank_and_select_best_dlt
from ..data_manager import LotteryDataManager
from .anti_popular import PopularityDetector, CorrelationChecker, SequenceAnalyzer
from ..filters import HistoryDuplicateFilter

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

        # 历史重复过滤配置
        self.history_filter_config = {
            'enabled': True,                # 是否启用历史过滤
            'check_periods': 100,           # 检查最近N期
            'ssq': {
                'max_red_overlap': 4,       # 红球最多重复4个
                'recent_strict_periods': 10, # 最近10期更严格
                'recent_max_overlap': 3,    # 最近10期最多重复3个
            },
            'dlt': {
                'max_front_overlap': 3,     # 前区最多重复3个
                'recent_strict_periods': 10,
                'recent_max_overlap': 2,
            }
        }

        # 初始化历史过滤器
        self.history_filter = HistoryDuplicateFilter(
            lottery_type=lottery_type,
            config=self.history_filter_config.get(lottery_type, {})
        )

        # 去热门算法配置
        self.anti_popular_config = {
            'enabled': False,  # 是否启用去热门模式
            'mode': 'moderate',  # 'strict'(严格), 'moderate'(适中), 'light'(轻度)

            # SSQ配置
            'ssq': {
                'max_score': 2,              # 热门打分阈值（越小越严格）
                'max_run': 2,                # 最大连号长度
                'max_same_last_digit': 2,    # 同尾数最大计数
                'odd_bounds': (2, 4),        # 奇数个数范围
                'sum_bounds': (70, 140),     # 和值范围
                'max_red_overlap': 2,        # 多注间红球最大重叠
                'max_blue_dup': 1,           # 蓝球重复次数限制
                'tries_per_ticket': 60       # 每注最大尝试次数
            },

            # DLT配置
            'dlt': {
                'max_score': 2,
                'max_run': 2,
                'max_same_last_digit': 2,
                'odd_bounds': (1, 4),
                'sum_bounds': (60, 120),
                'max_front_overlap': 2,
                'max_back_overlap': 1,
                'avoid_back_consecutive': False,
                'tries_per_ticket': 60
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

    def generate_recommended(self, count: int = 1,
                              enable_history_filter: Optional[bool] = None) -> List[LotteryNumber]:
        """生成精英推荐号码, 每一注都是优中选优的结果.

        Args:
            count: 生成数量
            enable_history_filter: 是否启用历史过滤（None则使用默认配置）
        """
        conf = self.config[self.lottery_type]
        history_data = self.data_manager.get_history_data(self.lottery_type)
        if history_data is None or history_data.empty or len(history_data) < conf['analysis_periods']:
            return self.random_generator.generate(count)

        hot_cold_numbers = self._analyze_hot_cold_numbers(history_data)

        recipes = conf.get('recipes') or conf.get('front_recipes')
        random.shuffle(recipes)

        ranking_function = rank_and_select_best if self.lottery_type == 'ssq' else rank_and_select_best_dlt

        # 判断是否启用历史过滤
        use_history_filter = enable_history_filter if enable_history_filter is not None else self.history_filter_config['enabled']

        elite_numbers = []
        filtered_count = 0  # 统计被过滤的数量
        retry_count = 0  # 统计重试次数

        # 获取用户设置的最大重复阈值
        if self.lottery_type == 'ssq':
            max_overlap_threshold = self.history_filter_config.get('ssq', {}).get('max_red_overlap', 4)
        else:
            max_overlap_threshold = self.history_filter_config.get('dlt', {}).get('max_front_overlap', 3)

        for i in range(count):
            print(f"正在为[{self.lottery_type.upper()}]进行第 {i+1}/{count} 注精英号码的选拔...")

            # 根据阈值严格程度动态调整候选数量
            # 阈值越低，需要生成越多候选
            if use_history_filter:
                strictness_factor = max(1, 5 - max_overlap_threshold)  # 阈值2->3倍, 阈值3->2倍, 阈值4->1倍
                batch_multiplier = 3 * strictness_factor
            else:
                batch_multiplier = 1

            candidates = []
            batch_size = conf['batch_size_per_elite'] * batch_multiplier
            max_retries = 5  # 最大重试次数

            for attempt in range(max_retries):
                # 生成候选号码
                for j in range(batch_size):
                    recipe = recipes[j % len(recipes)]
                    candidate = self._generate_one_candidate(hot_cold_numbers, recipe)
                    candidates.append(candidate)

                # 先通过 ranking 筛选
                ranked_candidates = self._rank_candidates(candidates, ranking_function)

                # 再通过历史过滤
                if use_history_filter:
                    elite_number = self._select_with_history_filter(
                        ranked_candidates, history_data, elite_numbers
                    )
                    if elite_number is not None:
                        break  # 找到合格的号码，跳出重试循环

                    # 检查是否还有机会找到更好的
                    best_overlap = self._get_best_overlap(ranked_candidates, history_data)
                    if best_overlap <= max_overlap_threshold:
                        # 有满足阈值的候选但被其他规则拒绝了，使用它
                        elite_number = self._select_lowest_overlap(ranked_candidates, history_data)
                        break

                    retry_count += 1
                    print(f"  ⚠️ 第{attempt+1}次尝试未找到满足阈值({max_overlap_threshold})的号码，继续生成更多候选...")
                    candidates = []  # 清空，重新生成
                else:
                    elite_number = ranked_candidates[0] if ranked_candidates else random.choice(candidates)
                    break
            else:
                # 达到最大重试次数仍未找到，选择最佳的（记录警告）
                elite_number = self._select_lowest_overlap(ranked_candidates, history_data)
                best_overlap = self._get_best_overlap(ranked_candidates, history_data)
                if best_overlap > max_overlap_threshold:
                    print(f"  ⚠️ 警告：无法找到满足阈值({max_overlap_threshold})的号码，选择重复度最低({best_overlap})的候选")
                    filtered_count += 1

            if elite_number:
                elite_numbers.append(elite_number)
            else:
                elite_numbers.append(random.choice(candidates) if candidates else self._generate_one_candidate(hot_cold_numbers, recipes[0]))

        if filtered_count > 0:
            print(f"📊 历史过滤统计: {filtered_count}/{count} 注无法满足设定阈值({max_overlap_threshold})")
        if retry_count > 0:
            print(f"📊 重试统计: 共进行了 {retry_count} 次额外重试")

        return elite_numbers

    def _rank_candidates(self, candidates: List[Union[SSQNumber, DLTNumber]],
                         ranking_function) -> List[Union[SSQNumber, DLTNumber]]:
        """对候选号码进行排名"""
        # 使用 ranking_function 对候选排名，返回排序后的列表
        scored = []
        for c in candidates:
            try:
                # ranking_function 返回最佳的一个，我们需要对所有评分
                scored.append((c, getattr(c, 'score', 0)))
            except:
                scored.append((c, 0))

        # 按分数降序排列
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]

    def _select_with_history_filter(self, candidates: List[Union[SSQNumber, DLTNumber]],
                                    history_data: pd.DataFrame,
                                    already_selected: List[Union[SSQNumber, DLTNumber]]) -> Optional[Union[SSQNumber, DLTNumber]]:
        """使用历史过滤选择号码"""
        check_periods = self.history_filter_config.get('check_periods', 100)

        for candidate in candidates:
            # 检查与历史数据的重复
            result = self.history_filter.filter(candidate, history_data, check_periods)

            if result.is_valid:
                # 额外检查：与已选号码的重复度
                if self._check_internal_overlap(candidate, already_selected):
                    return candidate

        return None

    def _check_internal_overlap(self, candidate: Union[SSQNumber, DLTNumber],
                                 already_selected: List[Union[SSQNumber, DLTNumber]]) -> bool:
        """检查与已选号码的重复度"""
        if not already_selected:
            return True

        max_internal_overlap = 3  # 允许的最大内部重复

        for selected in already_selected:
            if self.lottery_type == 'ssq':
                overlap = len(set(candidate.red) & set(selected.red))
            else:
                overlap = len(set(candidate.front) & set(selected.front))

            if overlap > max_internal_overlap:
                return False

        return True

    def _select_lowest_overlap(self, candidates: List[Union[SSQNumber, DLTNumber]],
                               history_data: pd.DataFrame) -> Optional[Union[SSQNumber, DLTNumber]]:
        """选择重复度最低的候选"""
        check_periods = self.history_filter_config.get('check_periods', 100)

        results = self.history_filter.filter_batch(candidates, history_data, check_periods)

        if results:
            # 返回重复度最低的（已按 overlap_score 排序）
            return results[0][0]

        return candidates[0] if candidates else None

    def _get_best_overlap(self, candidates: List[Union[SSQNumber, DLTNumber]],
                          history_data: pd.DataFrame) -> int:
        """获取候选中最低的重复数"""
        check_periods = self.history_filter_config.get('check_periods', 100)

        results = self.history_filter.filter_batch(candidates, history_data, check_periods)

        if results:
            # 返回最低的 max_overlap
            return results[0][1].max_overlap

        return 999  # 无候选时返回极大值

    def set_history_filter_enabled(self, enabled: bool):
        """设置是否启用历史过滤"""
        self.history_filter_config['enabled'] = enabled

    def set_history_filter_config(self, **kwargs):
        """设置历史过滤配置"""
        # 更新顶层配置
        for key in ['enabled', 'check_periods']:
            if key in kwargs:
                self.history_filter_config[key] = kwargs[key]

        # 更新彩种特定配置
        lottery_config = self.history_filter_config.get(self.lottery_type, {})
        for key in ['max_red_overlap', 'max_front_overlap', 'recent_strict_periods', 'recent_max_overlap']:
            if key in kwargs:
                lottery_config[key] = kwargs[key]

        # 自动同步：如果设置了最大重复，近期严格阈值应更低
        if 'max_red_overlap' in kwargs and 'recent_max_overlap' not in kwargs:
            # 近期阈值 = 最大阈值 - 1，但至少为1
            lottery_config['recent_max_overlap'] = max(1, kwargs['max_red_overlap'] - 1)
        if 'max_front_overlap' in kwargs and 'recent_max_overlap' not in kwargs:
            lottery_config['recent_max_overlap'] = max(1, kwargs['max_front_overlap'] - 1)

        # 同步到过滤器
        self.history_filter.update_config(**lottery_config)

        print(f"📋 历史过滤配置已更新: check_periods={self.history_filter_config.get('check_periods')}, "
              f"max_overlap={lottery_config.get('max_red_overlap') or lottery_config.get('max_front_overlap')}, "
              f"recent_max={lottery_config.get('recent_max_overlap')}")
    
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

    # ==================== 去热门算法相关方法 ====================

    def set_anti_popular_config(self, enabled: bool = True, mode: str = 'moderate', **kwargs):
        """
        配置去热门算法

        Args:
            enabled: 是否启用去热门模式
            mode: 预设模式 'strict'(严格), 'moderate'(适中), 'light'(轻度)
            **kwargs: 自定义配置参数

        Examples:
            # 启用严格模式
            generator.set_anti_popular_config(enabled=True, mode='strict')

            # 自定义配置
            generator.set_anti_popular_config(
                enabled=True,
                mode='moderate',
                max_score=1,
                max_run=1
            )
        """
        self.anti_popular_config['enabled'] = enabled
        self.anti_popular_config['mode'] = mode

        # 根据模式预设参数
        if mode == 'strict':
            # 严格模式：最大程度避免热门
            if self.lottery_type == 'ssq':
                self.anti_popular_config['ssq'].update({
                    'max_score': 1,
                    'max_run': 1,
                    'max_same_last_digit': 2,
                    'max_red_overlap': 1,
                    'max_blue_dup': 1,
                    'tries_per_ticket': 80
                })
            elif self.lottery_type == 'dlt':
                self.anti_popular_config['dlt'].update({
                    'max_score': 1,
                    'max_run': 1,
                    'max_same_last_digit': 2,
                    'max_front_overlap': 1,
                    'max_back_overlap': 0,
                    'tries_per_ticket': 80
                })

        elif mode == 'moderate':
            # 适中模式：平衡热门和多样性（默认值）
            if self.lottery_type == 'ssq':
                self.anti_popular_config['ssq'].update({
                    'max_score': 2,
                    'max_run': 2,
                    'max_same_last_digit': 2,
                    'max_red_overlap': 2,
                    'max_blue_dup': 1,
                    'tries_per_ticket': 60
                })
            elif self.lottery_type == 'dlt':
                self.anti_popular_config['dlt'].update({
                    'max_score': 2,
                    'max_run': 2,
                    'max_same_last_digit': 2,
                    'max_front_overlap': 2,
                    'max_back_overlap': 1,
                    'tries_per_ticket': 60
                })

        elif mode == 'light':
            # 轻度模式：轻微避免热门
            if self.lottery_type == 'ssq':
                self.anti_popular_config['ssq'].update({
                    'max_score': 3,
                    'max_run': 3,
                    'max_same_last_digit': 3,
                    'max_red_overlap': 3,
                    'max_blue_dup': 2,
                    'tries_per_ticket': 40
                })
            elif self.lottery_type == 'dlt':
                self.anti_popular_config['dlt'].update({
                    'max_score': 3,
                    'max_run': 3,
                    'max_same_last_digit': 2,
                    'max_front_overlap': 3,
                    'max_back_overlap': 1,
                    'tries_per_ticket': 40
                })

        # 应用自定义参数
        lottery_config = self.anti_popular_config.get(self.lottery_type, {})
        for key, value in kwargs.items():
            if key in lottery_config:
                lottery_config[key] = value

    def get_anti_popular_config(self) -> Dict:
        """获取去热门配置信息"""
        return {
            'enabled': self.anti_popular_config['enabled'],
            'mode': self.anti_popular_config['mode'],
            'lottery_config': self.anti_popular_config.get(self.lottery_type, {}).copy(),
            'available_modes': ['strict', 'moderate', 'light'],
            'description': {
                'strict': '严格模式 - 最大程度避免热门模式，号码最独特',
                'moderate': '适中模式 - 平衡热门规避和号码多样性',
                'light': '轻度模式 - 轻微避免热门，保持较高灵活性'
            }
        }

    def generate_anti_popular(self, count: int = 1) -> List[LotteryNumber]:
        """
        生成去热门号码

        Args:
            count: 生成数量

        Returns:
            号码列表

        Examples:
            generator = SmartNumberGenerator('ssq')
            generator.set_anti_popular_config(enabled=True, mode='moderate')
            numbers = generator.generate_anti_popular(10)
        """
        if not self.anti_popular_config['enabled']:
            print("提示：去热门模式未启用，使用统计优选算法")
            return self.generate_recommended(count)

        if self.lottery_type == 'ssq':
            return self._generate_anti_popular_ssq(count)
        elif self.lottery_type == 'dlt':
            return self._generate_anti_popular_dlt(count)
        else:
            return self.generate_recommended(count)

    def _generate_anti_popular_ssq(self, count: int) -> List[SSQNumber]:
        """生成去热门SSQ号码"""
        config = self.anti_popular_config['ssq']
        picks = []
        blue_usage = Counter()

        print(f"🎯 使用去热门模式生成 {count} 注双色球号码（{self.anti_popular_config['mode']}模式）")

        for i in range(count):
            best_candidate = None
            best_score = float('inf')

            for attempt in range(config['tries_per_ticket']):
                # 1. 生成候选号码
                red = sorted(random.sample(range(1, 34), 6))
                blue = random.randint(1, 16)

                # 2. 硬性规则检查
                if PopularityDetector.check_hard_reject_ssq(red, blue, config):
                    continue

                # 3. 相关性检查
                if not CorrelationChecker.check_ssq_correlation(red, blue, picks, config):
                    continue

                # 4. 蓝球使用次数检查
                if not CorrelationChecker.check_blue_usage(blue, blue_usage, config):
                    continue

                # 5. 计算热门度分数
                score = PopularityDetector.calculate_ssq_score(red, blue, config['sum_bounds'])

                # 6. 如果满足阈值，直接接受
                if score <= config['max_score']:
                    picks.append((red, blue, score))
                    blue_usage[blue] += 1
                    print(f"  [{i+1}/{count}] 红球: {' '.join(f'{x:02d}' for x in red)} | 蓝球: {blue:02d} | 热门度: {score}")
                    break

                # 7. 记录最佳候选
                if score < best_score:
                    best_candidate = (red, blue, score)
                    best_score = score
            else:
                # 达到最大尝试次数，接受最佳候选
                if best_candidate:
                    red, blue, score = best_candidate
                    picks.append(best_candidate)
                    blue_usage[blue] += 1
                    print(f"  [{i+1}/{count}] 红球: {' '.join(f'{x:02d}' for x in red)} | 蓝球: {blue:02d} | 热门度: {score} (降级接受)")
                else:
                    # 极端兜底
                    red = sorted(random.sample(range(1, 34), 6))
                    blue = random.randint(1, 16)
                    picks.append((red, blue, 99))
                    blue_usage[blue] += 1
                    print(f"  [{i+1}/{count}] 红球: {' '.join(f'{x:02d}' for x in red)} | 蓝球: {blue:02d} | 热门度: 99 (兜底)")

        # 生成报告
        report = CorrelationChecker.get_correlation_report(picks, 'ssq')
        print(f"\n📊 生成报告：")
        print(f"  多样性分数: {report['diversity_score']:.2f}")
        print(f"  独立蓝球数: {report['unique_blues']}/{count}")
        print(f"  平均红球重叠: {report.get('avg_red_overlap', 0):.2f}")

        # 转换为SSQNumber对象
        return [SSQNumber(red=red, blue=blue) for red, blue, _ in picks]

    def _generate_anti_popular_dlt(self, count: int) -> List[DLTNumber]:
        """生成去热门DLT号码"""
        config = self.anti_popular_config['dlt']
        picks = []

        print(f"🎯 使用去热门模式生成 {count} 注大乐透号码（{self.anti_popular_config['mode']}模式）")

        for i in range(count):
            best_candidate = None
            best_score = float('inf')

            for attempt in range(config['tries_per_ticket']):
                # 1. 生成候选号码
                front = sorted(random.sample(range(1, 36), 5))
                back = sorted(random.sample(range(1, 13), 2))

                # 2. 硬性规则检查
                if PopularityDetector.check_hard_reject_dlt(front, back, config):
                    continue

                # 3. 相关性检查
                if not CorrelationChecker.check_dlt_correlation(front, back, picks, config):
                    continue

                # 4. 计算热门度分数
                score = PopularityDetector.calculate_dlt_score(front, back)

                # 5. 如果满足阈值，直接接受
                if score <= config['max_score']:
                    picks.append((front, back, score))
                    print(f"  [{i+1}/{count}] 前区: {' '.join(f'{x:02d}' for x in front)} | 后区: {' '.join(f'{x:02d}' for x in back)} | 热门度: {score}")
                    break

                # 6. 记录最佳候选
                if score < best_score:
                    best_candidate = (front, back, score)
                    best_score = score
            else:
                # 达到最大尝试次数，接受最佳候选
                if best_candidate:
                    front, back, score = best_candidate
                    picks.append(best_candidate)
                    print(f"  [{i+1}/{count}] 前区: {' '.join(f'{x:02d}' for x in front)} | 后区: {' '.join(f'{x:02d}' for x in back)} | 热门度: {score} (降级接受)")
                else:
                    # 极端兜底
                    front = sorted(random.sample(range(1, 36), 5))
                    back = sorted(random.sample(range(1, 13), 2))
                    picks.append((front, back, 99))
                    print(f"  [{i+1}/{count}] 前区: {' '.join(f'{x:02d}' for x in front)} | 后区: {' '.join(f'{x:02d}' for x in back)} | 热门度: 99 (兜底)")

        # 生成报告
        report = CorrelationChecker.get_correlation_report(picks, 'dlt')
        print(f"\n📊 生成报告：")
        print(f"  多样性分数: {report['diversity_score']:.2f}")
        print(f"  平均前区重叠: {report.get('avg_front_overlap', 0):.2f}")
        print(f"  平均后区重叠: {report.get('avg_back_overlap', 0):.2f}")

        # 转换为DLTNumber对象
        return [DLTNumber(front=front, back=back) for front, back, _ in picks]

    def generate_hybrid(self, count: int = 1, anti_popular_ratio: float = 0.5) -> List[LotteryNumber]:
        """
        混合生成模式：结合统计优选和去热门

        Args:
            count: 生成总数量
            anti_popular_ratio: 去热门号码的比例（0-1）

        Returns:
            号码列表

        Examples:
            # 50%去热门 + 50%统计优选
            generator.set_anti_popular_config(enabled=True, mode='moderate')
            numbers = generator.generate_hybrid(10, anti_popular_ratio=0.5)
        """
        if not self.anti_popular_config['enabled']:
            print("提示：去热门模式未启用，全部使用统计优选算法")
            return self.generate_recommended(count)

        # 计算各模式生成数量
        anti_popular_count = int(count * anti_popular_ratio)
        smart_count = count - anti_popular_count

        print(f"\n🔀 混合模式生成：")
        print(f"  去热门号码: {anti_popular_count} 注")
        print(f"  统计优选号码: {smart_count} 注")
        print(f"  总计: {count} 注\n")

        all_numbers = []

        # 生成去热门号码
        if anti_popular_count > 0:
            print("=" * 60)
            print("第一部分：去热门号码生成")
            print("=" * 60)
            anti_popular_numbers = self.generate_anti_popular(anti_popular_count)
            all_numbers.extend(anti_popular_numbers)

        # 生成统计优选号码
        if smart_count > 0:
            print("\n" + "=" * 60)
            print("第二部分：统计优选号码生成")
            print("=" * 60)
            smart_numbers = self.generate_recommended(smart_count)
            all_numbers.extend(smart_numbers)

        # 打乱顺序
        random.shuffle(all_numbers)

        print("\n" + "=" * 60)
        print("✅ 混合模式生成完成")
        print("=" * 60)

        return all_numbers
