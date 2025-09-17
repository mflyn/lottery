import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Union
from collections import Counter
import random
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
            blue_number = self._select_blue_number(hot_cold_numbers['blue'])
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
            return {'red': red_pools, 'blue': {'frequencies': blue_freq}}
        
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
        """选择SSQ蓝球号码"""
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
