#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
异常处理系统
定义项目中使用的自定义异常类
"""

class LotteryError(Exception):
    """彩票系统基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class DataError(LotteryError):
    """数据相关异常"""
    pass

class DataNotFoundError(DataError):
    """数据未找到异常"""
    pass

class DataValidationError(DataError):
    """数据验证异常"""
    pass

class DataFormatError(DataError):
    """数据格式异常"""
    pass

class DataCleaningError(DataError):
    """数据清洗异常"""
    pass

class ConfigError(LotteryError):
    """配置相关异常"""
    pass

class ConfigNotFoundError(ConfigError):
    """配置未找到异常"""
    pass

class ConfigValidationError(ConfigError):
    """配置验证异常"""
    pass

class AnalysisError(LotteryError):
    """分析相关异常"""
    pass

class FeatureError(LotteryError):
    """特征工程相关异常"""
    pass

class ModelError(LotteryError):
    """模型相关异常"""
    pass

class ModelTrainingError(ModelError):
    """模型训练异常"""
    pass

class ModelPredictionError(ModelError):
    """模型预测异常"""
    pass

class GeneratorError(LotteryError):
    """号码生成相关异常"""
    pass

class ValidationError(LotteryError):
    """验证相关异常"""
    pass

class NumberValidationError(ValidationError):
    """号码验证异常"""
    pass

class UIError(LotteryError):
    """界面相关异常"""
    pass

def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LotteryError:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 将其他异常包装为LotteryError
            raise LotteryError(f"未知错误: {str(e)}") from e
    return wrapper 