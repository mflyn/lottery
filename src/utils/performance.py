import time
import psutil
import functools
from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import tracemalloc
from src.utils.logger import Logger

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    function_name: str

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = Logger()
        self.metrics_history = []
        self._start_monitoring()
        
    def _start_monitoring(self):
        """启动性能监控"""
        tracemalloc.start()
        self.process = psutil.Process()
        
    def get_current_memory_usage(self) -> float:
        """获取当前内存使用情况"""
        current, peak = tracemalloc.get_traced_memory()
        return current / 1024 / 1024  # 转换为MB
        
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return self.process.cpu_percent()
        
    def record_metrics(self, metrics: PerformanceMetrics):
        """记录性能指标"""
        self.metrics_history.append(metrics)
        self._log_metrics(metrics)
        
    def _log_metrics(self, metrics: PerformanceMetrics):
        """记录性能日志"""
        self.logger.info(
            f"Performance metrics for {metrics.function_name}:\n"
            f"Execution time: {metrics.execution_time:.2f}s\n"
            f"Memory usage: {metrics.memory_usage:.2f}MB\n"
            f"CPU usage: {metrics.cpu_usage:.2f}%"
        )
        
    def get_performance_report(self) -> dict:
        """生成性能报告"""
        if not self.metrics_history:
            return {}
            
        total_time = sum(m.execution_time for m in self.metrics_history)
        avg_memory = sum(m.memory_usage for m in self.metrics_history) / len(self.metrics_history)
        avg_cpu = sum(m.cpu_usage for m in self.metrics_history) / len(self.metrics_history)
        
        return {
            'total_execution_time': total_time,
            'average_memory_usage': avg_memory,
            'average_cpu_usage': avg_cpu,
            'number_of_operations': len(self.metrics_history)
        }

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, threshold_mb: float = 100):
        self.threshold_mb = threshold_mb
        self.logger = Logger()
        
    def check_memory_usage(self):
        """检查内存使用情况"""
        current_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        if current_usage > self.threshold_mb:
            self.optimize_memory()
            
    def optimize_memory(self):
        """执行内存优化"""
        import gc
        gc.collect()
        self.logger.info("Memory optimization performed")

def performance_timer(func: Callable) -> Callable:
    """性能计时装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        start_memory = monitor.get_current_memory_usage()
        start_cpu = monitor.get_cpu_usage()
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            end_memory = monitor.get_current_memory_usage()
            end_cpu = monitor.get_cpu_usage()
            
            metrics = PerformanceMetrics(
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu,
                timestamp=datetime.now(),
                function_name=func.__name__
            )
            
            monitor.record_metrics(metrics)
            
        return result
    return wrapper

def memory_tracker(threshold_mb: float = 100):
    """内存跟踪装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            optimizer = MemoryOptimizer(threshold_mb)
            
            try:
                result = func(*args, **kwargs)
            finally:
                optimizer.check_memory_usage()
                
            return result
        return wrapper
    return decorator
