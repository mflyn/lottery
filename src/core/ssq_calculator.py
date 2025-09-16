from typing import List, Dict, Tuple
from dataclasses import dataclass
from itertools import combinations
from src.utils.logger import Logger

@dataclass
class SSQBetResult:
    """双色球投注结果"""
    total_bets: int          # 总注数
    total_amount: float      # 总金额
    combinations: List[List[int]]  # 所有组合(前6个为红球,最后1个为蓝球)
    red_numbers: List[int]   # 红球号码
    blue_numbers: List[int]  # 蓝球号码

class SSQCalculator:
    """双色球计算器"""
    
    # 奖级设置
    PRIZE_LEVELS = {
        # (红球数, 蓝球数): [奖级, 基本奖金]
        (6, 1): [1, 5000000],  # 一等奖(浮动奖金)
        (6, 0): [2, 100000],   # 二等奖(浮动奖金)
        (5, 1): [3, 3000],     # 三等奖
        (5, 0): [4, 200],      # 四等奖
        (4, 1): [4, 200],      # 四等奖
        (4, 0): [5, 10],       # 五等奖
        (3, 1): [5, 10],       # 五等奖
        (2, 1): [6, 5],        # 六等奖
        (1, 1): [6, 5],        # 六等奖
        (0, 1): [6, 5],        # 六等奖
    }
    
    def __init__(self):
        self.logger = Logger()
        self.price_per_bet = 2  # 每注2元
        
    def validate_numbers(self, numbers: List[int], color: str) -> bool:
        """验证号码是否有效
        
        Args:
            numbers: 号码列表
            color: 球的颜色('red'/'blue')
        """
        if not numbers:
            return False
            
        if color == 'red':
            return all(1 <= n <= 33 for n in numbers)
        else:  # blue
            return all(1 <= n <= 16 for n in numbers)
            
    def calculate_complex_bet(self, red_numbers: List[int], blue_numbers: List[int]) -> SSQBetResult:
        """计算复式投注
        
        Args:
            red_numbers: 红球号码列表(6-33个号码)
            blue_numbers: 蓝球号码列表(1-16个号码)
        """
        # 验证号码
        if not (self.validate_numbers(red_numbers, 'red') and 
                self.validate_numbers(blue_numbers, 'blue')):
            raise ValueError("号码无效")
            
        if not (6 <= len(red_numbers) <= 33 and 1 <= len(blue_numbers) <= 16):
            raise ValueError("号码数量不符合规则")
            
        # 计算组合数
        red_combinations = list(combinations(sorted(red_numbers), 6))
        
        # 计算总注数
        total_bets = len(red_combinations) * len(blue_numbers)
        
        # 生成所有组合
        all_combinations = []
        for red in red_combinations:
            for blue in blue_numbers:
                all_combinations.append(list(red) + [blue])
                
        return SSQBetResult(
            total_bets=total_bets,
            total_amount=total_bets * self.price_per_bet,
            combinations=all_combinations[:10],  # 只返回前10个组合作为示例
            red_numbers=sorted(red_numbers),
            blue_numbers=sorted(blue_numbers)
        )
        
    def calculate_dantuo_bet(self, 
                           red_dan: List[int], 
                           red_tuo: List[int],
                           blue_numbers: List[int]) -> SSQBetResult:
        """计算胆拖投注
        
        Args:
            red_dan: 红球胆码(0-5个号码)
            red_tuo: 红球拖码
            blue_numbers: 蓝球号码列表
        """
        # 验证号码
        if (red_dan and not self.validate_numbers(red_dan, 'red')) or \
           (red_tuo and not self.validate_numbers(red_tuo, 'red')) or \
           (blue_numbers and not self.validate_numbers(blue_numbers, 'blue')):
            raise ValueError("号码无效")
                
        # 验证胆码数量
        if len(red_dan) >= 6:
            raise ValueError("红球胆码数量不能超过5个")
            
        # 验证红球号码
        need_red = 6 - len(red_dan)  # 需要从拖码中选择的个数
        if len(red_tuo) < need_red:
            raise ValueError("红球拖码数量不足")
            
        # 验证蓝球号码
        if len(blue_numbers) < 1:
            raise ValueError("至少需要选择1个蓝球")
            
        # 计算组合
        red_combinations = [list(red_dan) + list(c) 
                          for c in combinations(red_tuo, need_red)]
                           
        # 计算总注数
        total_bets = len(red_combinations) * len(blue_numbers)
        
        # 生成所有组合
        all_combinations = []
        for red in red_combinations:
            for blue in blue_numbers:
                all_combinations.append(sorted(red) + [blue])
                
        return SSQBetResult(
            total_bets=total_bets,
            total_amount=total_bets * self.price_per_bet,
            combinations=all_combinations[:10],  # 只返回前10个组合作为示例
            red_numbers=sorted(red_dan + red_tuo),
            blue_numbers=sorted(blue_numbers)
        )

    def _generate_complex_combinations(self, red_numbers: List[int], blue_numbers: List[int]) -> List[List[int]]:
        """内部方法：生成复式投注的所有单式组合"""
        if not (6 <= len(red_numbers) <= 33 and 1 <= len(blue_numbers) <= 16):
            # 此处不抛出异常，因为调用者可能需要处理无效输入
            # 但实际计算方法中应有验证
            return []
        red_combinations = list(combinations(sorted(red_numbers), 6))
        all_combinations = []
        for red in red_combinations:
            for blue in blue_numbers:
                all_combinations.append(list(red) + [blue])
        return all_combinations

    def _generate_dantuo_combinations(self, red_dan: List[int], red_tuo: List[int], blue_numbers: List[int]) -> List[List[int]]:
        """内部方法：生成胆拖投注的所有单式组合"""
        if len(red_dan) >= 6 or len(blue_numbers) < 1:
             return []
        need_red = 6 - len(red_dan)
        if len(red_tuo) < need_red:
             return []
        if set(red_dan) & set(red_tuo):
             return [] # 胆拖不能重复

        red_combinations = [list(red_dan) + list(c)
                          for c in combinations(red_tuo, need_red)]
        all_combinations = []
        for red in red_combinations:
            for blue in blue_numbers:
                all_combinations.append(sorted(red) + [blue])
        return all_combinations

    def check_prize(self, bet_numbers: List[int], draw_numbers: List[int]) -> Tuple[int, float]:
        """检查单注中奖情况

        Args:
            bet_numbers: 单注投注号码(前6个为红球,最后1个为蓝球)
            draw_numbers: 开奖号码(前6个为红球,最后1个为蓝球)

        Returns:
            (奖级, 奖金)
        """
        bet_red = set(bet_numbers[:6])
        bet_blue = bet_numbers[6]
        draw_red = set(draw_numbers[:6])
        draw_blue = draw_numbers[6]

        print(f"--- Debug check_prize: bet={bet_numbers}, draw={draw_numbers} ---") # 打印输入

        # 计算红蓝球匹配数
        red_matches = len(bet_red & draw_red)
        blue_match = 1 if bet_blue == draw_blue else 0

        # 查找中奖等级和奖金
        prize_key = (red_matches, blue_match)
        print(f"--- Debug check_prize: red_matches={red_matches}, blue_match={blue_match}, prize_key={prize_key} ---") # 打印匹配结果

        if prize_key in self.PRIZE_LEVELS:
            result = tuple(self.PRIZE_LEVELS[prize_key])
            print(f"--- Debug check_prize: Found level {result[0]}, returning {result} ---") # 打印找到的奖级
            return result
        print("--- Debug check_prize: Not found in PRIZE_LEVELS, returning (0, 0) ---") # 打印未中奖
        return (0, 0)  # 未中奖

    def check_complex_prize(self, red_numbers: List[int], blue_numbers: List[int], draw_numbers: List[int]) -> Dict[int, int]:
        """检查复式投注的中奖情况

        Args:
            red_numbers: 复式红球
            blue_numbers: 复式蓝球
            draw_numbers: 开奖号码

        Returns:
            一个字典，键是奖级，值是该奖级的注数。例如 {1: 0, 3: 2, 6: 10}
        """
        all_bets = self._generate_complex_combinations(red_numbers, blue_numbers)
        prize_summary = {level: 0 for level in range(1, 7)} # 初始化奖级计数

        for bet in all_bets:
            level, _ = self.check_prize(bet, draw_numbers)
            if level > 0:
                prize_summary[level] += 1
        return prize_summary

    def check_dantuo_prize(self, red_dan: List[int], red_tuo: List[int], blue_numbers: List[int], draw_numbers: List[int]) -> Dict[int, int]:
        """检查胆拖投注的中奖情况

        Args:
            red_dan: 红球胆码
            red_tuo: 红球拖码
            blue_numbers: 蓝球号码
            draw_numbers: 开奖号码

        Returns:
            一个字典，键是奖级，值是该奖级的注数。
        """
        all_bets = self._generate_dantuo_combinations(red_dan, red_tuo, blue_numbers)
        prize_summary = {level: 0 for level in range(1, 7)} # 初始化奖级计数

        for bet in all_bets:
            level, _ = self.check_prize(bet, draw_numbers)
            if level > 0:
                prize_summary[level] += 1
        return prize_summary
