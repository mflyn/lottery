from typing import List, Dict
import numpy as np
from src.core.generators.base_generator import LotteryNumber
from src.core.analyzers import SSQAnalyzer, DLTAnalyzer

class SmartRecommender:
    """智能号码推荐系统"""
    
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type
        self.analyzer = SSQAnalyzer() if lottery_type == 'ssq' else DLTAnalyzer()
        
    def recommend(
        self,
        history_data: List[Dict],
        count: int = 5,
        weights: Dict[str, float] = None
    ) -> List[LotteryNumber]:
        """生成智能推荐号码"""
        if weights is None:
            weights = {
                'frequency': 0.3,
                'missing': 0.3,
                'pattern': 0.2,
                'random': 0.2
            }
            
        # 分析历史数据
        freq_analysis = self.analyzer.analyze_frequency(history_data)
        missing_analysis = self.analyzer.analyze_missing_values(history_data)
        pattern_analysis = self.analyzer.analyze_patterns(history_data)
        
        recommendations = []
        for _ in range(count):
            number = self._generate_smart_number(
                freq_analysis,
                missing_analysis,
                pattern_analysis,
                weights
            )
            recommendations.append(number)
            
        return recommendations
        
    def _generate_smart_number(
        self,
        freq_analysis: Dict,
        missing_analysis: Dict,
        pattern_analysis: Dict,
        weights: Dict[str, float]
    ) -> LotteryNumber:
        """生成单个智能号码"""
        if self.lottery_type == 'ssq':
            red_numbers = self._select_red_numbers(
                freq_analysis,
                missing_analysis,
                pattern_analysis,
                weights
            )
            blue_number = self._select_blue_number(
                freq_analysis,
                missing_analysis,
                weights
            )
            return LotteryNumber(
                type='ssq',
                red=red_numbers,
                blue=blue_number
            )
        else:  # dlt
            front_numbers = self._select_front_numbers(
                freq_analysis,
                missing_analysis,
                pattern_analysis,
                weights
            )
            back_numbers = self._select_back_numbers(
                freq_analysis,
                missing_analysis,
                weights
            )
            return LotteryNumber(
                type='dlt',
                front=front_numbers,
                back=back_numbers
            )