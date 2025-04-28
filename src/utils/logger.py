import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class Logger:
    """日志管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._setup_logger()
        
    def _setup_logger(self):
        """配置日志系统"""
        # 创建日志目录
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志文件名
        current_date = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'lottery_tools_{current_date}.log')
        
        # 创建logger
        self.logger = logging.getLogger('LotteryTools')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器 - 记录所有日志
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 错误日志处理器 - 只记录错误和严重错误
        error_log = os.path.join(log_dir, f'error_{current_date}.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
        
    def info(self, message: str, *args, **kwargs):
        """记录一般信息"""
        self.logger.info(message, *args, **kwargs)
        
    def warning(self, message: str, *args, **kwargs):
        """记录警告信息"""
        self.logger.warning(message, *args, **kwargs)
        
    def error(self, message: str, error: Optional[Exception] = None, *args, **kwargs):
        """记录错误信息"""
        if error:
            message = f"{message}: {str(error)}"
        self.logger.error(message, *args, **kwargs)
        
    def critical(self, message: str, error: Optional[Exception] = None, *args, **kwargs):
        """记录严重错误信息"""
        if error:
            message = f"{message}: {str(error)}"
        self.logger.critical(message, *args, **kwargs)
