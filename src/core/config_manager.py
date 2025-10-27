#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理器
统一管理应用程序的所有配置项
"""

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
                    "basic_price": 2,
                    "required_columns": ["draw_date", "draw_num", "red_numbers", "blue_number"]
                },
                "dlt": {
                    "name": "大乐透",
                    "front_range": [1, 35],
                    "back_range": [1, 12],
                    "front_count": 5,
                    "back_count": 2,
                    "basic_price": 2,
                    "additional_price": 1,
                    "required_columns": ["draw_date", "draw_num", "front_numbers", "back_numbers"]
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

    def get_lottery_range(self, lottery_type: str, zone: str) -> tuple:
        """获取彩票号码范围

        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
            zone: 区域 ('red', 'blue', 'front', 'back')

        Returns:
            (min, max) 号码范围元组
        """
        config = self.get_lottery_config(lottery_type)
        range_key = f'{zone}_range'
        range_list = config.get(range_key, [1, 10])
        return tuple(range_list)

    def get_lottery_count(self, lottery_type: str, zone: str) -> int:
        """获取彩票号码数量

        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
            zone: 区域 ('red', 'blue', 'front', 'back')

        Returns:
            号码数量
        """
        config = self.get_lottery_config(lottery_type)
        count_key = f'{zone}_count'
        return config.get(count_key, 1)

    def get_lottery_price(self, lottery_type: str, price_type: str = 'basic') -> float:
        """获取彩票价格

        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
            price_type: 价格类型 ('basic' 或 'additional')

        Returns:
            价格（元）
        """
        config = self.get_lottery_config(lottery_type)
        if price_type == 'basic':
            return config.get('basic_price', 2)
        else:
            return config.get('additional_price', 1)

    def get_lottery_name(self, lottery_type: str) -> str:
        """获取彩票名称

        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')

        Returns:
            彩票名称
        """
        config = self.get_lottery_config(lottery_type)
        return config.get('name', lottery_type.upper())

    def get_required_columns(self, lottery_type: str) -> list:
        """获取必需的数据列

        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')

        Returns:
            必需列名列表
        """
        config = self.get_lottery_config(lottery_type)
        return config.get('required_columns', ['draw_date', 'draw_num'])

    def validate_config(self) -> Dict[str, Any]:
        """验证配置的有效性

        Returns:
            验证结果字典，包含 'valid'、'errors' 和 'warnings' 键
        """
        errors = []
        warnings = []

        # 1. 验证彩票配置
        lottery_errors, lottery_warnings = self._validate_lottery_configs()
        errors.extend(lottery_errors)
        warnings.extend(lottery_warnings)

        # 2. 验证数据配置
        data_errors, data_warnings = self._validate_data_config()
        errors.extend(data_errors)
        warnings.extend(data_warnings)

        # 3. 验证网络配置
        network_errors, network_warnings = self._validate_network_config()
        errors.extend(network_errors)
        warnings.extend(network_warnings)

        # 4. 验证日志配置
        logging_errors, logging_warnings = self._validate_logging_config()
        errors.extend(logging_errors)
        warnings.extend(logging_warnings)

        # 5. 验证UI配置
        ui_errors, ui_warnings = self._validate_ui_config()
        errors.extend(ui_errors)
        warnings.extend(ui_warnings)

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_lottery_configs(self) -> tuple:
        """验证彩票配置

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        # 验证支持的彩票类型
        supported_types = self.get('lottery.supported_types', [])
        if not supported_types:
            errors.append("未配置支持的彩票类型")
            return (errors, warnings)

        # 验证每个彩票类型的配置
        for lottery_type in supported_types:
            try:
                config = self.get_lottery_config(lottery_type)
                if not config:
                    errors.append(f"缺少彩票类型 '{lottery_type}' 的配置")
                    continue

                # 验证名称
                if 'name' not in config:
                    warnings.append(f"彩票类型 '{lottery_type}' 缺少名称配置")

                # 验证号码范围
                if lottery_type == 'ssq':
                    # 双色球：验证红球和蓝球范围
                    self._validate_number_range(config, 'red', errors, lottery_type)
                    self._validate_number_range(config, 'blue', errors, lottery_type)
                    self._validate_number_count(config, 'red', errors, lottery_type)
                    self._validate_number_count(config, 'blue', errors, lottery_type)
                elif lottery_type == 'dlt':
                    # 大乐透：验证前区和后区范围
                    self._validate_number_range(config, 'front', errors, lottery_type)
                    self._validate_number_range(config, 'back', errors, lottery_type)
                    self._validate_number_count(config, 'front', errors, lottery_type)
                    self._validate_number_count(config, 'back', errors, lottery_type)

                # 验证价格
                if 'basic_price' not in config:
                    errors.append(f"彩票类型 '{lottery_type}' 缺少基本价格配置")
                elif not isinstance(config['basic_price'], (int, float)) or config['basic_price'] <= 0:
                    errors.append(f"彩票类型 '{lottery_type}' 的基本价格必须是正数")

                # 验证必需列
                if 'required_columns' not in config:
                    warnings.append(f"彩票类型 '{lottery_type}' 缺少必需列配置")
                elif not isinstance(config['required_columns'], list):
                    errors.append(f"彩票类型 '{lottery_type}' 的必需列配置必须是列表")

            except Exception as e:
                errors.append(f"验证彩票类型 '{lottery_type}' 配置时出错: {str(e)}")

        return (errors, warnings)

    def _validate_number_range(self, config: dict, zone: str, errors: list, lottery_type: str):
        """验证号码范围配置"""
        range_key = f'{zone}_range'
        if range_key not in config:
            errors.append(f"彩票类型 '{lottery_type}' 缺少 '{range_key}' 配置")
            return

        range_val = config[range_key]
        if not isinstance(range_val, list) or len(range_val) != 2:
            errors.append(f"彩票类型 '{lottery_type}' 的 '{range_key}' 必须是包含2个元素的列表")
            return

        if not all(isinstance(x, int) for x in range_val):
            errors.append(f"彩票类型 '{lottery_type}' 的 '{range_key}' 必须包含整数")
            return

        if range_val[0] >= range_val[1]:
            errors.append(f"彩票类型 '{lottery_type}' 的 '{range_key}' 范围无效: {range_val}")

        if range_val[0] < 1:
            errors.append(f"彩票类型 '{lottery_type}' 的 '{range_key}' 最小值必须 >= 1")

    def _validate_number_count(self, config: dict, zone: str, errors: list, lottery_type: str):
        """验证号码数量配置"""
        count_key = f'{zone}_count'
        if count_key not in config:
            errors.append(f"彩票类型 '{lottery_type}' 缺少 '{count_key}' 配置")
            return

        count_val = config[count_key]
        if not isinstance(count_val, int) or count_val <= 0:
            errors.append(f"彩票类型 '{lottery_type}' 的 '{count_key}' 必须是正整数")

    def _validate_data_config(self) -> tuple:
        """验证数据配置

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        # 验证数据路径
        data_path = self.get('data.data_path')
        if not data_path:
            errors.append("数据路径 'data.data_path' 不能为空")

        # 验证缓存配置
        cache_enabled = self.get('data.cache_enabled')
        if cache_enabled is None:
            warnings.append("未配置数据缓存选项 'data.cache_enabled'")

        return (errors, warnings)

    def _validate_network_config(self) -> tuple:
        """验证网络配置

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        # 验证超时
        timeout = self.get('network.timeout')
        if timeout is None:
            warnings.append("未配置网络超时 'network.timeout'")
        elif not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("网络超时 'network.timeout' 必须是正数")

        # 验证重试次数
        retry_times = self.get('network.retry_times')
        if retry_times is None:
            warnings.append("未配置重试次数 'network.retry_times'")
        elif not isinstance(retry_times, int) or retry_times < 0:
            errors.append("重试次数 'network.retry_times' 必须是非负整数")

        return (errors, warnings)

    def _validate_logging_config(self) -> tuple:
        """验证日志配置

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        # 验证日志级别
        log_level = self.get('logging.level')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level is None:
            warnings.append("未配置日志级别 'logging.level'")
        elif log_level not in valid_levels:
            errors.append(f"日志级别 'logging.level' 必须是以下之一: {', '.join(valid_levels)}")

        # 验证日志路径
        log_path = self.get('logging.log_path')
        if not log_path:
            warnings.append("未配置日志路径 'logging.log_path'")

        # 验证日志文件大小
        max_bytes = self.get('logging.max_bytes')
        if max_bytes is not None:
            if not isinstance(max_bytes, int) or max_bytes <= 0:
                errors.append("日志文件最大大小 'logging.max_bytes' 必须是正整数")

        # 验证备份数量
        backup_count = self.get('logging.backup_count')
        if backup_count is not None:
            if not isinstance(backup_count, int) or backup_count < 0:
                errors.append("日志备份数量 'logging.backup_count' 必须是非负整数")

        return (errors, warnings)

    def _validate_ui_config(self) -> tuple:
        """验证UI配置

        Returns:
            (errors, warnings) 元组
        """
        errors = []
        warnings = []

        # 验证窗口大小
        window_size = self.get('ui.window_size')
        if window_size is not None:
            if not isinstance(window_size, list) or len(window_size) != 2:
                errors.append("窗口大小 'ui.window_size' 必须是包含2个元素的列表 [width, height]")
            elif not all(isinstance(x, int) and x > 0 for x in window_size):
                errors.append("窗口大小 'ui.window_size' 必须包含正整数")

        # 验证主题
        theme = self.get('ui.theme')
        if theme is not None:
            valid_themes = ['light', 'dark', 'auto']
            if theme not in valid_themes:
                warnings.append(f"UI主题 'ui.theme' 建议使用: {', '.join(valid_themes)}")

        return (errors, warnings)

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