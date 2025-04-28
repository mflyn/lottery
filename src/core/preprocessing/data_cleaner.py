from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.impute import SimpleImputer
import logging

class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.imputer = SimpleImputer(strategy='median')
        
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行完整的数据清洗流程
        
        Args:
            data: 原始数据DataFrame
            
        Returns:
            清洗后的DataFrame
        """
        try:
            df = data.copy()
            
            # 1. 基础清洗
            df = self._basic_cleaning(df)
            
            # 2. 数据验证
            df = self._validate_data(df)
            
            # 3. 格式标准化
            df = self._standardize_formats(df)
            
            # 4. 处理异常值
            df = self._handle_outliers(df)
            
            # 5. 数据一致性检查
            df = self._ensure_consistency(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {str(e)}")
            raise
            
    def _basic_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """基础数据清洗"""
        # 删除重复行
        df = df.drop_duplicates()
        
        # 删除全空的行
        df = df.dropna(how='all')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
        
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据验证"""
        # 验证必需列
        required_columns = ['date', 'red_numbers', 'blue_number']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必需列: {missing_columns}")
            
        # 验证数据类型
        df['date'] = pd.to_datetime(df['date'])
        
        # 验证号码格式
        df = self._validate_numbers(df)
        
        return df
        
    def _validate_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证号码格式"""
        def validate_red_numbers(numbers):
            if isinstance(numbers, str):
                numbers = eval(numbers)
            if not isinstance(numbers, (list, tuple)) or len(numbers) != 6:
                raise ValueError("红球格式错误")
            return sorted([int(n) for n in numbers])
            
        def validate_blue_number(number):
            if isinstance(number, str):
                number = int(number)
            if not isinstance(number, (int, float)) or number < 1 or number > 16:
                raise ValueError("蓝球格式错误")
            return int(number)
            
        df['red_numbers'] = df['red_numbers'].apply(validate_red_numbers)
        df['blue_number'] = df['blue_number'].apply(validate_blue_number)
        
        return df
        
    def _standardize_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 标准化日期格式
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # 提取红球数字特征
        for i in range(6):
            df[f'red_{i+1}'] = df['red_numbers'].apply(lambda x: x[i])
            
        # 计算红球和值
        df['red_sum'] = df['red_numbers'].apply(sum)
        
        # 计算红球跨度
        df['red_span'] = df['red_numbers'].apply(lambda x: max(x) - min(x))
        
        return df
        
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理异常值"""
        numerical_columns = ['red_sum', 'red_span']
        
        for col in numerical_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 记录异常值
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if not outliers.empty:
                self.logger.warning(f"列 {col} 发现 {len(outliers)} 个异常值")
                
            # 截断异常值
            df[col] = df[col].clip(lower_bound, upper_bound)
            
        return df
        
    def _ensure_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """确保数据一致性"""
        # 检查日期连续性
        date_gaps = pd.date_range(
            start=df['date'].min(),
            end=df['date'].max()
        ).difference(pd.DatetimeIndex(df['date']))
        
        if not date_gaps.empty:
            self.logger.warning(f"发现 {len(date_gaps)} 个日期缺失")
            
        # 检查号码范围
        invalid_red = df[~df['red_numbers'].apply(
            lambda x: all(1 <= n <= 33 for n in x)
        )]
        if not invalid_red.empty:
            self.logger.error(f"发现 {len(invalid_red)} 个红球号码超出范围")
            
        invalid_blue = df[~df['blue_number'].between(1, 16)]
        if not invalid_blue.empty:
            self.logger.error(f"发现 {len(invalid_blue)} 个蓝球号码超出范围")
            
        return df
        
    def get_data_quality_report(self, df: pd.DataFrame) -> Dict:
        """生成数据质量报告"""
        return {
            'total_records': len(df),
            'duplicates': len(df[df.duplicated()]),
            'missing_values': df.isnull().sum().to_dict(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max(),
                'periods': len(df)
            },
            'value_ranges': {
                'red_sum': {
                    'min': df['red_sum'].min(),
                    'max': df['red_sum'].max(),
                    'mean': df['red_sum'].mean()
                },
                'blue_number': {
                    'min': df['blue_number'].min(),
                    'max': df['blue_number'].max(),
                    'mode': df['blue_number'].mode()[0]
                }
            }
        }