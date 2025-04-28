from typing import Optional, Callable
from datetime import datetime

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.start_time = None
        self.current_step = None
        self.total_steps = None
        
    def start(self, total_steps: int):
        """开始跟踪"""
        self.start_time = datetime.now()
        self.total_steps = total_steps
        self.current_step = 0
        self._notify("开始处理")
        
    def update(self, step: int, message: str):
        """更新进度"""
        self.current_step = step
        self._notify(message)
        
    def finish(self):
        """完成处理"""
        duration = datetime.now() - self.start_time
        self._notify(f"处理完成，总耗时: {duration}")
        
    def _notify(self, message: str):
        """通知回调"""
        if self.callback:
            progress = (self.current_step / self.total_steps * 100) if self.total_steps else 0
            self.callback(progress, message)