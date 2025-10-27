from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models import LotteryNumber
from ..config_manager import ConfigManager

class NumberGenerator(ABC):
    """号码生成器基类"""

    def __init__(self, lottery_type: str, config_manager: Optional[ConfigManager] = None):
        self.lottery_type = lottery_type
        self.config_manager = config_manager or ConfigManager()
        self.config = self._get_config()

    @abstractmethod
    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成号码"""
        pass

    def _get_config(self) -> Dict:
        """从配置管理器获取配置"""
        if self.lottery_type == 'dlt':
            front_range = self.config_manager.get_lottery_range('dlt', 'front')
            back_range = self.config_manager.get_lottery_range('dlt', 'back')
            return {
                'front_range': front_range,
                'front_count': self.config_manager.get_lottery_count('dlt', 'front'),
                'back_range': back_range,
                'back_count': self.config_manager.get_lottery_count('dlt', 'back')
            }
        elif self.lottery_type == 'ssq':
            red_range = self.config_manager.get_lottery_range('ssq', 'red')
            blue_range = self.config_manager.get_lottery_range('ssq', 'blue')
            return {
                'red_range': red_range,
                'red_count': self.config_manager.get_lottery_count('ssq', 'red'),
                'blue_range': blue_range,
                'blue_count': self.config_manager.get_lottery_count('ssq', 'blue')
            }
        return {}