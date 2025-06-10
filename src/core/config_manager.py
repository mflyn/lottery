#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理器
统一管理应用程序的所有配置项
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(__name__)
        
        # 默认配置文件路径
        if config_file is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "app_config.json"
        
        self.config_file = Path(config_file)
        self._default_config = self._get_default_config()
        self._config = self._load_config()
        
        # 如果配置文件不存在，创建它
        if not self.config_file.exists():
            self.save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 数据相关配置
            "data": {
                "data_path": "data",
                "date_limit": "2020-01-01",
                "cache_ttl_hours": 24,
                "max_periods": 1000
            },
            
            # 网络请求配置
            "network": {
                "timeout": 30,
                "max_retry": 3,
                "retry_delay": 1,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "verify_ssl": True
            },
            
            # 彩票类型配置
            "lottery": {
                "supported_types": ["ssq", "dlt"],
                "default_type": "ssq",
                "ssq": {
                    "name": "双色球",
                    "red_range": [1, 33],
                    "blue_range": [1, 16],
                    "red_count": 6,
                    "blue_count": 1,
                    "basic_price": 2
                },
                "dlt": {
                    "name": "大乐透",
                    "front_range": [1, 35],
                    "back_range": [1, 12],
                    "front_count": 5,
                    "back_count": 2,
                    "basic_price": 2,
                    "additional_price": 1
                }
            },
            
            # 界面配置
            "ui": {
                "window_width": 1000,
                "window_height": 700,
                "min_width": 800,
                "min_height": 600,
                "theme": "default",
                "font_size": 10,
                "language": "zh_CN"
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",
                "log_dir": "logs",
                "max_log_files": 10,
                "max_log_size_mb": 10
            },
            
            # 分析配置
            "analysis": {
                "default_periods": 100,
                "hot_cold_threshold": 3,
                "feature_cache_size": 1000
            },
            
            # API配置
            "api": {
                "ssq_url": "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice",
                "dlt_url": "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry",
                "page_size": 30,
                "max_pages": 100
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                return self._merge_config(self._default_config, config)
            else:
                # 如果配置文件不存在，使用默认配置并稍后保存
                default_config = self._default_config.copy()
                # 延迟保存，避免在_config未设置时调用save_config
                return default_config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self._default_config.copy()
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和用户配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'data.data_path'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加保存时间戳
            config_to_save = self._config.copy()
            config_to_save['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self._config = self._default_config.copy()
        self.save_config()
    
    def get_lottery_config(self, lottery_type: str) -> Dict[str, Any]:
        """获取特定彩票类型的配置
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
            
        Returns:
            彩票配置字典
        """
        return self.get(f'lottery.{lottery_type}', {})
    
    def get_data_path(self) -> str:
        """获取数据路径"""
        return self.get('data.data_path', 'data')
    
    def get_network_config(self) -> Dict[str, Any]:
        """获取网络配置"""
        return self.get('network', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取界面配置"""
        return self.get('ui', {})
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置的有效性
        
        Returns:
            验证结果字典，包含 'valid' 和 'errors' 键
        """
        errors = []
        
        # 验证数据路径
        data_path = self.get('data.data_path')
        if not data_path:
            errors.append("数据路径不能为空")
        
        # 验证网络超时
        timeout = self.get('network.timeout')
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("网络超时必须是正数")
        
        # 验证彩票类型配置
        for lottery_type in self.get('lottery.supported_types', []):
            config = self.get_lottery_config(lottery_type)
            if not config:
                errors.append(f"缺少彩票类型 {lottery_type} 的配置")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# 全局配置实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """快捷方式：获取配置值"""
    return get_config_manager().get(key, default)

def set_config(key: str, value: Any) -> None:
    """快捷方式：设置配置值"""
    get_config_manager().set(key, value) 