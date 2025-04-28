from typing import Dict, Optional, Callable
from datetime import datetime
import time
import threading
from queue import Queue
import logging

class ProgressTracker:
    """特征工程进度跟踪器"""
    
    def __init__(self):
        self.total_steps = 0
        self.current_step = 0
        self.start_time = None
        self.end_time = None
        self.status = "not_started"  # not_started, running, completed, failed
        self.error = None
        self.step_details: Dict[str, Dict] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._update_queue = Queue()
        self._stop_event = threading.Event()
        
        # 启动更新处理线程
        self._update_thread = threading.Thread(target=self._process_updates)
        self._update_thread.daemon = True
        self._update_thread.start()

    def initialize(self, total_steps: int, step_names: Optional[Dict[int, str]] = None):
        """初始化进度跟踪"""
        with self._lock:
            self.total_steps = total_steps
            self.current_step = 0
            self.start_time = datetime.now()
            self.status = "running"
            self.error = None
            self.step_details.clear()
            
            if step_names:
                for step, name in step_names.items():
                    self.step_details[name] = {
                        "status": "pending",
                        "start_time": datetime.now(),  # 初始化开始时间
                        "end_time": None,
                        "duration": None,
                        "progress": 0.0
                    }

    def update(self, step_name: str, progress: float, status: str = "running"):
        """更新特定步骤的进度"""
        if not 0 <= progress <= 1:
            raise ValueError("Progress must be between 0 and 1")
            
        self._update_queue.put(("step_update", {
            "step_name": step_name,
            "progress": progress,
            "status": status
        }))

    def complete_step(self, step_name: str):
        """标记步骤完成"""
        self._update_queue.put(("step_complete", {
            "step_name": step_name
        }))

    def fail_step(self, step_name: str, error: str):
        """标记步骤失败"""
        self._update_queue.put(("step_fail", {
            "step_name": step_name,
            "error": error
        }))

    def register_callback(self, event: str, callback: Callable):
        """注册进度更新回调函数"""
        self._callbacks[event] = callback

    def get_progress(self) -> Dict:
        """获取当前进度信息"""
        with self._lock:
            current_time = datetime.now()
            duration = None
            if self.start_time:
                duration = (current_time - self.start_time).total_seconds()
                
            return {
                "total_steps": self.total_steps,
                "current_step": self.current_step,
                "overall_progress": self.current_step / self.total_steps if self.total_steps > 0 else 0,
                "status": self.status,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": duration,
                "step_details": self.step_details.copy()
            }

    def _process_updates(self):
        """处理进度更新队列"""
        while not self._stop_event.is_set():
            try:
                try:
                    update_type, data = self._update_queue.get(timeout=1)
                except:
                    continue
                
                with self._lock:
                    if update_type == "step_update":
                        step_name = data["step_name"]
                        if step_name in self.step_details:
                            current_time = datetime.now()
                            self.step_details[step_name].update({
                                "status": data["status"],
                                "progress": data["progress"],
                                "last_update": current_time
                            })
                        
                    elif update_type == "step_complete":
                        step_name = data["step_name"]
                        if step_name in self.step_details:
                            current_time = datetime.now()
                            start_time = self.step_details[step_name]["start_time"]
                            duration = (current_time - start_time).total_seconds() if start_time else 0
                        
                            self.step_details[step_name].update({
                                "status": "completed",
                                "progress": 1.0,
                                "end_time": current_time,
                                "duration": duration
                            })
                            self.current_step += 1
                        
                            # 检查是否所有步骤都已完成
                            if self.current_step == self.total_steps:
                                self.status = "completed"
                                self.end_time = current_time
                        
                    elif update_type == "step_fail":
                        step_name = data["step_name"]
                        if step_name in self.step_details:
                            current_time = datetime.now()
                            self.step_details[step_name].update({
                                "status": "failed",
                                "error": data["error"],
                                "end_time": current_time
                            })
                            self.status = "failed"
                            self.error = data["error"]
            
                # 触发回调
                if update_type in self._callbacks:
                    try:
                        self._callbacks[update_type](data)
                    except Exception as e:
                        logging.error(f"Error in callback: {str(e)}")
                
            except Exception as e:
                logging.error(f"Error processing progress update: {str(e)}")

    def stop(self):
        """停止进度跟踪"""
        self._stop_event.set()
        if self._update_thread.is_alive():
            self._update_thread.join()
        self.end_time = datetime.now()
