#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志配置系统
统一管理应用程序的日志记录
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from .config_manager import get_config_manager

class LotteryLogger:
    """彩票系统日志管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self._loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志系统"""
        # 获取日志配置
        log_config = self.config_manager.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_dir = log_config.get('log_dir', 'logs')
        max_log_files = log_config.get('max_log_files', 10)
        max_log_size_mb = log_config.get('max_log_size_mb', 10)
        
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 设置根日志级别
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        
        # 文件处理器 - 应用日志
        app_log_file = log_path / 'lottery_app.log'
        app_file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_log_size_mb * 1024 * 1024,
            backupCount=max_log_files,
            encoding='utf-8'
        )
        app_file_handler.setLevel(logging.INFO)
        app_file_handler.setFormatter(detailed_formatter)
        
        # 错误日志文件处理器
        error_log_file = log_path / 'lottery_error.log'
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_log_size_mb * 1024 * 1024,
            backupCount=max_log_files,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        
        # 网络请求日志文件处理器
        network_log_file = log_path / 'lottery_network.log'
        network_file_handler = logging.handlers.RotatingFileHandler(
            network_log_file,
            maxBytes=max_log_size_mb * 1024 * 1024,
            backupCount=max_log_files,
            encoding='utf-8'
        )
        network_file_handler.setLevel(logging.DEBUG)
        network_file_handler.setFormatter(detailed_formatter)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.handlers.clear()  # 清除现有处理器
        root_logger.addHandler(console_handler)
        root_logger.addHandler(app_file_handler)
        root_logger.addHandler(error_file_handler)
        
        # 配置网络日志记录器
        network_logger = logging.getLogger('src.core.network_client')
        network_logger.addHandler(network_file_handler)
        network_logger.propagate = False  # 不传播到根日志记录器
        
        # 配置数据管理日志记录器
        data_logger = logging.getLogger('src.core.data_manager')
        data_logger.setLevel(logging.DEBUG)
        
        # 配置第三方库日志级别
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        
        self._log_startup_info()
    
    def _log_startup_info(self):
        """记录启动信息"""
        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("彩票工具集启动")
        logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info("=" * 50)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def set_level(self, level: str):
        """设置日志级别
        
        Args:
            level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        log_level = getattr(logging, level.upper())
        logging.getLogger().setLevel(log_level)
        
        # 更新配置
        self.config_manager.set('logging.level', level.upper())
        self.config_manager.save_config()
    
    def log_performance(self, func_name: str, duration: float, **kwargs):
        """记录性能信息
        
        Args:
            func_name: 函数名称
            duration: 执行时间（秒）
            **kwargs: 其他性能相关信息
        """
        logger = self.get_logger('performance')
        extra_info = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        logger.info(f"性能统计 - {func_name}: {duration:.3f}s" + 
                   (f" ({extra_info})" if extra_info else ""))
    
    def log_user_action(self, action: str, details: str = None):
        """记录用户操作
        
        Args:
            action: 操作名称
            details: 操作详情
        """
        logger = self.get_logger('user_action')
        message = f"用户操作: {action}"
        if details:
            message += f" - {details}"
        logger.info(message)
    
    def log_data_operation(self, operation: str, lottery_type: str, 
                          count: int = None, success: bool = True):
        """记录数据操作
        
        Args:
            operation: 操作类型
            lottery_type: 彩票类型
            count: 数据条数
            success: 是否成功
        """
        logger = self.get_logger('data_operation')
        status = "成功" if success else "失败"
        message = f"数据操作 - {operation} ({lottery_type}): {status}"
        if count is not None:
            message += f" - {count}条记录"
        logger.info(message)

# 全局日志管理器实例
_lottery_logger = None

def get_lottery_logger() -> LotteryLogger:
    """获取全局日志管理器实例"""
    global _lottery_logger
    if _lottery_logger is None:
        _lottery_logger = LotteryLogger()
    return _lottery_logger

def get_logger(name: str) -> logging.Logger:
    """快捷方式：获取日志记录器"""
    return get_lottery_logger().get_logger(name)

def setup_logging():
    """初始化日志系统"""
    get_lottery_logger()

# 性能监控装饰器
def log_performance(func):
    """性能监控装饰器"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            get_lottery_logger().log_performance(
                func.__name__, 
                duration,
                args_count=len(args),
                kwargs_count=len(kwargs)
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            get_lottery_logger().log_performance(
                func.__name__, 
                duration,
                error=str(e)
            )
            raise
    return wrapper 