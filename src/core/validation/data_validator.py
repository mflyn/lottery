#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一数据验证框架
提供完整的数据验证功能，包括格式验证、范围验证、逻辑验证等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable, Union
import json
from dataclasses import dataclass
from enum import Enum

from ..config_manager import get_config_manager
from ..exceptions import DataValidationError
from ..logging_config import get_logger

class ValidationLevel(Enum):
    """验证级别"""
    ERROR = "error"      # 错误：必须修复
    WARNING = "warning"  # 警告：建议修复
    INFO = "info"        # 信息：仅提示

@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    description: str
    level: ValidationLevel
    validator: Callable
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

@dataclass
class ValidationResult:
    """验证结果"""
    rule_name: str
    level: ValidationLevel
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class DataValidator:
    """统一数据验证器"""
    
    def __init__(self, lottery_type: str = None):
        """初始化验证器
        
        Args:
            lottery_type: 彩票类型，如果指定则加载对应的验证规则
        """
        self.config_manager = get_config_manager()
        self.logger = get_logger(__name__)
        self.lottery_type = lottery_type
        
        # 验证规则集合
        self.rules: List[ValidationRule] = []
        
        # 验证结果
        self.results: List[ValidationResult] = []
        
        # 初始化基础规则
        self._init_base_rules()
        
        # 如果指定了彩票类型，加载对应规则
        if lottery_type:
            self._init_lottery_rules(lottery_type)
    
    def _init_base_rules(self):
        """初始化基础验证规则"""
        # 数据框基础验证
        self.add_rule(ValidationRule(
            name="dataframe_not_empty",
            description="数据框不能为空",
            level=ValidationLevel.ERROR,
            validator=self._validate_dataframe_not_empty
        ))
        
        self.add_rule(ValidationRule(
            name="required_columns",
            description="必需列存在性检查",
            level=ValidationLevel.ERROR,
            validator=self._validate_required_columns
        ))
        
        # 数据类型验证
        self.add_rule(ValidationRule(
            name="data_types",
            description="数据类型验证",
            level=ValidationLevel.ERROR,
            validator=self._validate_data_types
        ))
        
        # 数据完整性验证
        self.add_rule(ValidationRule(
            name="data_completeness",
            description="数据完整性检查",
            level=ValidationLevel.WARNING,
            validator=self._validate_data_completeness
        ))
        
        # 异常值检测
        self.add_rule(ValidationRule(
            name="outlier_detection",
            description="异常值检测",
            level=ValidationLevel.WARNING,
            validator=self._validate_outliers
        ))
        
        # 日期验证
        self.add_rule(ValidationRule(
            name="date_format",
            description="日期格式验证",
            level=ValidationLevel.ERROR,
            validator=self._validate_date_format
        ))
        
        self.add_rule(ValidationRule(
            name="date_range",
            description="日期范围验证",
            level=ValidationLevel.WARNING,
            validator=self._validate_date_range
        ))
        
        self.add_rule(ValidationRule(
            name="date_sequence",
            description="日期序列验证",
            level=ValidationLevel.WARNING,
            validator=self._validate_date_sequence
        ))
        
        # 期号验证
        self.add_rule(ValidationRule(
            name="issue_format",
            description="期号格式验证",
            level=ValidationLevel.ERROR,
            validator=self._validate_issue_format
        ))
        
        self.add_rule(ValidationRule(
            name="issue_uniqueness",
            description="期号唯一性验证",
            level=ValidationLevel.ERROR,
            validator=self._validate_issue_uniqueness
        ))
        
        self.add_rule(ValidationRule(
            name="issue_sequence",
            description="期号序列验证",
            level=ValidationLevel.WARNING,
            validator=self._validate_issue_sequence
        ))
    
    def _init_lottery_rules(self, lottery_type: str):
        """初始化彩票类型特定的验证规则"""
        if lottery_type == 'ssq':
            self._init_ssq_rules()
        elif lottery_type == 'dlt':
            self._init_dlt_rules()
        else:
            self.logger.warning(f"未知的彩票类型: {lottery_type}")
    
    def _init_ssq_rules(self):
        """初始化双色球验证规则"""
        # 红球验证
        self.add_rule(ValidationRule(
            name="ssq_red_count",
            description="红球数量必须为6个",
            level=ValidationLevel.ERROR,
            validator=self._validate_ssq_red_count
        ))
        
        self.add_rule(ValidationRule(
            name="ssq_red_range",
            description="红球号码必须在1-33之间",
            level=ValidationLevel.ERROR,
            validator=self._validate_ssq_red_range
        ))
        
        self.add_rule(ValidationRule(
            name="ssq_red_duplicates",
            description="红球号码不能重复",
            level=ValidationLevel.ERROR,
            validator=self._validate_ssq_red_duplicates
        ))
        
        # 蓝球验证
        self.add_rule(ValidationRule(
            name="ssq_blue_range",
            description="蓝球号码必须在1-16之间",
            level=ValidationLevel.ERROR,
            validator=self._validate_ssq_blue_range
        ))
    
    def _init_dlt_rules(self):
        """初始化大乐透验证规则"""
        # 前区验证
        self.add_rule(ValidationRule(
            name="dlt_front_count",
            description="前区号码数量必须为5个",
            level=ValidationLevel.ERROR,
            validator=self._validate_dlt_front_count
        ))
        
        self.add_rule(ValidationRule(
            name="dlt_front_range",
            description="前区号码必须在1-35之间",
            level=ValidationLevel.ERROR,
            validator=self._validate_dlt_front_range
        ))
        
        # 后区验证
        self.add_rule(ValidationRule(
            name="dlt_back_count",
            description="后区号码数量必须为2个",
            level=ValidationLevel.ERROR,
            validator=self._validate_dlt_back_count
        ))
        
        self.add_rule(ValidationRule(
            name="dlt_back_range",
            description="后区号码必须在1-12之间",
            level=ValidationLevel.ERROR,
            validator=self._validate_dlt_back_range
        ))
    
    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules.append(rule)
    
    def validate(self, data: Union[pd.DataFrame, Dict, List]) -> Dict[str, Any]:
        """执行数据验证"""
        self.results.clear()
        
        try:
            # 数据类型转换
            if isinstance(data, dict):
                data = pd.DataFrame([data])
            elif isinstance(data, list):
                data = pd.DataFrame(data)
            
            # 执行所有验证规则
            for rule in self.rules:
                try:
                    rule.validator(data, rule.params)
                except Exception as e:
                    self.results.append(ValidationResult(
                        rule_name=rule.name,
                        level=ValidationLevel.ERROR,
                        message=f"验证规则执行失败: {str(e)}",
                        details={"exception": str(e)}
                    ))
            
            # 生成验证报告
            return self._generate_report()
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}", exc_info=True)
            raise DataValidationError(f"数据验证失败: {str(e)}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        errors = [r for r in self.results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.results if r.level == ValidationLevel.WARNING]
        infos = [r for r in self.results if r.level == ValidationLevel.INFO]
        
        return {
            "valid": len(errors) == 0,
            "total_issues": len(self.results),
            "errors": [{"rule": r.rule_name, "message": r.message, "details": r.details} for r in errors],
            "warnings": [{"rule": r.rule_name, "message": r.message, "details": r.details} for r in warnings],
            "infos": [{"rule": r.rule_name, "message": r.message, "details": r.details} for r in infos],
            "summary": {
                "error_count": len(errors),
                "warning_count": len(warnings),
                "info_count": len(infos)
            }
        }
    
    def _add_result(self, rule_name: str, level: ValidationLevel, message: str, details: Dict = None):
        """添加验证结果"""
        self.results.append(ValidationResult(
            rule_name=rule_name,
            level=level,
            message=message,
            details=details or {}
        ))
    
    # ==================== 基础验证方法 ====================
    
    def _validate_dataframe_not_empty(self, data: pd.DataFrame, params: Dict):
        """验证数据框不为空"""
        if data.empty:
            self._add_result("dataframe_not_empty", ValidationLevel.ERROR, "数据框为空")
    
    def _validate_required_columns(self, data: pd.DataFrame, params: Dict):
        """验证必需列存在"""
        # 从配置管理器获取必需列
        from src.core.config_manager import get_config_manager
        config = get_config_manager()
        required_cols = config.get_required_columns(self.lottery_type)

        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            self._add_result("required_columns", ValidationLevel.ERROR,
                           f"缺少必需列: {', '.join(missing_cols)}")
    
    def _validate_date_format(self, data: pd.DataFrame, params: Dict):
        """验证日期格式"""
        if 'draw_date' not in data.columns:
            return
        
        try:
            pd.to_datetime(data['draw_date'])
        except Exception as e:
            self._add_result("date_format", ValidationLevel.ERROR, 
                           f"日期格式错误: {str(e)}")
    
    def _validate_date_range(self, data: pd.DataFrame, params: Dict):
        """验证日期范围"""
        if 'draw_date' not in data.columns:
            return
        
        try:
            dates = pd.to_datetime(data['draw_date'])
            min_date = self.config_manager.get('data.date_limit', '2020-01-01')
            min_date = pd.to_datetime(min_date)
            
            old_dates = dates[dates < min_date]
            if not old_dates.empty:
                self._add_result("date_range", ValidationLevel.WARNING,
                               f"发现 {len(old_dates)} 条记录的日期早于限制日期 {min_date.date()}")
        except Exception as e:
            self._add_result("date_range", ValidationLevel.ERROR,
                           f"日期范围验证失败: {str(e)}")
    
    def _validate_issue_format(self, data: pd.DataFrame, params: Dict):
        """验证期号格式"""
        if 'draw_num' not in data.columns:
            return
        
        # 根据彩票类型验证期号格式
        if self.lottery_type == 'ssq':
            # 双色球期号应该是8位数字 (YYYYNNN)
            pattern = r'^\d{8}$'
            expected_format = "8位数字"
        elif self.lottery_type == 'dlt':
            # 大乐透期号应该是5位数字 (YYNNN)
            pattern = r'^\d{5}$'
            expected_format = "5位数字"
        else:
            # 其他类型，使用通用格式
            pattern = r'^\d{4,8}$'
            expected_format = "4-8位数字"
        
        invalid_issues = data[~data['draw_num'].astype(str).str.match(pattern)]
        if not invalid_issues.empty:
            self._add_result("issue_format", ValidationLevel.ERROR,
                           f"发现 {len(invalid_issues)} 条记录的期号格式不正确（期望{expected_format}）")
    
    def _validate_issue_uniqueness(self, data: pd.DataFrame, params: Dict):
        """验证期号唯一性"""
        if 'draw_num' not in data.columns:
            return
        
        duplicates = data[data['draw_num'].duplicated()]
        if not duplicates.empty:
            self._add_result("issue_uniqueness", ValidationLevel.ERROR,
                           f"发现 {len(duplicates)} 条重复期号记录")
    
    # ==================== 双色球验证方法 ====================
    
    def _validate_ssq_red_count(self, data: pd.DataFrame, params: Dict):
        """验证双色球红球数量"""
        if 'red_numbers' not in data.columns:
            return
        
        def check_count(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            return isinstance(numbers, (list, tuple)) and len(numbers) == 6
        
        invalid_count = data[~data['red_numbers'].apply(check_count)]
        if not invalid_count.empty:
            self._add_result("ssq_red_count", ValidationLevel.ERROR,
                           f"发现 {len(invalid_count)} 条记录的红球数量不正确")
    
    def _validate_ssq_red_range(self, data: pd.DataFrame, params: Dict):
        """验证双色球红球范围"""
        if 'red_numbers' not in data.columns:
            return
        
        def check_range(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            if not isinstance(numbers, (list, tuple)):
                return False
            return all(isinstance(n, int) and 1 <= n <= 33 for n in numbers)
        
        invalid_range = data[~data['red_numbers'].apply(check_range)]
        if not invalid_range.empty:
            self._add_result("ssq_red_range", ValidationLevel.ERROR,
                           f"发现 {len(invalid_range)} 条记录的红球号码超出范围")
    
    def _validate_ssq_red_duplicates(self, data: pd.DataFrame, params: Dict):
        """验证双色球红球重复"""
        if 'red_numbers' not in data.columns:
            return
        
        def check_duplicates(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            if not isinstance(numbers, (list, tuple)):
                return False
            return len(numbers) == len(set(numbers))
        
        has_duplicates = data[~data['red_numbers'].apply(check_duplicates)]
        if not has_duplicates.empty:
            self._add_result("ssq_red_duplicates", ValidationLevel.ERROR,
                           f"发现 {len(has_duplicates)} 条记录的红球号码有重复")
    
    def _validate_ssq_blue_range(self, data: pd.DataFrame, params: Dict):
        """验证双色球蓝球范围"""
        if 'blue_number' not in data.columns:
            return
        
        def check_blue_range(number):
            try:
                if isinstance(number, str):
                    number = int(number)
                return isinstance(number, (int, float)) and 1 <= number <= 16
            except ValueError:
                return False
        
        invalid_blue = data[~data['blue_number'].apply(check_blue_range)]
        if not invalid_blue.empty:
            self._add_result("ssq_blue_range", ValidationLevel.ERROR,
                           f"发现 {len(invalid_blue)} 条记录的蓝球号码超出范围")
    
    # ==================== 大乐透验证方法 ====================
    
    def _validate_dlt_front_count(self, data: pd.DataFrame, params: Dict):
        """验证大乐透前区数量"""
        if 'front_numbers' not in data.columns:
            return
        
        def check_count(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            return isinstance(numbers, (list, tuple)) and len(numbers) == 5
        
        invalid_count = data[~data['front_numbers'].apply(check_count)]
        if not invalid_count.empty:
            self._add_result("dlt_front_count", ValidationLevel.ERROR,
                           f"发现 {len(invalid_count)} 条记录的前区号码数量不正确")
    
    def _validate_dlt_front_range(self, data: pd.DataFrame, params: Dict):
        """验证大乐透前区范围"""
        if 'front_numbers' not in data.columns:
            return
        
        def check_range(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            if not isinstance(numbers, (list, tuple)):
                return False
            return all(isinstance(n, int) and 1 <= n <= 35 for n in numbers)
        
        invalid_range = data[~data['front_numbers'].apply(check_range)]
        if not invalid_range.empty:
            self._add_result("dlt_front_range", ValidationLevel.ERROR,
                           f"发现 {len(invalid_range)} 条记录的前区号码超出范围")
    
    def _validate_dlt_back_count(self, data: pd.DataFrame, params: Dict):
        """验证大乐透后区数量"""
        if 'back_numbers' not in data.columns:
            return
        
        def check_count(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            return isinstance(numbers, (list, tuple)) and len(numbers) == 2
        
        invalid_count = data[~data['back_numbers'].apply(check_count)]
        if not invalid_count.empty:
            self._add_result("dlt_back_count", ValidationLevel.ERROR,
                           f"发现 {len(invalid_count)} 条记录的后区号码数量不正确")
    
    def _validate_dlt_back_range(self, data: pd.DataFrame, params: Dict):
        """验证大乐透后区范围"""
        if 'back_numbers' not in data.columns:
            return
        
        def check_range(numbers):
            if isinstance(numbers, str):
                try:
                    numbers = json.loads(numbers)
                except json.JSONDecodeError:
                    return False
            if not isinstance(numbers, (list, tuple)):
                return False
            return all(isinstance(n, int) and 1 <= n <= 12 for n in numbers)
        
        invalid_range = data[~data['back_numbers'].apply(check_range)]
        if not invalid_range.empty:
            self._add_result("dlt_back_range", ValidationLevel.ERROR,
                           f"发现 {len(invalid_range)} 条记录的后区号码超出范围")
    
    # ==================== 新增验证方法 ====================
    
    def _validate_data_types(self, data: pd.DataFrame, params: Dict):
        """验证数据类型（增强版）"""
        type_errors = []

        # 检查期号列
        if 'draw_num' in data.columns:
            if data['draw_num'].dtype not in ['object', 'string', 'int64']:
                type_errors.append(f"期号列类型异常: {data['draw_num'].dtype}")

        # 检查日期列
        if 'draw_date' in data.columns:
            try:
                pd.to_datetime(data['draw_date'])
            except ValueError:
                type_errors.append("日期列格式不正确")

        # 检查号码列表类型（双色球）
        if self.lottery_type == 'ssq':
            if 'red_numbers' in data.columns:
                invalid_types = self._validate_number_list_type(data, 'red_numbers', 6)
                if invalid_types:
                    type_errors.append(f"红球号码列表类型错误: {invalid_types}条记录")

            if 'blue_number' in data.columns:
                invalid_types = self._validate_number_type(data, 'blue_number')
                if invalid_types:
                    type_errors.append(f"蓝球号码类型错误: {invalid_types}条记录")

        # 检查号码列表类型（大乐透）
        elif self.lottery_type == 'dlt':
            if 'front_numbers' in data.columns:
                invalid_types = self._validate_number_list_type(data, 'front_numbers', 5)
                if invalid_types:
                    type_errors.append(f"前区号码列表类型错误: {invalid_types}条记录")

            if 'back_numbers' in data.columns:
                invalid_types = self._validate_number_list_type(data, 'back_numbers', 2)
                if invalid_types:
                    type_errors.append(f"后区号码列表类型错误: {invalid_types}条记录")

        # 检查数值字段类型
        numeric_fields = ['prize_pool', 'sales', 'total_sales']
        for field in numeric_fields:
            if field in data.columns:
                # 尝试转换为数值类型
                try:
                    pd.to_numeric(data[field], errors='coerce')
                except Exception as e:
                    type_errors.append(f"{field}列无法转换为数值类型: {str(e)}")

        if type_errors:
            self._add_result(
                "data_types",
                ValidationLevel.ERROR,
                f"数据类型错误: {'; '.join(type_errors)}",
                {"type_errors": type_errors}
            )

    def _validate_number_list_type(self, data: pd.DataFrame, column: str, expected_count: int) -> int:
        """验证号码列表类型

        Args:
            data: 数据框
            column: 列名
            expected_count: 期望的号码数量

        Returns:
            无效记录数
        """
        invalid_count = 0

        for idx, value in data[column].items():
            # 检查是否为列表类型
            if not isinstance(value, (list, tuple)):
                invalid_count += 1
                continue

            # 检查列表长度
            if len(value) != expected_count:
                invalid_count += 1
                continue

            # 检查列表元素是否为整数
            try:
                for num in value:
                    if not isinstance(num, (int, np.integer)):
                        invalid_count += 1
                        break
            except Exception:
                invalid_count += 1

        return invalid_count

    def _validate_number_type(self, data: pd.DataFrame, column: str) -> int:
        """验证单个号码类型

        Args:
            data: 数据框
            column: 列名

        Returns:
            无效记录数
        """
        invalid_count = 0

        for idx, value in data[column].items():
            if not isinstance(value, (int, np.integer)):
                invalid_count += 1

        return invalid_count
    
    def _validate_data_completeness(self, data: pd.DataFrame, params: Dict):
        """验证数据完整性"""
        completeness_issues = []
        
        # 检查空值
        null_counts = data.isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                percentage = (count / len(data)) * 100
                completeness_issues.append(f"{col}列有{count}个空值 ({percentage:.1f}%)")
        
        # 检查重复行（只检查可哈希的列）
        try:
            # 选择可以用于重复检查的列（排除包含列表的列）
            hashable_cols = []
            for col in data.columns:
                try:
                    # 尝试对第一个非空值进行哈希
                    first_value = data[col].dropna().iloc[0] if not data[col].dropna().empty else None
                    if first_value is not None:
                        hash(first_value)
                    hashable_cols.append(col)
                except (TypeError, AttributeError):
                    # 跳过不可哈希的列（如包含列表的列）
                    continue
            
            if hashable_cols:
                duplicate_count = data[hashable_cols].duplicated().sum()
                if duplicate_count > 0:
                    completeness_issues.append(f"发现{duplicate_count}行重复数据")
        except Exception:
            # 如果重复检查失败，跳过这个检查
            pass
        
        if completeness_issues:
            self._add_result(
                "data_completeness",
                ValidationLevel.WARNING,
                f"数据完整性问题: {'; '.join(completeness_issues)}",
                {"issues": completeness_issues}
            )
    
    def _validate_outliers(self, data: pd.DataFrame, params: Dict):
        """验证异常值"""
        outlier_issues = []
        
        # 检查数值列的异常值
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in ['blue_number']:  # 对于号码列进行特殊处理
                continue
            
            if len(data[col].dropna()) < 4:  # 数据太少无法计算四分位数
                continue
                
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0:  # 避免除零错误
                continue
                
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
            if len(outliers) > 0:
                outlier_issues.append(f"{col}列发现{len(outliers)}个异常值")
        
        if outlier_issues:
            self._add_result(
                "outlier_detection",
                ValidationLevel.WARNING,
                f"异常值检测: {'; '.join(outlier_issues)}",
                {"issues": outlier_issues}
            )
    
    def _validate_date_sequence(self, data: pd.DataFrame, params: Dict):
        """验证日期序列"""
        if 'draw_date' not in data.columns or len(data) < 2:
            return
        
        try:
            dates = pd.to_datetime(data['draw_date']).sort_values()
            
            # 检查日期间隔
            date_diffs = dates.diff().dropna()
            
            # 检查是否有异常的日期间隔
            if len(date_diffs) > 0:
                median_diff = date_diffs.median()
                large_gaps = date_diffs[date_diffs > median_diff * 3]
                
                if len(large_gaps) > 0:
                    self._add_result(
                        "date_sequence",
                        ValidationLevel.WARNING,
                        f"发现{len(large_gaps)}个异常的日期间隔",
                        {"large_gaps": len(large_gaps)}
                    )
        except Exception as e:
            self._add_result(
                "date_sequence",
                ValidationLevel.WARNING,
                f"日期序列验证失败: {str(e)}"
            )
    
    def _validate_issue_sequence(self, data: pd.DataFrame, params: Dict):
        """验证期号序列"""
        if 'draw_num' not in data.columns or len(data) < 2:
            return
        
        try:
            # 提取年份和期号
            issues = data['draw_num'].astype(str)
            years = issues.str[:4].astype(int)
            periods = issues.str[4:].astype(int)
            
            # 检查期号连续性
            sequence_issues = []
            for year in years.unique():
                year_data = periods[years == year].sort_values()
                if len(year_data) > 1:
                    gaps = year_data.diff().dropna()
                    large_gaps = gaps[gaps > 1]
                    if len(large_gaps) > 0:
                        sequence_issues.append(f"{year}年期号序列有{len(large_gaps)}个跳跃")
            
            if sequence_issues:
                self._add_result(
                    "issue_sequence",
                    ValidationLevel.WARNING,
                    f"期号序列问题: {'; '.join(sequence_issues)}",
                    {"issues": sequence_issues}
                )
        except Exception as e:
            self._add_result(
                "issue_sequence",
                ValidationLevel.WARNING,
                f"期号序列验证失败: {str(e)}"
            )

# 便捷函数
def validate_lottery_data(data: Union[pd.DataFrame, Dict, List], lottery_type: str) -> Dict[str, Any]:
    """验证彩票数据的便捷函数"""
    validator = DataValidator(lottery_type)
    return validator.validate(data)

def validate_single_number(numbers: Dict[str, Any], lottery_type: str) -> Dict[str, Any]:
    """验证单个号码组合"""
    data = pd.DataFrame([numbers])
    return validate_lottery_data(data, lottery_type)
