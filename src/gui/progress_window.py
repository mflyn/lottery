import tkinter as tk
from tkinter import ttk

class ProgressWindow(tk.Toplevel):
    """进度窗口"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        
        # 使窗口置顶
        self.transient(parent)
        self.grab_set()
        
        # 创建进度条
        self.progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            length=250,
            mode='determinate'
        )
        self.progress.pack(pady=20)
        
        # 状态标签
        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=10)
    
    def update_progress(self, value):
        """更新进度"""
        self.progress['value'] = value
        self.update()
    
    def update_status(self, text):
        """更新状态文本"""
        self.status_label['text'] = text
        self.update()
    
    def show(self):
        """显示窗口"""
        self.deiconify()
        self.focus_set()
    
    def close(self):
        """关闭窗口"""
        self.grab_release()
        self.destroy()