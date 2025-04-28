import random
from typing import List
from .base import NumberGenerator
from ..models import LotteryNumber, DLTNumber, SSQNumber

class RandomGenerator(NumberGenerator):
    """随机号码生成器"""
    
    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成随机号码"""
        numbers = []
        for _ in range(count):
            if self.lottery_type == 'dlt':
                front = sorted(random.sample(
                    range(self.config['front_range'][0], 
                          self.config['front_range'][1] + 1),
                    self.config['front_count']
                ))
                back = sorted(random.sample(
                    range(self.config['back_range'][0],
                          self.config['back_range'][1] + 1),
                    self.config['back_count']
                ))
                numbers.append(DLTNumber(front=front, back=back))
            else:
                red = sorted(random.sample(
                    range(self.config['red_range'][0],
                          self.config['red_range'][1] + 1),
                    self.config['red_count']
                ))
                blue = random.randint(
                    self.config['blue_range'][0],
                    self.config['blue_range'][1]
                )
                numbers.append(SSQNumber(red=red, blue=blue))
        return numbers
