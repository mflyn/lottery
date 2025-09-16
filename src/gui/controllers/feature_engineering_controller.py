from typing import Dict, Callable
import pandas as pd
from ...core.features.feature_engineering import FeatureEngineering

class FeatureEngineeringController:
    """特征工程控制器 - 用于连接GUI和核心逻辑"""
    
    def __init__(self):
        self.feature_engineering = None
        self.callbacks = {
            'on_feature_generated': [],
            'on_feature_selected': [],
            'on_error': []
        }
        
    def initialize(self, lottery_type: str):
        """初始化特征工程控制器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
        """
        try:
            self.feature_engineering = FeatureEngineering(lottery_type)
            return True
        except Exception as e:
            self._notify_error(f"初始化特征工程失败: {str(e)}")
            return False
            
    def register_callback(self, event_type: str, callback: Callable):
        """注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            
    def generate_features(self, periods: int = 100):
        """生成特征
        
        Args:
            periods: 处理的期数
        """
        try:
            if not self.feature_engineering:
                raise ValueError("请先初始化特征工程控制器")
                
            result = self.feature_engineering.generate_features(periods)
            self._notify_feature_generated(result)
            return result
        except Exception as e:
            self._notify_error(f"生成特征失败: {str(e)}")
            return None
            
    def select_features(self, features_df: pd.DataFrame, target: pd.Series, 
                       method: str = 'mutual_info', k: int = 10):
        """特征选择
        
        Args:
            features_df: 特征DataFrame
            target: 目标变量
            method: 选择方法
            k: 选择的特征数量
        """
        try:
            if not self.feature_engineering:
                raise ValueError("请先初始化特征工程控制器")
                
            selected_features = self.feature_engineering.select_features(
                features_df, target, method, k
            )
            self._notify_feature_selected(selected_features)
            return selected_features
        except Exception as e:
            self._notify_error(f"特征选择失败: {str(e)}")
            return None
            
    def get_feature_importance_report(self):
        """获取特征重要性报告"""
        try:
            if not self.feature_engineering:
                raise ValueError("请先初始化特征工程控制器")
                
            return self.feature_engineering.get_feature_importance_report()
        except Exception as e:
            self._notify_error(f"获取特征重要性报告失败: {str(e)}")
            return None
            
    def _notify_feature_generated(self, result: Dict):
        """通知特征生成完成"""
        for callback in self.callbacks['on_feature_generated']:
            callback(result)
            
    def _notify_feature_selected(self, selected_features: pd.DataFrame):
        """通知特征选择完成"""
        for callback in self.callbacks['on_feature_selected']:
            callback(selected_features)
            
    def _notify_error(self, error_message: str):
        """通知错误"""
        for callback in self.callbacks['on_error']:
            callback(error_message)