from typing import Dict, List, Optional
from .base_validator import BaseValidator, ValidationRule
from ..models import LotteryNumber
from ..config_manager import ConfigManager

class NumberValidator(BaseValidator):
    """号码验证器"""

    def __init__(self, lottery_type: str, config_manager: Optional[ConfigManager] = None):
        super().__init__()
        self.lottery_type = lottery_type
        self.config = config_manager or ConfigManager()
        self._init_rules()
        
    def _init_rules(self):
        """初始化验证规则"""
        if self.lottery_type == 'dlt':
            self._init_dlt_rules()
        else:
            self._init_ssq_rules()
    
    def _init_dlt_rules(self):
        """初始化大乐透验证规则"""
        # 从配置获取参数
        front_count = self.config.get_lottery_count('dlt', 'front')
        back_count = self.config.get_lottery_count('dlt', 'back')
        front_min, front_max = self.config.get_lottery_range('dlt', 'front')
        back_min, back_max = self.config.get_lottery_range('dlt', 'back')

        self.rules.extend([
            ValidationRule(
                name='front_count',
                description=f'前区号码数量必须为{front_count}个',
                severity='error'
            ),
            ValidationRule(
                name='front_range',
                description=f'前区号码必须在{front_min}-{front_max}之间',
                severity='error'
            ),
            ValidationRule(
                name='front_duplicates',
                description='前区号码不能重复',
                severity='error'
            ),
            ValidationRule(
                name='front_sum',
                description='前区号码和应在合理范围内(30-140)',
                severity='warning'
            ),
            ValidationRule(
                name='front_consecutive',
                description='前区不建议出现3个以上连号',
                severity='warning'
            ),
            ValidationRule(
                name='front_odd_even',
                description='前区奇偶比例应均衡',
                severity='warning'
            ),
            ValidationRule(
                name='back_count',
                description=f'后区号码数量必须为{back_count}个',
                severity='error'
            ),
            ValidationRule(
                name='back_range',
                description=f'后区号码必须在{back_min}-{back_max}之间',
                severity='error'
            ),
            ValidationRule(
                name='back_duplicates',
                description='后区号码不能重复',
                severity='error'
            ),
            ValidationRule(
                name='back_sum',
                description='后区号码和应在合理范围内(3-24)',
                severity='warning'
            )
        ])
    
    def _init_ssq_rules(self):
        """初始化双色球验证规则"""
        # 从配置获取参数
        red_count = self.config.get_lottery_count('ssq', 'red')
        blue_count = self.config.get_lottery_count('ssq', 'blue')
        red_min, red_max = self.config.get_lottery_range('ssq', 'red')
        blue_min, blue_max = self.config.get_lottery_range('ssq', 'blue')

        self.rules.extend([
            ValidationRule(
                name='red_count',
                description=f'红球号码数量必须为{red_count}个',
                severity='error'
            ),
            ValidationRule(
                name='red_range',
                description=f'红球号码必须在{red_min}-{red_max}之间',
                severity='error'
            ),
            ValidationRule(
                name='red_duplicates',
                description='红球号码不能重复',
                severity='error'
            ),
            ValidationRule(
                name='red_sum',
                description='红球号码和应在合理范围内(21-183)',
                severity='warning'
            ),
            ValidationRule(
                name='red_consecutive',
                description='红球不建议出现4个以上连号',
                severity='warning'
            ),
            ValidationRule(
                name='red_odd_even',
                description='红球奇偶比例应均衡',
                severity='warning'
            ),
            ValidationRule(
                name='blue_range',
                description=f'蓝球号码必须在{blue_min}-{blue_max}之间',
                severity='error'
            )
        ])

    def validate(self, number: LotteryNumber) -> Dict:
        """验证号码是否有效"""
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if self.lottery_type == 'dlt':
            self._validate_dlt(number)
        else:
            self._validate_ssq(number)
            
        return self.validation_results
    
    def _validate_dlt(self, number: LotteryNumber):
        """验证大乐透号码"""
        # 从配置获取参数
        front_count = self.config.get_lottery_count('dlt', 'front')
        back_count = self.config.get_lottery_count('dlt', 'back')
        front_min, front_max = self.config.get_lottery_range('dlt', 'front')
        back_min, back_max = self.config.get_lottery_range('dlt', 'back')

        # 基本验证
        if len(number.front) != front_count:
            self.add_error(f'前区号码数量必须为{front_count}个')

        if not all(front_min <= n <= front_max for n in number.front):
            self.add_error(f'前区号码必须在{front_min}-{front_max}之间')

        if len(set(number.front)) != len(number.front):
            self.add_error('前区号码不能重复')

        if len(number.back) != back_count:
            self.add_error(f'后区号码数量必须为{back_count}个')

        if not all(back_min <= n <= back_max for n in number.back):
            self.add_error(f'后区号码必须在{back_min}-{back_max}之间')

        if len(set(number.back)) != len(number.back):
            self.add_error('后区号码不能重复')
        
        # 高级验证
        front_sum = sum(number.front)
        if not (30 <= front_sum <= 140):
            self.add_warning('前区号码和不在推荐范围内')
            
        back_sum = sum(number.back)
        if not (3 <= back_sum <= 24):
            self.add_warning('后区号码和不在推荐范围内')
        
        # 连号检查
        consecutive_count = self._count_consecutive(number.front)
        if consecutive_count >= 3:
            self.add_warning(f'前区存在{consecutive_count}个连号')
        
        # 奇偶比例检查
        odd_count = sum(1 for n in number.front if n % 2 == 1)
        if odd_count <= 1 or odd_count >= 4:
            self.add_warning('前区奇偶比例不均衡')
    
    def _validate_ssq(self, number: LotteryNumber):
        """验证双色球号码"""
        # 从配置获取参数
        red_count = self.config.get_lottery_count('ssq', 'red')
        red_min, red_max = self.config.get_lottery_range('ssq', 'red')
        blue_min, blue_max = self.config.get_lottery_range('ssq', 'blue')

        # 基本验证
        if len(number.red) != red_count:
            self.add_error(f'红球号码数量必须为{red_count}个')

        if not all(red_min <= n <= red_max for n in number.red):
            self.add_error(f'红球号码必须在{red_min}-{red_max}之间')

        if len(set(number.red)) != len(number.red):
            self.add_error('红球号码不能重复')

        if not (blue_min <= number.blue <= blue_max):
            self.add_error(f'蓝球号码必须在{blue_min}-{blue_max}之间')
        
        # 高级验证
        red_sum = sum(number.red)
        if not (21 <= red_sum <= 183):
            self.add_warning('红球号码和不在推荐范围内')
        
        # 连号检查
        consecutive_count = self._count_consecutive(number.red)
        if consecutive_count >= 4:
            self.add_warning(f'红球存在{consecutive_count}个连号')
        
        # 奇偶比例检查
        odd_count = sum(1 for n in number.red if n % 2 == 1)
        if odd_count <= 2 or odd_count >= 5:
            self.add_warning('红球奇偶比例不均衡')
    
    def _count_consecutive(self, numbers: List[int]) -> int:
        """计算最大连号数量"""
        if not numbers:
            return 0
            
        numbers = sorted(numbers)
        max_consecutive = current_consecutive = 1
        
        for i in range(1, len(numbers)):
            if numbers[i] == numbers[i-1] + 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
                
        return max_consecutive
