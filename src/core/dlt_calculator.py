from typing import List, Dict, Tuple, Optional
from numbers import Integral
import math
import re
from dataclasses import dataclass
from itertools import combinations
from src.utils.logger import Logger
from src.core.calculators import BaseCalculator

@dataclass
class DLTBetResult:
    """大乐透投注结果"""
    total_bets: int          # 总注数
    total_amount: float      # 总金额
    combinations: List[List[int]]  # 所有组合(前5个为前区号码,后2个为后区号码)
    front_numbers: List[int] # 前区号码
    back_numbers: List[int]  # 后区号码
    is_additional: bool      # 是否追加投注

class DLTCalculator(BaseCalculator):
    """大乐透计算器（完整实现）

    提供大乐透投注计算、中奖计算等功能。
    继承自 BaseCalculator 基类。
    """

    # Official 2026 rules apply from issue 26014. Floating amounts require draw data.
    PRIZE_LEVELS = {
        (5, 2): (1, None, 0), (5, 1): (2, None, 0),
        (5, 0): (3, 5000, 0), (4, 2): (3, 5000, 0),
        (4, 1): (4, 300, 0), (4, 0): (5, 150, 0), (3, 2): (5, 150, 0),
        (3, 1): (6, 15, 0), (2, 2): (6, 15, 0),
        (3, 0): (7, 5, 0), (2, 1): (7, 5, 0), (1, 2): (7, 5, 0), (0, 2): (7, 5, 0),
    }
    LEGACY_PRIZE_LEVELS = {
        (5, 2): (1, None, 0), (5, 1): (2, None, 0), (5, 0): (3, 10000, 0),
        (4, 2): (4, 3000, 0), (4, 1): (5, 300, 0), (3, 2): (6, 200, 0),
        (4, 0): (7, 100, 0), (3, 1): (8, 15, 0), (2, 2): (8, 15, 0),
        (3, 0): (9, 5, 0), (2, 1): (9, 5, 0), (1, 2): (9, 5, 0), (0, 2): (9, 5, 0),
    }

    def __init__(self, config_manager=None):
        """初始化大乐透计算器

        Args:
            config_manager: 配置管理器实例（可选）
        """
        super().__init__(config_manager)
        self.logger = Logger()

        # 从配置管理器读取价格
        if self.config:
            self.basic_price = self.config.get_lottery_price('dlt', 'basic')
            self.additional_price = self.config.get_lottery_price('dlt', 'additional')
        else:
            self.basic_price = 2    # 默认基本投注每注2元
            self.additional_price = 1  # 默认追加投注每注1元
        
        # 2026新规：当奖池 >= 8亿元时，固定奖奖金上调 (3-7等奖)
        self.high_pool_prizes = {
            3: (6666, 0),
            4: (380, 0),
            5: (200, 0),
            6: (18, 0),
            7: (7, 0)
        }

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

    @staticmethod
    def _canonical_issue(draw_issue) -> Optional[str]:
        if draw_issue is None:
            return None
        issue = str(draw_issue).strip()
        if re.fullmatch(r'20[0-9]{5}', issue):
            issue = issue[2:]
        if not re.fullmatch(r'[0-9]{5}', issue) or int(issue[-3:]) == 0:
            raise ValueError('大乐透期号必须为YYNNN或20YYNNN')
        return issue

    @classmethod
    def get_prize_levels(cls, draw_issue=None) -> Dict:
        issue = cls._canonical_issue(draw_issue)
        if issue is None or int(issue) >= 26014:
            return cls.PRIZE_LEVELS
        if int(issue) >= 19019:
            return cls.LEGACY_PRIZE_LEVELS
        raise ValueError('暂不支持19019期之前的大乐透兑奖规则')

    def get_prize_amount(self, level: int, is_additional: bool = False,
                         prize_pool: Optional[float] = 0.0, *, draw_issue=None,
                         floating_prizes: Optional[Dict[int, float]] = None) -> Optional[float]:
        """固定奖按开奖前奖池计算；浮动奖金额缺失时返回None，不作金额假设。"""
        table = self.get_prize_levels(draw_issue)
        if prize_pool is not None and (not math.isfinite(prize_pool) or prize_pool < 0):
            raise ValueError('开奖前奖池必须为非负有限数值')
        if level == 0:
            return 0.0
        if level in (1, 2):
            basic = (floating_prizes or {}).get(level)
            if basic is None:
                return None
            if isinstance(basic, bool) or not math.isfinite(basic) or basic <= 0 or int(basic) != basic:
                raise ValueError('官方浮动奖单注奖金必须为正整数元')
            basic = int(basic)
            return basic + (basic * 8 // 10 if is_additional else 0)
        for award, basic, _ in table.values():
            if award == level:
                if table is self.PRIZE_LEVELS:
                    if prize_pool is None:
                        return None
                    if prize_pool >= 800000000:
                        basic = self.high_pool_prizes[level][0]
                return basic
        raise ValueError(f'奖级不适用于所选期号: {level}')

    @staticmethod
    def _validate_ticket(numbers):
        if not isinstance(numbers, (list, tuple)) or len(numbers) != 7:
            raise ValueError('单注号码必须为5个前区和2个后区号码')
        for area, count, maximum in [(numbers[:5], 5, 35), (numbers[5:], 2, 12)]:
            if (len(set(area)) != count or any(isinstance(n, bool) or not isinstance(n, Integral)
                                              or not 1 <= n <= maximum for n in area)):
                raise ValueError('号码重复或超出有效范围')

    def check_prize(self, bet_numbers: List[int], draw_numbers: List[int],
                    is_additional: bool = False, prize_pool: Optional[float] = 0.0, *,
                    draw_issue=None, floating_prizes: Optional[Dict[int, float]] = None) -> Tuple[int, Optional[float]]:
        """核对单注。默认采用26014期起规则；缺少官方浮动奖金额时奖金为None。

        prize_pool是开奖前奖池；默认0只用于低奖池条件试算，不代表某期开奖金额。
        """
        self._validate_ticket(bet_numbers)
        self._validate_ticket(draw_numbers)
        table = self.get_prize_levels(draw_issue)
        matches = (len(set(bet_numbers[:5]) & set(draw_numbers[:5])),
                   len(set(bet_numbers[5:]) & set(draw_numbers[5:])))
        level = table.get(matches, (0, 0, 0))[0]
        return level, self.get_prize_amount(level, is_additional, prize_pool,
                                             draw_issue=draw_issue, floating_prizes=floating_prizes)

    def check_complex_prize(self, front_numbers: List[int], back_numbers: List[int], draw_numbers: List[int],
                            is_additional: bool = False, prize_pool: Optional[float] = 0.0, *,
                            draw_issue=None, floating_prizes=None) -> Dict[int, int]:
        return self._summarize_prizes(self._generate_complex_combinations(front_numbers, back_numbers),
                                     draw_numbers, is_additional, prize_pool, draw_issue, floating_prizes)

    def check_dantuo_prize(self, front_dan: List[int], front_tuo: List[int], back_dan: List[int],
                          back_tuo: List[int], draw_numbers: List[int], is_additional: bool = False,
                          prize_pool: Optional[float] = 0.0, *, draw_issue=None, floating_prizes=None) -> Dict[int, int]:
        bets = self._generate_dantuo_combinations(front_dan, front_tuo, back_dan, back_tuo)
        return self._summarize_prizes(bets, draw_numbers, is_additional, prize_pool, draw_issue, floating_prizes)

    def _summarize_prizes(self, bets, draw, additional, pool, issue, floating):
        summary = {level: 0 for level in sorted({entry[0] for entry in self.get_prize_levels(issue).values()})}
        for bet in bets:
            level, _ = self.check_prize(bet, draw, additional, pool, draw_issue=issue, floating_prizes=floating)
            if level:
                summary[level] += 1
        return summary

    @classmethod
    def get_draw_context(cls, history, draw_issue, draw_numbers) -> Dict:
        """从匹配的历史记录取官方奖金，从紧邻上一期的余额取开奖前奖池。"""
        issue = cls._canonical_issue(draw_issue)
        context = {'draw_issue': issue, 'prize_pool': None, 'floating_prizes': {}}
        cls.get_prize_levels(issue)
        if issue is None or history is None:
            return context
        records = history.to_dict('records') if hasattr(history, 'to_dict') else history
        by_issue = {}
        for row in records:
            try:
                key = cls._canonical_issue(row.get('draw_num'))
                by_issue[key] = row
            except (TypeError, ValueError):
                continue
        current = by_issue.get(issue)
        if not current:
            return context
        front, back = current.get('front_numbers'), current.get('back_numbers')
        if not isinstance(front, (list, tuple)) or not isinstance(back, (list, tuple)):
            return context
        if sorted(front) + sorted(back) != sorted(draw_numbers[:5]) + sorted(draw_numbers[5:]):
            return context
        for level, field in [(1, 'first_prize_amount'), (2, 'second_prize_amount')]:
            amount = current.get(field)
            if isinstance(amount, (int, float)) and math.isfinite(amount) and amount > 0:
                context['floating_prizes'][level] = amount
        previous = by_issue.get(f'{int(issue) - 1:05d}') if int(issue[-3:]) > 1 else None
        if previous:
            pool = previous.get('prize_pool')
            # History loading also uses zero for missing/unparseable pool values.
            # Without provenance, zero cannot be treated as a verified official balance.
            if isinstance(pool, (int, float)) and math.isfinite(pool) and pool > 0:
                context['prize_pool'] = pool
        return context

    def format_prize_summary(self, summary: Dict[int, int], check_type: str = '单式',
                             is_additional: bool = False, **context) -> str:
        lines = [f"{check_type}中奖结果 ({'追加' if is_additional else '基本'}):"]
        total, unknown = 0, False
        for level, count in sorted(summary.items()):
            if not count:
                continue
            amount = self.get_prize_amount(level, is_additional, **context)
            if amount is None:
                unknown = True
                reason = '浮动奖金额以当期开奖公告为准' if level in (1, 2) else '缺少开奖前奖池，金额待核实'
                lines.append(f'  - {level}等奖: {count} 注，{reason}')
            else:
                lines.append(f'  - {level}等奖: {count} 注 x {amount} 元')
                total += count * amount
        if unknown:
            lines.append(f'总计: {sum(summary.values())} 注，已知奖金小计: {total} 元，部分奖金待核实')
        else:
            lines.append(f'总计: {sum(summary.values())} 注，总奖金: {total} 元')
        return '\n'.join(lines)
