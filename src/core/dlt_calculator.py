from typing import List, Dict, Tuple
from dataclasses import dataclass
from itertools import combinations
from src.utils.logger import Logger

@dataclass
class DLTBetResult:
    """大乐透投注结果"""
    total_bets: int          # 总注数
    total_amount: float      # 总金额
    combinations: List[List[int]]  # 所有组合(前5个为前区号码,后2个为后区号码)
    front_numbers: List[int] # 前区号码
    back_numbers: List[int]  # 后区号码
    is_additional: bool      # 是否追加投注

class DLTCalculator:
    """大乐透计算器"""
    
    # 奖级设置
    PRIZE_LEVELS = {
        # (前区命中数, 后区命中数): [奖级, 基本奖金, 追加奖金]
        (5, 2): [1, 10000000, 8000000],  # 一等奖
        (5, 1): [2, 250000, 200000],     # 二等奖
        (5, 0): [3, 10000, 8000],        # 三等奖
        (4, 2): [4, 3000, 2400],         # 四等奖
        (4, 1): [5, 300, 240],           # 五等奖
        (3, 2): [6, 200, 160],           # 六等奖
        (4, 0): [7, 100, 80],            # 七等奖
        (3, 1): [8, 15, 12],             # 八等奖
        (2, 2): [8, 15, 12],             # 八等奖
        (3, 0): [9, 5, 0],               # 九等奖
        (1, 2): [9, 5, 0],               # 九等奖
        (2, 1): [9, 5, 0],               # 九等奖
        (0, 2): [9, 5, 0],               # 九等奖
    }
    
    def __init__(self):
        self.logger = Logger()
        self.basic_price = 2    # 基本投注每注2元
        self.additional_price = 1  # 追加投注每注1元
        
    def validate_numbers(self, numbers: List[int], area: str) -> bool:
        """验证号码是否有效
        
        Args:
            numbers: 号码列表
            area: 区域('front'/'back')
        """
        if not numbers:
            return False
            
        if area == 'front':
            return all(1 <= n <= 35 for n in numbers)
        else:  # back
            return all(1 <= n <= 12 for n in numbers)
            
    def calculate_complex_bet(self, 
                            front_numbers: List[int], 
                            back_numbers: List[int],
                            is_additional: bool = False) -> DLTBetResult:
        """计算复式投注
        
        Args:
            front_numbers: 前区号码列表(5-35个号码)
            back_numbers: 后区号码列表(2-12个号码)
            is_additional: 是否追加投注
        """
        # 验证号码
        if not (self.validate_numbers(front_numbers, 'front') and 
                self.validate_numbers(back_numbers, 'back')):
            raise ValueError("号码无效")
            
        if not (5 <= len(front_numbers) <= 35 and 2 <= len(back_numbers) <= 12):
            raise ValueError("号码数量不符合规则")
            
        # 计算组合数
        front_combinations = list(combinations(sorted(front_numbers), 5))
        back_combinations = list(combinations(sorted(back_numbers), 2))
        
        # 计算总注数
        total_bets = len(front_combinations) * len(back_combinations)
        
        # 计算投注金额
        price = self.basic_price + (self.additional_price if is_additional else 0)
        total_amount = total_bets * price
        
        # 生成所有组合
        all_combinations = []
        for front in front_combinations:
            for back in back_combinations:
                all_combinations.append(list(front) + list(back))
                
        return DLTBetResult(
            total_bets=total_bets,
            total_amount=total_amount,
            combinations=all_combinations[:10],  # 只返回前10个组合作为示例
            front_numbers=sorted(front_numbers),
            back_numbers=sorted(back_numbers),
            is_additional=is_additional
        )
        
    def calculate_dantuo_bet(self,
                           front_dan: List[int],
                           front_tuo: List[int],
                           back_dan: List[int],
                           back_tuo: List[int],
                           is_additional: bool = False) -> DLTBetResult:
        """计算胆拖投注
        
        Args:
            front_dan: 前区胆码(0-4个号码)
            front_tuo: 前区拖码
            back_dan: 后区胆码(0-1个号码)
            back_tuo: 后区拖码
            is_additional: 是否追加投注
        """
        # 验证号码
        if ((front_dan and not self.validate_numbers(front_dan, 'front')) or
            (front_tuo and not self.validate_numbers(front_tuo, 'front')) or
            (back_dan and not self.validate_numbers(back_dan, 'back')) or
            (back_tuo and not self.validate_numbers(back_tuo, 'back'))):
            raise ValueError("号码无效")
            
        # 验证胆码数量
        if len(front_dan) >= 5:
            raise ValueError("前区胆码数量不能超过4个")
        if len(back_dan) >= 2:
            raise ValueError("后区胆码数量不能超过1个")
            
        # 验证号码数量
        need_front = 5 - len(front_dan)  # 需要从前区拖码中选择的个数
        need_back = 2 - len(back_dan)    # 需要从后区拖码中选择的个数
        
        if len(front_tuo) < need_front or len(back_tuo) < need_back:
            raise ValueError("拖码数量不足")
            
        # 计算组合
        front_combinations = [list(front_dan) + list(c) 
                            for c in combinations(front_tuo, need_front)]
        back_combinations = [list(back_dan) + list(c)
                           for c in combinations(back_tuo, need_back)]
        
        # 计算总注数
        total_bets = len(front_combinations) * len(back_combinations)
        
        # 计算投注金额
        price = self.basic_price + (self.additional_price if is_additional else 0)
        total_amount = total_bets * price
        
        # 生成所有组合
        all_combinations = []
        for front in front_combinations:
            for back in back_combinations:
                all_combinations.append(sorted(front) + sorted(back))
                
        return DLTBetResult(
            total_bets=total_bets,
            total_amount=total_amount,
            combinations=all_combinations[:10],
            front_numbers=sorted(front_dan + front_tuo),
            back_numbers=sorted(back_dan + back_tuo),
            is_additional=is_additional
        )

    def _generate_complex_combinations(self, front_numbers: List[int], back_numbers: List[int]) -> List[List[int]]:
        """内部方法：生成复式投注的所有单式组合"""
        if not (5 <= len(front_numbers) <= 35 and 2 <= len(back_numbers) <= 12):
            return []
        front_combinations = list(combinations(sorted(front_numbers), 5))
        back_combinations = list(combinations(sorted(back_numbers), 2))
        all_combinations = []
        for front in front_combinations:
            for back in back_combinations:
                all_combinations.append(list(front) + list(back))
        return all_combinations

    def _generate_dantuo_combinations(self, front_dan: List[int], front_tuo: List[int], back_dan: List[int], back_tuo: List[int]) -> List[List[int]]:
        """内部方法：生成胆拖投注的所有单式组合"""
        if len(front_dan) >= 5 or len(back_dan) >= 2:
            return []
        need_front = 5 - len(front_dan)
        need_back = 2 - len(back_dan)
        if len(front_tuo) < need_front or len(back_tuo) < need_back:
            return []
        if set(front_dan) & set(front_tuo) or set(back_dan) & set(back_tuo):
             return [] # 胆拖不能重复

        front_combinations = [list(front_dan) + list(c)
                            for c in combinations(front_tuo, need_front)]
        back_combinations = [list(back_dan) + list(c)
                           for c in combinations(back_tuo, need_back)]
        all_combinations = []
        for front in front_combinations:
            for back in back_combinations:
                all_combinations.append(sorted(front) + sorted(back))
        return all_combinations

    def check_prize(self, 
                   bet_numbers: List[int], 
                   draw_numbers: List[int],
                   is_additional: bool = False) -> Tuple[int, float]:
        """检查单注中奖情况

        Args:
            bet_numbers: 单注投注号码(前5个为前区号码,后2个为后区号码)
            draw_numbers: 开奖号码(前5个为前区号码,后2个为后区号码)
            is_additional: 是否追加投注

        Returns:
            (奖级, 奖金)
        """
        # 分离前后区号码
        bet_front = set(bet_numbers[:5])
        bet_back = set(bet_numbers[5:])
        draw_front = set(draw_numbers[:5])
        draw_back = set(draw_numbers[5:])

        # 计算前后区匹配数
        front_matches = len(bet_front & draw_front)
        back_matches = len(bet_back & draw_back)

        # 查找中奖等级和奖金
        prize_key = (front_matches, back_matches)
        if prize_key in self.PRIZE_LEVELS:
            level, basic, additional = self.PRIZE_LEVELS[prize_key]
            prize = basic + (additional if is_additional else 0)
            return level, prize
        return 0, 0  # 未中奖

    def check_complex_prize(self, front_numbers: List[int], back_numbers: List[int], draw_numbers: List[int], is_additional: bool = False) -> Dict[int, int]:
        """检查复式投注的中奖情况

        Args:
            front_numbers: 复式前区
            back_numbers: 复式后区
            draw_numbers: 开奖号码
            is_additional: 是否追加

        Returns:
            一个字典，键是奖级，值是该奖级的注数。例如 {1: 0, 4: 2, 8: 10}
        """
        all_bets = self._generate_complex_combinations(front_numbers, back_numbers)
        prize_summary = {level: 0 for level in range(1, 10)} # DLT 奖级 1-9

        for bet in all_bets:
            level, _ = self.check_prize(bet, draw_numbers, is_additional)
            if level > 0:
                prize_summary[level] += 1
        return prize_summary

    def check_dantuo_prize(self, front_dan: List[int], front_tuo: List[int], back_dan: List[int], back_tuo: List[int], draw_numbers: List[int], is_additional: bool = False) -> Dict[int, int]:
        """检查胆拖投注的中奖情况

        Args:
            (胆拖号码...)
            draw_numbers: 开奖号码
            is_additional: 是否追加

        Returns:
            一个字典，键是奖级，值是该奖级的注数。
        """
        all_bets = self._generate_dantuo_combinations(front_dan, front_tuo, back_dan, back_tuo)
        prize_summary = {level: 0 for level in range(1, 10)} # DLT 奖级 1-9

        for bet in all_bets:
            level, _ = self.check_prize(bet, draw_numbers, is_additional)
            if level > 0:
                prize_summary[level] += 1
        return prize_summary
