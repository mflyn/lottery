from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models import LotteryNumber, DLTNumber, SSQNumber

class NumberGenerator(ABC):
    """号码生成器基类"""
    
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type
        self.config = self._get_config()
        
    @abstractmethod
    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成号码"""
        pass
    
    def _get_config(self) -> Dict:
        """获取配置"""
        configs = {
            'dlt': {
                'front_range': (1, 35),
                'front_count': 5,
                'back_range': (1, 12),
                'back_count': 2
            },
            'ssq': {
                'red_range': (1, 33),
                'red_count': 6,
                'blue_range': (1, 16),
                'blue_count': 1
            }
        }
        return configs.get(self.lottery_type, {})