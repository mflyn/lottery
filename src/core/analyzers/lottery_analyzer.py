from abc import ABC, abstractmethod
from typing import List, Dict

class LotteryAnalyzer(ABC):
    """彩票数据分析器基类"""
    @abstractmethod
    def analyze_frequency(self, history_data: List[Dict], periods: int = 100) -> Dict:
        pass
    @abstractmethod
    def analyze_trends(self, history_data: List[Dict], periods: int = 30) -> Dict:
        pass
