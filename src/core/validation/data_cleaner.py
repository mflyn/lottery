#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据清洗增强器
提供完整的数据清洗功能，包括格式标准化、异常值处理、数据修复等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import re
from datetime import datetime, timedelta

from .data_validator import DataValidator, ValidationLevel
from ..config_manager import get_config_manager
from ..exceptions import DataCleaningError
from ..logging_config import get_logger

class DataCleaner:
    """增强的数据清洗器"""
    
    def __init__(self, lottery_type: str):
        """初始化数据清洗器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
        """
        self.lottery_type = lottery_type
        self.config_manager = get_config_manager()
        self.logger = get_logger(__name__)
        self.validator = DataValidator(lottery_type)
        
        # 清洗统计
        self.cleaning_stats = {
            'total_records': 0,
            'cleaned_records': 0,
            'removed_records': 0,
            'fixed_records': 0,
            'issues_found': []
        }
    
    def clean_data(self, data: pd.DataFrame, 
                   auto_fix: bool = True, 
                   remove_invalid: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """清洗数据
        
        Args:
            data: 原始数据
            auto_fix: 是否自动修复可修复的问题
            remove_invalid: 是否移除无法修复的无效记录
            
        Returns:
            (清洗后的数据, 清洗报告)
        """
        self.logger.info(f"开始清洗 {self.lottery_type} 数据，共 {len(data)} 条记录")
        
        # 重置统计
        self.cleaning_stats = {
            'total_records': len(data),
            'cleaned_records': 0,
            'removed_records': 0,
            'fixed_records': 0,
            'issues_found': []
        }
        
        try:
            # 1. 基础清洗
            data = self._basic_cleaning(data)
            
            # 2. 格式标准化
            data = self._standardize_formats(data)
            
            # 3. 数据验证和修复
            if auto_fix:
                data = self._auto_fix_data(data)
            
            # 4. 移除无效记录
            if remove_invalid:
                data = self._remove_invalid_records(data)
            
            # 5. 更新清洗统计
            self.cleaning_stats['cleaned_records'] = len(data)
            
            # 6. 最终验证
            validation_result = self.validator.validate(data)
            
            # 7. 生成清洗报告
            report = self._generate_cleaning_report(validation_result)
            
            self.logger.info(f"数据清洗完成，保留 {len(data)} 条有效记录")
            
            return data, report
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {str(e)}", exc_info=True)
            raise DataCleaningError(f"数据清洗失败: {str(e)}")
    
    def _basic_cleaning(self, data: pd.DataFrame) -> pd.DataFrame:
        """基础清洗"""
        self.logger.debug("执行基础清洗")
        
        # 移除完全空白的行
        before_count = len(data)
        data = data.dropna(how='all')
        removed = before_count - len(data)
        if removed > 0:
            self.cleaning_stats['issues_found'].append(f"移除了 {removed} 条完全空白的记录")
        
        # 重置索引
        data = data.reset_index(drop=True)
        
        # 移除重复记录
        if 'draw_num' in data.columns:
            before_count = len(data)
            data = data.drop_duplicates(subset=['draw_num'], keep='first')
            removed = before_count - len(data)
            if removed > 0:
                self.cleaning_stats['issues_found'].append(f"移除了 {removed} 条重复记录")
        
        return data
    
    def _standardize_formats(self, data: pd.DataFrame) -> pd.DataFrame:
        """格式标准化"""
        self.logger.debug("执行格式标准化")
        
        # 标准化日期格式
        if 'draw_date' in data.columns:
            data = self._standardize_dates(data)
        
        # 标准化期号格式
        if 'draw_num' in data.columns:
            data = self._standardize_issue_numbers(data)
        
        # 标准化号码格式
        if self.lottery_type == 'ssq':
            data = self._standardize_ssq_numbers(data)
        elif self.lottery_type == 'dlt':
            data = self._standardize_dlt_numbers(data)
        
        return data
    
    def _standardize_dates(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化日期格式"""
        def parse_date(date_str):
            if pd.isna(date_str):
                return None
            
            # 尝试多种日期格式
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d', 
                '%Y.%m.%d',
                '%Y年%m月%d日',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except:
                    continue
            
            # 如果都失败，尝试自动解析
            try:
                return pd.to_datetime(date_str)
            except:
                return None
        
        original_count = data['draw_date'].notna().sum()
        data['draw_date'] = data['draw_date'].apply(parse_date)
        parsed_count = data['draw_date'].notna().sum()
        
        if parsed_count < original_count:
            failed = original_count - parsed_count
            self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的日期格式无法解析")
        
        return data
    
    def _standardize_issue_numbers(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化期号格式"""
        def clean_issue_number(issue):
            if pd.isna(issue):
                return None
            
            # 转换为字符串并清理
            issue_str = str(issue).strip()
            
            # 移除非数字字符
            issue_clean = re.sub(r'[^\d]', '', issue_str)
            
            # 根据彩票类型验证期号格式
            if self.lottery_type == 'ssq':
                # 双色球期号通常是8位数字 (YYYYNNN)
                if len(issue_clean) == 8 and issue_clean.isdigit():
                    return issue_clean
                elif len(issue_clean) >= 6:
                    # 尝试补零到8位
                    return issue_clean.zfill(8)
            elif self.lottery_type == 'dlt':
                # 大乐透期号通常是5位数字 (YYNNN)
                if len(issue_clean) == 5 and issue_clean.isdigit():
                    return issue_clean
                elif len(issue_clean) >= 4:
                    # 尝试补零到5位
                    return issue_clean.zfill(5)
            else:
                # 其他彩票类型，保持原有逻辑
                if len(issue_clean) >= 4 and issue_clean.isdigit():
                    return issue_clean
            
            return None
        
        original_count = data['draw_num'].notna().sum()
        data['draw_num'] = data['draw_num'].apply(clean_issue_number)
        cleaned_count = data['draw_num'].notna().sum()
        
        if cleaned_count < original_count:
            failed = original_count - cleaned_count
            self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的期号格式无法标准化")
        
        return data
    
    def _standardize_ssq_numbers(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化双色球号码格式"""
        # 标准化红球
        if 'red_numbers' in data.columns:
            data['red_numbers'] = data['red_numbers'].apply(self._parse_number_list)
            
            # 验证和修复红球
            def fix_red_numbers(numbers):
                if not isinstance(numbers, list) or len(numbers) != 6:
                    return None
                
                # 确保都是整数且在有效范围内
                try:
                    fixed_numbers = []
                    for n in numbers:
                        n = int(n)
                        if 1 <= n <= 33:
                            fixed_numbers.append(n)
                    
                    if len(fixed_numbers) == 6 and len(set(fixed_numbers)) == 6:
                        return sorted(fixed_numbers)
                except:
                    pass
                
                return None
            
            original_count = data['red_numbers'].notna().sum()
            data['red_numbers'] = data['red_numbers'].apply(fix_red_numbers)
            fixed_count = data['red_numbers'].notna().sum()
            
            if fixed_count < original_count:
                failed = original_count - fixed_count
                self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的红球号码无法修复")
        
        # 标准化蓝球
        if 'blue_number' in data.columns:
            def fix_blue_number(number):
                try:
                    n = int(number)
                    if 1 <= n <= 16:
                        return n
                except:
                    pass
                return None
            
            original_count = data['blue_number'].notna().sum()
            data['blue_number'] = data['blue_number'].apply(fix_blue_number)
            fixed_count = data['blue_number'].notna().sum()
            
            if fixed_count < original_count:
                failed = original_count - fixed_count
                self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的蓝球号码无法修复")
        
        return data
    
    def _standardize_dlt_numbers(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化大乐透号码格式"""
        # 标准化前区
        if 'front_numbers' in data.columns:
            data['front_numbers'] = data['front_numbers'].apply(self._parse_number_list)
            
            def fix_front_numbers(numbers):
                if not isinstance(numbers, list) or len(numbers) != 5:
                    return None
                
                try:
                    fixed_numbers = []
                    for n in numbers:
                        n = int(n)
                        if 1 <= n <= 35:
                            fixed_numbers.append(n)
                    
                    if len(fixed_numbers) == 5 and len(set(fixed_numbers)) == 5:
                        return sorted(fixed_numbers)
                except:
                    pass
                
                return None
            
            original_count = data['front_numbers'].notna().sum()
            data['front_numbers'] = data['front_numbers'].apply(fix_front_numbers)
            fixed_count = data['front_numbers'].notna().sum()
            
            if fixed_count < original_count:
                failed = original_count - fixed_count
                self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的前区号码无法修复")
        
        # 标准化后区
        if 'back_numbers' in data.columns:
            data['back_numbers'] = data['back_numbers'].apply(self._parse_number_list)
            
            def fix_back_numbers(numbers):
                if not isinstance(numbers, list) or len(numbers) != 2:
                    return None
                
                try:
                    fixed_numbers = []
                    for n in numbers:
                        n = int(n)
                        if 1 <= n <= 12:
                            fixed_numbers.append(n)
                    
                    if len(fixed_numbers) == 2 and len(set(fixed_numbers)) == 2:
                        return sorted(fixed_numbers)
                except:
                    pass
                
                return None
            
            original_count = data['back_numbers'].notna().sum()
            data['back_numbers'] = data['back_numbers'].apply(fix_back_numbers)
            fixed_count = data['back_numbers'].notna().sum()
            
            if fixed_count < original_count:
                failed = original_count - fixed_count
                self.cleaning_stats['issues_found'].append(f"有 {failed} 条记录的后区号码无法修复")
        
        return data
    
    def _parse_number_list(self, numbers) -> Optional[List[int]]:
        """解析号码列表"""
        # 处理各种类型的空值检查
        if numbers is None:
            return None
        
        # 对于数组类型，检查是否所有元素都是NaN
        if isinstance(numbers, (list, tuple, np.ndarray)):
            if len(numbers) == 0:
                return None
            # 检查是否所有元素都是NaN
            try:
                if all(pd.isna(x) for x in numbers):
                    return None
            except:
                pass
        else:
            # 对于标量值，使用pd.isna检查
            try:
                if pd.isna(numbers):
                    return None
            except:
                pass
        
        # 如果已经是列表
        if isinstance(numbers, (list, tuple)):
            try:
                # 确保列表中的元素都是整数
                return [int(x) for x in numbers if str(x).strip().isdigit()]
            except:
                return list(numbers)
        
        # 如果是字符串
        if isinstance(numbers, str):
            numbers = numbers.strip()
            
            # 尝试JSON解析
            try:
                parsed = json.loads(numbers)
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            except:
                pass
            
            # 尝试其他分隔符
            for sep in [',', ' ', '|', ';', '\t']:
                try:
                    parts = numbers.split(sep)
                    if len(parts) > 1:
                        return [int(p.strip()) for p in parts if p.strip().isdigit()]
                except:
                    continue
        
        return None
    
    def _auto_fix_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """自动修复数据"""
        self.logger.debug("执行自动数据修复")
        
        fixed_count = 0
        
        # 修复缺失的日期（基于期号推算）
        if 'draw_date' in data.columns and 'draw_num' in data.columns:
            fixed_count += self._fix_missing_dates(data)
        
        # 修复数值类型的字段
        numeric_fields = ['prize_pool', 'sales', 'first_prize_num', 'first_prize_amount']
        for field in numeric_fields:
            if field in data.columns:
                fixed_count += self._fix_numeric_field(data, field)
        
        if fixed_count > 0:
            self.cleaning_stats['fixed_records'] = fixed_count
            self.cleaning_stats['issues_found'].append(f"自动修复了 {fixed_count} 个数据问题")
        
        return data
    
    def _fix_missing_dates(self, data: pd.DataFrame) -> int:
        """修复缺失的日期"""
        fixed_count = 0
        
        # 基于期号推算日期的逻辑
        # 这里可以根据彩票的开奖规律来实现
        # 暂时跳过复杂的日期推算逻辑
        
        return fixed_count
    
    def _fix_numeric_field(self, data: pd.DataFrame, field: str) -> int:
        """修复数值字段"""
        fixed_count = 0
        
        def clean_numeric(value):
            if pd.isna(value):
                return None
            
            # 转换为字符串并清理
            value_str = str(value).strip()
            
            # 移除非数字字符（保留小数点）
            cleaned = re.sub(r'[^\d.]', '', value_str)
            
            try:
                return float(cleaned) if '.' in cleaned else int(cleaned)
            except:
                return None
        
        original_values = data[field].copy()
        data[field] = data[field].apply(clean_numeric)
        
        # 统计修复的数量
        for i in range(len(data)):
            if pd.notna(original_values.iloc[i]) and pd.notna(data[field].iloc[i]):
                if str(original_values.iloc[i]) != str(data[field].iloc[i]):
                    fixed_count += 1
        
        return fixed_count
    
    def _remove_invalid_records(self, data: pd.DataFrame) -> pd.DataFrame:
        """移除无效记录"""
        self.logger.debug("移除无效记录")
        
        before_count = len(data)
        
        # 移除关键字段为空的记录
        if self.lottery_type == 'ssq':
            required_fields = ['draw_date', 'draw_num', 'red_numbers', 'blue_number']
        elif self.lottery_type == 'dlt':
            required_fields = ['draw_date', 'draw_num', 'front_numbers', 'back_numbers']
        else:
            required_fields = ['draw_date', 'draw_num']
        
        for field in required_fields:
            if field in data.columns:
                data = data[data[field].notna()]
        
        removed_count = before_count - len(data)
        if removed_count > 0:
            self.cleaning_stats['removed_records'] = removed_count
            self.cleaning_stats['issues_found'].append(f"移除了 {removed_count} 条关键字段缺失的记录")
        
        return data
    
    def _generate_cleaning_report(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成清洗报告"""
        return {
            'cleaning_stats': self.cleaning_stats,
            'validation_result': validation_result,
            'data_quality': {
                'total_records': self.cleaning_stats['total_records'],
                'valid_records': self.cleaning_stats['cleaned_records'],
                'data_quality_score': (
                    self.cleaning_stats['cleaned_records'] / 
                    max(self.cleaning_stats['total_records'], 1)
                ) * 100,
                'issues_resolved': len(self.cleaning_stats['issues_found']),
                'validation_passed': validation_result['valid']
            }
        }

# 便捷函数
def clean_lottery_data(data: pd.DataFrame, 
                      lottery_type: str,
                      auto_fix: bool = True,
                      remove_invalid: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """清洗彩票数据的便捷函数
    
    Args:
        data: 原始数据
        lottery_type: 彩票类型
        auto_fix: 是否自动修复
        remove_invalid: 是否移除无效记录
        
    Returns:
        (清洗后的数据, 清洗报告)
    """
    cleaner = DataCleaner(lottery_type)
    return cleaner.clean_data(data, auto_fix, remove_invalid) 