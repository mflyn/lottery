import random
from typing import List, Optional
from .base import NumberGenerator
from ..models import LotteryNumber, DLTNumber, SSQNumber

class RandomGenerator(NumberGenerator):
    """随机号码生成器"""
    
    def __init__(self, lottery_type: str):
        """初始化随机生成器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
        """
        super().__init__(lottery_type)
    
    def generate(self, count: int = 1, **kwargs) -> List[LotteryNumber]:
        """生成随机号码
        
        Args:
            count: 生成的号码组数
            **kwargs: 其他参数
            
        Returns:
            生成的号码列表
        """
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
    
    def generate_hot_cold(self, count: int = 1, hot_ratio: float = 0.4, cold_ratio: float = 0.2) -> List[LotteryNumber]:
        """生成热冷号组合
        
        Args:
            count: 生成的号码组数
            hot_ratio: 热号比例
            cold_ratio: 冷号比例
            
        Returns:
            生成的号码列表
        """
        numbers = []
        
        for _ in range(count):
            if self.lottery_type == 'ssq':
                # 简化的热冷号生成（实际应该基于历史数据）
                hot_numbers = list(range(1, 12))  # 假设1-11为热号
                cold_numbers = list(range(23, 34))  # 假设23-33为冷号
                normal_numbers = list(range(12, 23))  # 中间号码
                
                hot_count = int(6 * hot_ratio)
                cold_count = int(6 * cold_ratio)
                normal_count = 6 - hot_count - cold_count
                
                selected_numbers = []
                selected_numbers.extend(random.sample(hot_numbers, min(hot_count, len(hot_numbers))))
                selected_numbers.extend(random.sample(cold_numbers, min(cold_count, len(cold_numbers))))
                
                remaining_count = 6 - len(selected_numbers)
                if remaining_count > 0:
                    available_numbers = [n for n in range(1, 34) if n not in selected_numbers]
                    selected_numbers.extend(random.sample(available_numbers, remaining_count))
                
                red = sorted(selected_numbers[:6])
                blue = random.randint(1, 16)
                numbers.append(SSQNumber(red=red, blue=blue))
                
            elif self.lottery_type == 'dlt':
                # 大乐透热冷号生成
                hot_front = list(range(1, 13))
                cold_front = list(range(24, 36))
                normal_front = list(range(13, 24))
                
                hot_count = int(5 * hot_ratio)
                cold_count = int(5 * cold_ratio)
                
                selected_front = []
                selected_front.extend(random.sample(hot_front, min(hot_count, len(hot_front))))
                selected_front.extend(random.sample(cold_front, min(cold_count, len(cold_front))))
                
                remaining_count = 5 - len(selected_front)
                if remaining_count > 0:
                    available_numbers = [n for n in range(1, 36) if n not in selected_front]
                    selected_front.extend(random.sample(available_numbers, remaining_count))
                
                front = sorted(selected_front[:5])
                back = sorted(random.sample(range(1, 13), 2))
                numbers.append(DLTNumber(front=front, back=back))
        
        return numbers
    
    def generate_consecutive(self, count: int = 1, max_consecutive: int = 2) -> List[LotteryNumber]:
        """生成包含连号的号码
        
        Args:
            count: 生成的号码组数
            max_consecutive: 最大连号数量
            
        Returns:
            生成的号码列表
        """
        numbers = []
        
        for _ in range(count):
            if self.lottery_type == 'ssq':
                # 生成连号
                consecutive_count = random.randint(1, min(max_consecutive, 3))
                start_num = random.randint(1, 33 - consecutive_count + 1)
                consecutive_nums = list(range(start_num, start_num + consecutive_count))
                
                # 生成其余号码
                remaining_count = 6 - consecutive_count
                available_numbers = [n for n in range(1, 34) if n not in consecutive_nums]
                other_nums = random.sample(available_numbers, remaining_count)
                
                red = sorted(consecutive_nums + other_nums)
                blue = random.randint(1, 16)
                numbers.append(SSQNumber(red=red, blue=blue))
                
            elif self.lottery_type == 'dlt':
                # 前区连号
                consecutive_count = random.randint(1, min(max_consecutive, 3))
                start_num = random.randint(1, 35 - consecutive_count + 1)
                consecutive_nums = list(range(start_num, start_num + consecutive_count))
                
                remaining_count = 5 - consecutive_count
                available_numbers = [n for n in range(1, 36) if n not in consecutive_nums]
                other_nums = random.sample(available_numbers, remaining_count)
                
                front = sorted(consecutive_nums + other_nums)
                back = sorted(random.sample(range(1, 13), 2))
                numbers.append(DLTNumber(front=front, back=back))
        
        return numbers
    
    def generate_by_sum_range(self, count: int = 1, min_sum: Optional[int] = None, max_sum: Optional[int] = None) -> List[LotteryNumber]:
        """根据和值范围生成号码
        
        Args:
            count: 生成的号码组数
            min_sum: 最小和值
            max_sum: 最大和值
            
        Returns:
            生成的号码列表
        """
        numbers = []
        
        # 设置默认和值范围
        if self.lottery_type == 'ssq':
            min_sum = min_sum or 60
            max_sum = max_sum or 140
        elif self.lottery_type == 'dlt':
            min_sum = min_sum or 50
            max_sum = max_sum or 120
        
        attempts = 0
        max_attempts = count * 100  # 避免无限循环
        
        while len(numbers) < count and attempts < max_attempts:
            attempts += 1
            
            if self.lottery_type == 'ssq':
                red = sorted(random.sample(range(1, 34), 6))
                red_sum = sum(red)
                
                if min_sum <= red_sum <= max_sum:
                    blue = random.randint(1, 16)
                    numbers.append(SSQNumber(red=red, blue=blue))
                    
            elif self.lottery_type == 'dlt':
                front = sorted(random.sample(range(1, 36), 5))
                front_sum = sum(front)
                
                if min_sum <= front_sum <= max_sum:
                    back = sorted(random.sample(range(1, 13), 2))
                    numbers.append(DLTNumber(front=front, back=back))
        
        if len(numbers) < count:
            self.logger.warning(f"只生成了{len(numbers)}组符合和值范围的号码，目标是{count}组")
        
        return numbers
    
    def add_strategy(self, name: str, strategy):
        """添加自定义策略
        
        Args:
            name: 策略名称
            strategy: 策略对象
        """
        self.strategies[name] = strategy
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的生成策略
        
        Returns:
            策略名称列表
        """
        return list(self.strategies.keys())
