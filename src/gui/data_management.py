import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from typing import Optional
import json
import csv

class DataManagementFrame(ttk.Frame):
    """数据管理框架"""
    
    def __init__(self, master, data_manager):
        super().__init__(master)
        self.data_manager = data_manager
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 数据概览区域
        overview_frame = ttk.LabelFrame(self, text="数据概览")
        overview_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.overview_text = tk.Text(overview_frame, height=5, width=50)
        self.overview_text.pack(padx=5, pady=5)
        
        # 数据操作区域
        operations_frame = ttk.LabelFrame(self, text="数据操作")
        operations_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 导入按钮
        import_frame = ttk.Frame(operations_frame)
        import_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(import_frame, text="导入数据:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            import_frame,
            text="CSV文件",
            command=lambda: self._import_data("csv")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            import_frame,
            text="Excel文件",
            command=lambda: self._import_data("excel")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            import_frame,
            text="JSON文件",
            command=lambda: self._import_data("json")
        ).pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        export_frame = ttk.Frame(operations_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(export_frame, text="导出数据:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            export_frame,
            text="导出CSV",
            command=lambda: self._export_data("csv")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            export_frame,
            text="导出Excel",
            command=lambda: self._export_data("excel")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            export_frame,
            text="导出JSON",
            command=lambda: self._export_data("json")
        ).pack(side=tk.LEFT, padx=5)
        
        # 数据清理按钮
        cleanup_frame = ttk.Frame(operations_frame)
        cleanup_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            cleanup_frame,
            text="清理重复数据",
            command=self._cleanup_duplicates
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            cleanup_frame,
            text="修复缺失数据",
            command=self._fix_missing_data
        ).pack(side=tk.LEFT, padx=5)
        
        # 更新数据概览
        self._update_overview()
        
    def _import_data(self, file_type: str):
        """导入数据"""
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "excel": [("Excel files", "*.xlsx;*.xls")],
            "json": [("JSON files", "*.json")]
        }
        
        filename = filedialog.askopenfilename(
            title=f"选择{file_type.upper()}文件",
            filetypes=filetypes[file_type]
        )
        
        if filename:
            try:
                if file_type == "csv":
                    data = pd.read_csv(filename)
                elif file_type == "excel":
                    data = pd.read_excel(filename)
                else:  # json
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = pd.DataFrame(json.load(f))
                        
                # 验证数据格式
                if self._validate_data_format(data):
                    # 导入数据
                    self.data_manager.import_data(data)
                    messagebox.showinfo("成功", "数据导入成功!")
                    self._update_overview()
                else:
                    messagebox.showerror("错误", "数据格式不正确!")
                    
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
                
    def _export_data(self, file_type: str):
        """导出数据"""
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "excel": [("Excel files", "*.xlsx")],
            "json": [("JSON files", "*.json")]
        }
        
        filename = filedialog.asksaveasfilename(
            title=f"保存{file_type.upper()}文件",
            filetypes=filetypes[file_type],
            defaultextension=f".{file_type}"
        )
        
        if filename:
            try:
                data = self.data_manager.export_data()
                
                if file_type == "csv":
                    data.to_csv(filename, index=False)
                elif file_type == "excel":
                    data.to_excel(filename, index=False)
                else:  # json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data.to_dict('records'), f, ensure_ascii=False, indent=2)
                        
                messagebox.showinfo("成功", "数据导出成功!")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
                
    def _cleanup_duplicates(self):
        """清理重复数据"""
        try:
            removed_count = self.data_manager.remove_duplicates()
            messagebox.showinfo("成功", f"已清理{removed_count}条重复数据")
            self._update_overview()
        except Exception as e:
            messagebox.showerror("错误", f"清理失败: {str(e)}")
            
    def _fix_missing_data(self):
        """修复缺失数据"""
        try:
            fixed_count = self.data_manager.fix_missing_data()
            messagebox.showinfo("成功", f"已修复{fixed_count}条缺失数据")
            self._update_overview()
        except Exception as e:
            messagebox.showerror("错误", f"修复失败: {str(e)}")
            
    def _update_overview(self):
        """更新数据概览"""
        stats = self.data_manager.get_data_stats()
        
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, 
            f"数据总量: {stats['total_records']}条\n"
            f"大乐透数据: {stats['dlt_records']}条\n"
            f"双色球数据: {stats['ssq_records']}条\n"
            f"数据时间范围: {stats['date_range']}\n"
            f"最后更新时间: {stats['last_updated']}"
        )
        
    def _validate_data_format(self, data: pd.DataFrame) -> bool:
        """验证数据格式"""
        required_columns = {
            'dlt': ['date', 'issue', 'front_numbers', 'back_numbers'],
            'ssq': ['date', 'issue', 'red_numbers', 'blue_number']
        }
        
        try:
            # 检查必需列
            if not all(col in data.columns for col in required_columns['dlt']) and \
               not all(col in data.columns for col in required_columns['ssq']):
                return False
            
            # 验证日期格式
            data['date'] = pd.to_datetime(data['date'])
            
            # 验证期号格式
            if not data['issue'].str.match(r'^\d{8}$').all():
                return False
            
            # 验证号码格式
            if 'front_numbers' in data.columns:  # 大乐透
                if not self._validate_dlt_numbers(data):
                    return False
            else:  # 双色球
                if not self._validate_ssq_numbers(data):
                    return False
            
            return True
        
        except Exception:
            return False

    def _validate_dlt_numbers(self, data: pd.DataFrame) -> bool:
        """验证大乐透号码格式"""
        try:
            for _, row in data.iterrows():
                front = json.loads(row['front_numbers'])
                back = json.loads(row['back_numbers'])
                
                # 验证前区号码
                if not (len(front) == 5 and 
                       all(isinstance(n, int) and 1 <= n <= 35 for n in front)):
                    return False
                
                # 验证后区号码
                if not (len(back) == 2 and 
                       all(isinstance(n, int) and 1 <= n <= 12 for n in back)):
                    return False
                
            return True
        
        except Exception:
            return False

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 标准化日期格式
        data['date'] = pd.to_datetime(data['date'])
        
        # 排序数据
        data = data.sort_values('date')
        
        # 处理号码格式
        if 'front_numbers' in data.columns:  # 大乐透
            data['front_numbers'] = data['front_numbers'].apply(
                lambda x: sorted(json.loads(x)) if isinstance(x, str) else sorted(x)
            )
            data['back_numbers'] = data['back_numbers'].apply(
                lambda x: sorted(json.loads(x)) if isinstance(x, str) else sorted(x)
            )
        else:  # 双色球
            data['red_numbers'] = data['red_numbers'].apply(
                lambda x: sorted(json.loads(x)) if isinstance(x, str) else sorted(x)
            )
        
        return data
