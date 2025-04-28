import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
from datetime import datetime
import webbrowser
import os

class PreprocessingLogWindow:
    """预处理日志查看窗口"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("预处理日志查看")
        self.window.geometry("800x600")
        
        # 设置日志目录
        self.log_dir = Path("logs/preprocessing")
        
        self._init_ui()
        self._load_log_files()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建左侧日志文件列表
        list_frame = ttk.LabelFrame(main_frame, text="日志文件")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.log_list = tk.Listbox(list_frame, width=30)
        self.log_list.pack(fill=tk.Y, expand=True)
        self.log_list.bind('<<ListboxSelect>>', self._on_select_log)
        
        # 创建右侧详情面板
        detail_frame = ttk.LabelFrame(main_frame, text="日志详情")
        detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加操作按钮
        button_frame = ttk.Frame(detail_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="查看HTML报告",
            command=self._view_html_report
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="导出HTML报告",
            command=self._export_html_report
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="删除日志",
            command=self._delete_log
        ).pack(side=tk.LEFT, padx=5)
        
        # 添加日志内容显示区域
        self.log_text = tk.Text(detail_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def _load_log_files(self):
        """加载日志文件列表"""
        self.log_list.delete(0, tk.END)
        
        if not self.log_dir.exists():
            return
        
        log_files = sorted(
            self.log_dir.glob("*.log"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for log_file in log_files:
            # 将文件修改时间添加到显示中
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            display_name = f"{mtime.strftime('%Y-%m-%d %H:%M:%S')} - {log_file.name}"
            self.log_list.insert(tk.END, display_name)
    
    def _on_select_log(self, event):
        """当选择日志文件时的处理"""
        selection = self.log_list.curselection()
        if not selection:
            return
        
        # 获取选中的日志文件名
        log_name = self.log_list.get(selection[0]).split(" - ")[1]
        log_path = self.log_dir / log_name
        
        # 清空并显示日志内容
        self.log_text.delete(1.0, tk.END)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_text.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("错误", f"读取日志文件失败: {str(e)}")
    
    def _view_html_report(self):
        """查看HTML报告"""
        selection = self.log_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个日志文件")
            return
        
        log_name = self.log_list.get(selection[0]).split(" - ")[1]
        html_path = self.log_dir / log_name.replace('.log', '.html')
        
        if not html_path.exists():
            # 如果HTML报告不存在，先生成
            self._export_html_report()
        
        # 在默认浏览器中打开HTML报告
        webbrowser.open(html_path.absolute().as_uri())
    
    def _export_html_report(self):
        """导出HTML报告"""
        selection = self.log_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个日志文件")
            return
        
        log_name = self.log_list.get(selection[0]).split(" - ")[1]
        log_path = self.log_dir / log_name
        html_path = log_path.with_suffix('.html')
        
        try:
            # 读取日志文件内容
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 使用PreprocessingLogger生成HTML报告
            from ..core.preprocessing.preprocessing_logger import PreprocessingLogger
            logger = PreprocessingLogger()
            logger.details = log_data
            logger.export_html_report(str(html_path))
            
            messagebox.showinfo("成功", "HTML报告已生成")
        except Exception as e:
            messagebox.showerror("错误", f"生成HTML报告失败: {str(e)}")
    
    def _delete_log(self):
        """删除日志文件"""
        selection = self.log_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个日志文件")
            return
        
        if not messagebox.askyesno("确认", "确定要删除选中的日志文件吗？"):
            return
        
        log_name = self.log_list.get(selection[0]).split(" - ")[1]
        log_path = self.log_dir / log_name
        html_path = log_path.with_suffix('.html')
        
        try:
            # 删除日志文件和对应的HTML报告
            if log_path.exists():
                os.remove(log_path)
            if html_path.exists():
                os.remove(html_path)
            
            # 刷新列表
            self._load_log_files()
            # 清空详情显示
            self.log_text.delete(1.0, tk.END)
            
            messagebox.showinfo("成功", "日志文件已删除")
        except Exception as e:
            messagebox.showerror("错误", f"删除日志文件失败: {str(e)}")