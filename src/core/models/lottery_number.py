from typing import List

class LotteryNumber:
    """彩票号码基类"""
    
    def __init__(self, lottery_type: str):
        """
        Args:
            lottery_type: 彩票类型 ('dlt' 或 'ssq')
        """
        self.lottery_type = lottery_type
        
class DLTNumber(LotteryNumber):
    """大乐透号码"""
    
    def __init__(self, front: List[int], back: List[int]):
        """
        Args:
            front: 前区号码列表
            back: 后区号码列表
        """
        super().__init__('dlt')
        self.front = sorted(front)
        self.back = sorted(back)
        
    def __str__(self):
        front_str = ','.join(map(str, self.front))
        back_str = ','.join(map(str, self.back))
        return f"前区:[{front_str}] 后区:[{back_str}]"
        
class SSQNumber(LotteryNumber):
    """双色球号码"""
    
    def __init__(self, red: List[int], blue: int):
        """
        Args:
            red: 红球号码列表
            blue: 蓝球号码
        """
        super().__init__('ssq')
        self.red = sorted(red)
        self.blue = blue
        
    def __str__(self):
        red_str = ','.join(map(str, self.red))
        return f"红球:[{red_str}] 蓝球:[{self.blue}]"