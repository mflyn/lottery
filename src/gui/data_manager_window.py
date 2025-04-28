import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
from ..core.validators.history_validator import HistoryValidator

class DataManagerWindow(tk.Toplevel):
    """数据管理窗口"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.title("数据管理")
        self.geometry("800x600")
        
        self.data_manager = data_manager
        self.validator = HistoryValidator()
        
        # 初始化UI
        self._init_ui()
        
        # 使窗口模态
        self.transient(parent)
        self.grab_set()
        
    def _init_ui(self):
        """初始化界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 数据类型选择
        type_frame = ttk.LabelFrame(main_frame, text="数据类型")
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lottery_type = tk.StringVar(value="dlt")
        ttk.Radiobutton(
            type_frame,
            text="大乐透",
            value="dlt",
            variable=self.lottery_type,
            command=self._update_data_view
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            type_frame,
            text="双色球",
            value="ssq",
            variable=self.lottery_type,
            command=self._update_data_view
        ).pack(side=tk.LEFT, padx=10)
        
        # 数据表格
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("期号", "开奖日期", "开奖号码", "奖池金额", "更新时间")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text="验证数据",
            command=self._validate_data
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="更新数据",
            command=self._update_data
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="导出数据",
            command=self._export_data
        ).pack(side=tk.LEFT, padx=5)
        
        # 初始显示数据
        self._update_data_view()
    
    def _update_data_view(self):
        """更新数据视图"""
        try:
            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 获取数据
            data = self.data_manager.get_lottery_data(self.lottery_type.get())
            
            # 显示数据
            for item in data:
                self.tree.insert("", tk.END, values=(
                    item['draw_number'],
                    item['draw_date'],
                    " ".join(map(str, item['numbers'])),
                    f"{item.get('prize_pool', 0):,}",
                    item['updated_at']
                ))
                
        except Exception as e:
            messagebox.showerror("错误", f"获取数据失败: {str(e)}")
    
    def _validate_data(self):
        """验证数据"""
        try:
            # 获取当前显示的数据
            data = self._get_current_data()
            
            # 执行验证
            results = self.validator.validate(data)
            
            # 清空验证结果显示
            self.validation_text.delete(1.0, tk.END)
            
            # 显示验证结果
            if results['valid']:
                self.validation_text.insert(tk.END, "✓ 数据验证通过\n", "success")
            else:
                if results['errors']:
                    self.validation_text.insert(tk.END, "错误:\n", "error")
                    for error in results['errors']:
                        self.validation_text.insert(tk.END, f"• {error}\n", "error")
                
                if results['warnings']:
                    self.validation_text.insert(tk.END, "警告:\n", "warning")
                    for warning in results['warnings']:
                        self.validation_text.insert(tk.END, f"• {warning}\n", "warning")
            
            # 配置文本标签样式
            self.validation_text.tag_configure("success", foreground="green")
            self.validation_text.tag_configure("error", foreground="red")
            self.validation_text.tag_configure("warning", foreground="orange")
            
        except Exception as e:
            messagebox.showerror("验证失败", f"数据验证过程出错: {str(e)}")

    def _get_current_data(self):
        """获取当前显示的数据，转换为DataFrame格式"""
        # 这里需要根据实际数据结构实现数据获取和转换
        # 返回pandas DataFrame
        pass

    def _update_data(self):
        """更新数据"""
        try:
            self.data_manager.update_lottery_data(self.lottery_type.get())
            self._update_data_view()
            self._validate_data()
            messagebox.showinfo("成功", "数据更新成功!")
            
        except Exception as e:
            messagebox.showerror("错误", f"更新数据失败: {str(e)}")
    
    def _export_data(self):
        """导出数据"""
        try:
            filename = f"{self.lottery_type.get()}_data_{datetime.now().strftime('%Y%m%d')}.xlsx"
            self.data_manager.export_data(filename)
            messagebox.showinfo("成功", f"数据已导出到文件: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出数据失败: {str(e)}")
