from typing import Dict, List
import pandas as pd
from datetime import datetime
from .base_validator import BaseValidator, ValidationRule

class HistoryValidator(BaseValidator):
    """历史数据验证器"""
    
    def __init__(self):
        super().__init__()
        self._init_rules()
    
    def _init_rules(self):
        """初始化验证规则"""
        self.rules.extend([
            ValidationRule(
                name='required_columns',
                description='检查必需列是否存在',
                severity='error'
            ),
            ValidationRule(
                name='date_format',
                description='检查日期格式是否正确',
                severity='error'
            ),
            ValidationRule(
                name='date_sequence',
                description='检查日期是否连续',
                severity='warning'
            ),
            ValidationRule(
                name='duplicates',
                description='检查是否存在重复数据',
                severity='error'
            ),
            ValidationRule(
                name='missing_values',
                description='检查是否存在缺失值',
                severity='error'
            ),
            ValidationRule(
                name='data_range',
                description='检查数据范围是否合理',
                severity='error'
            )
        ])
    
    def validate(self, data: pd.DataFrame) -> Dict:
        """验证历史数据"""
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查必需列
        required_columns = {'date', 'issue'}
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            self.add_error(f'缺少必需列: {missing_columns}')
        
        # 检查日期格式
        try:
            data['date'] = pd.to_datetime(data['date'])
        except Exception:
            self.add_error('日期格式不正确')
            return self.validation_results
        
        # 检查日期连续性
        date_gaps = self._check_date_sequence(data['date'])
        if date_gaps:
            self.add_warning(f'发现{len(date_gaps)}个日期缺失')
        
        # 检查重复数据
        duplicates = data.duplicated().sum()
        if duplicates > 0:
            self.add_error(f'存在{duplicates}条重复数据')
        
        # 检查缺失值
        missing = data.isnull().sum()
        if missing.any():
            for col in missing[missing > 0].index:
                self.add_error(f'列 {col} 存在{missing[col]}个缺失值')
        
        # 检查数据范围
        self._check_data_range(data)
        
        return self.validation_results
    
    def _check_date_sequence(self, dates: pd.Series) -> List[datetime]:
        """检查日期连续性"""
        dates = dates.sort_values()
        date_range = pd.date_range(dates.min(), dates.max())
        missing_dates = date_range.difference(dates)
        return list(missing_dates)
    
    def _check_data_range(self, data: pd.DataFrame):
        """检查数据范围"""
        # 检查期号格式
        if not data['issue'].astype(str).str.match(r'^\d{8}$').all():
            self.add_error('期号格式不正确')
        
        # 根据列名判断彩票类型
        if 'red_numbers' in data.columns:  # 双色球
            self._check_ssq_range(data)
        elif 'front_numbers' in data.columns:  # 大乐透
            self._check_dlt_range(data)
    
    def _check_ssq_range(self, data: pd.DataFrame):
        """检查双色球数据范围"""
        red_numbers = data['red_numbers'].apply(eval)
        blue_number = data['blue_number']
        
        # 检查红球范围
        if not all(all(1 <= n <= 33 for n in nums) for nums in red_numbers):
            self.add_error('红球号码超出有效范围(1-33)')
        
        # 检查红球数量
        if not all(len(nums) == 6 for nums in red_numbers):
            self.add_error('红球号码数量不正确(应为6个)')
        
        # 检查蓝球范围
        if not all(1 <= n <= 16 for n in blue_number):
            self.add_error('蓝球号码超出有效范围(1-16)')
    
    def _check_dlt_range(self, data: pd.DataFrame):
        """检查大乐透数据范围"""
        front_numbers = data['front_numbers'].apply(eval)
        back_numbers = data['back_numbers'].apply(eval)
        
        # 检查前区范围
        if not all(all(1 <= n <= 35 for n in nums) for nums in front_numbers):
            self.add_error('前区号码超出有效范围(1-35)')
        
        # 检查前区数量
        if not all(len(nums) == 5 for nums in front_numbers):
            self.add_error('前区号码数量不正确(应为5个)')
        
        # 检查后区范围
        if not all(all(1 <= n <= 12 for n in nums) for nums in back_numbers):
            self.add_error('后区号码超出有效范围(1-12)')
        
        # 检查后区数量
        if not all(len(nums) == 2 for nums in back_numbers):
            self.add_error('后区号码数量不正确(应为2个)')