from typing import Optional, Callable
import pandas as pd
import logging

class DataTransformer:
    """数据转换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.transformers = {}
        
    def add_transformer(self, column: str, transformer: Callable, **kwargs):
        """添加转换器"""
        self.transformers[column] = {
            'func': transformer,
            'params': kwargs
        }
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行数据转换"""
        df = data.copy()
        
        for column, transformer in self.transformers.items():
            if column in df.columns:
                try:
                    df[column] = transformer['func'](
                        df[column],
                        **transformer['params']
                    )
                except Exception as e:
                    self.logger.error(f"转换列 {column} 失败: {str(e)}")
                    raise
                    
        return df
        
    @staticmethod
    def to_datetime(series: pd.Series, format: Optional[str] = None) -> pd.Series:
        """转换为日期时间"""
        return pd.to_datetime(series, format=format)
        
    @staticmethod
    def to_numeric(series: pd.Series, errors: str = 'coerce') -> pd.Series:
        """转换为数值"""
        return pd.to_numeric(series, errors=errors)
        
    @staticmethod
    def to_category(series: pd.Series) -> pd.Series:
        """转换为分类"""
        return series.astype('category')
        
    @staticmethod
    def apply_format(series: pd.Series, format_func: Callable) -> pd.Series:
        """应用格式化函数"""
        return series.apply(format_func)