from typing import List, Dict, Union
import random
import numpy as np
from .number_evaluator import NumberEvaluator
from ..models.lottery_types import DLTNumber, SSQNumber

class EnhancedNumberGenerator:
    """增强的号码生成器"""
    
    def __init__(self, lottery_type: str, history_data: List[Dict]):
        self.lottery_type = lottery_type
        self.history_data = history_data
        self.evaluator = NumberEvaluator(history_data, lottery_type)
        
    def generate_with_strategy(self, 
                             strategy: str, 
                             count: int,
                             history_weight: float = 0.5,
                             pattern_weight: float = 0.3) -> List[Union[DLTNumber, SSQNumber]]:
        """使用指定策略生成号码"""
        strategies = {
            'smart': self._generate_smart_numbers,
            'pattern': self._generate_pattern_based_numbers,
            'frequency': self._generate_frequency_based_numbers,
            'hybrid': self._generate_hybrid_numbers,
            'evolutionary': self._generate_evolutionary_numbers
        }
        
        generator = strategies.get(strategy, self._generate_hybrid_numbers)
        candidates = generator(count * 3)  # 生成更多候选号码
        
        # 评估并筛选最佳号码
        scored_numbers = [
            (num, self.evaluator.evaluate_number(num))
            for num in candidates
        ]
        scored_numbers.sort(key=lambda x: x[1].score, reverse=True)
        
        return [num for num, _ in scored_numbers[:count]]
    
    def _generate_balanced_numbers(self, count: int) -> List[Union[DLTNumber, SSQNumber]]:
        """生成平衡性好的号码"""
        numbers = []
        for _ in range(count):
            if self.lottery_type == 'dlt':
                front = self._generate_balanced_sequence(5, 35)
                back = self._generate_balanced_sequence(2, 12)
                numbers.append(DLTNumber(front=front, back=back))
            else:
                red = self._generate_balanced_sequence(6, 33)
                blue = random.randint(1, 16)
                numbers.append(SSQNumber(red=red, blue=blue))
        return numbers
    
    def _generate_smart_numbers(self, count: int) -> List[Union[DLTNumber, SSQNumber]]:
        """智能生成号码"""
        # 结合多种策略的优点
        numbers = []
        generators = [
            (self._generate_pattern_based_numbers, 0.4),
            (self._generate_frequency_based_numbers, 0.3),
            (self._generate_balanced_numbers, 0.3)
        ]
        
        for _ in range(count):
            generator, weight = random.choices(
                generators,
                weights=[w for _, w in generators]
            )[0]
            numbers.extend(generator(1))
            
        return numbers
    
    def _generate_frequency_based_numbers(self, count: int) -> List[Union[DLTNumber, SSQNumber]]:
        """基于号码频率生成"""
        frequency_map = self._analyze_number_frequency()
        numbers = []
        
        for _ in range(count):
            if self.lottery_type == 'dlt':
                front = self._select_by_frequency(frequency_map['front'], 5)
                back = self._select_by_frequency(frequency_map['back'], 2)
                numbers.append(DLTNumber(front=front, back=back))
            else:
                red = self._select_by_frequency(frequency_map['red'], 6)
                blue = self._select_by_frequency(frequency_map['blue'], 1)[0]
                numbers.append(SSQNumber(red=red, blue=blue))
                
        return numbers
    
    def _generate_pattern_based_numbers(self, count: int) -> List[Union[DLTNumber, SSQNumber]]:
        """基于历史模式生成"""
        patterns = self._analyze_winning_patterns()
        numbers = []
        
        for _ in range(count):
            pattern = random.choice(patterns)
            if self.lottery_type == 'dlt':
                front = self._apply_pattern(pattern['front'], 35, 5)
                back = self._apply_pattern(pattern['back'], 12, 2)
                numbers.append(DLTNumber(front=front, back=back))
            else:
                red = self._apply_pattern(pattern['red'], 33, 6)
                blue = random.randint(1, 16)
                numbers.append(SSQNumber(red=red, blue=blue))
                
        return numbers
    
    def _generate_evolutionary_numbers(self, count: int) -> List[Union[DLTNumber, SSQNumber]]:
        """使用遗传算法生成号码"""
        population_size = count * 5
        generations = 50
        population = self._initialize_population(population_size)
        
        for _ in range(generations):
            fitness_scores = [
                self.evaluator.evaluate_number(num).score 
                for num in population
            ]
            
            selected = self._select_best_individuals(
                population, 
                fitness_scores, 
                int(population_size * 0.4)
            )
            
            new_population = []
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(selected, 2)
                child = self._crossover(parent1, parent2)
                if random.random() < 0.1:  # 10%的变异概率
                    child = self._mutate(child)
                new_population.append(child)
                
            population = new_population
            
        # 返回最优解
        return sorted(
            population,
            key=lambda x: self.evaluator.evaluate_number(x).score,
            reverse=True
        )[:count]
