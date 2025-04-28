from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from typing import List, Dict
import pandas as pd
from src.core.ssq_analyzer import SSQAnalyzer
from src.core.strategy.number_generator import NumberGenerator

class SSQFrame(ttk.Frame):
    """双色球界面"""
    
    def __init__(self, master):
        super().__init__(master)
        self.analyzer = SSQAnalyzer()
        self.number_generator = NumberGenerator('ssq')
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 创建标签页
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')
        
        # 复式投注页
        self.complex_frame = self._create_complex_frame()
        self.notebook.add(self.complex_frame, text='复式投注')
        
        # 胆拖投注页
        self.dantuo_frame = self._create_dantuo_frame()
        self.notebook.add(self.dantuo_frame, text='胆拖投注')
        
        # 智能选号页
        self.smart_frame = self._create_smart_frame()
        self.notebook.add(self.smart_frame, text='智能选号')
        
        # 历史数据页
        self.history_frame = self._create_history_frame()
        self.notebook.add(self.history_frame, text='历史数据')
        
        # 中奖对照页
        self.prize_check_frame = self._create_prize_check_frame()
        self.notebook.add(self.prize_check_frame, text='中奖对照')
        
    def _create_complex_frame(self) -> ttk.Frame:
        """创建复式投注页"""
        frame = ttk.Frame(self.notebook)
        
        # 红球选择区
        red_frame = ttk.LabelFrame(frame, text='红球区')
        red_frame.pack(fill='x', padx=5, pady=5)
        
        self.red_vars = []
        for i in range(33):
            var = tk.BooleanVar()
            self.red_vars.append(var)
            if i % 7 == 0:
                row_frame = ttk.Frame(red_frame)
                row_frame.pack()
            cb = ttk.Checkbutton(row_frame, text=str(i+1), variable=var)
            cb.pack(side='left', padx=2)
            
        # 蓝球选择区
        blue_frame = ttk.LabelFrame(frame, text='蓝球区')
        blue_frame.pack(fill='x', padx=5, pady=5)
        
        self.blue_vars = []
        for i in range(16):
            var = tk.BooleanVar()
            self.blue_vars.append(var)
            if i % 8 == 0:
                row_frame = ttk.Frame(blue_frame)
                row_frame.pack()
            cb = ttk.Checkbutton(row_frame, text=str(i+1), variable=var)
            cb.pack(side='left', padx=2)
            
        # 计算按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text='计算注数', 
                   command=self._calculate_complex).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='清空选择',
                   command=self._clear_complex).pack(side='left', padx=5)
                   
        # 结果显示
        self.result_label = ttk.Label(frame, text='')
        self.result_label.pack(pady=5)
        
        return frame
        
    def _create_dantuo_frame(self) -> ttk.Frame:
        """创建胆拖投注页"""
        frame = ttk.Frame(self.notebook)
        
        # 红球胆码区
        red_dan_frame = ttk.LabelFrame(frame, text='红球胆码区(最多5个)')
        red_dan_frame.pack(fill='x', padx=5, pady=5)
        
        self.red_dan_vars = []
        for i in range(33):
            var = tk.BooleanVar()
            self.red_dan_vars.append(var)
            if i % 7 == 0:
                row_frame = ttk.Frame(red_dan_frame)
                row_frame.pack()
            cb = ttk.Checkbutton(row_frame, text=str(i+1), variable=var)
            cb.pack(side='left', padx=2)
            
        # 红球拖码区
        red_tuo_frame = ttk.LabelFrame(frame, text='红球拖码区')
        red_tuo_frame.pack(fill='x', padx=5, pady=5)
        
        self.red_tuo_vars = []
        for i in range(33):
            var = tk.BooleanVar()
            self.red_tuo_vars.append(var)
            if i % 7 == 0:
                row_frame = ttk.Frame(red_tuo_frame)
                row_frame.pack()
            cb = ttk.Checkbutton(row_frame, text=str(i+1), variable=var)
            cb.pack(side='left', padx=2)
            
        # 蓝球选择区
        blue_frame = ttk.LabelFrame(frame, text='蓝球区')
        blue_frame.pack(fill='x', padx=5, pady=5)
        
        self.blue_dan_vars = []
        for i in range(16):
            var = tk.BooleanVar()
            self.blue_dan_vars.append(var)
            if i % 8 == 0:
                row_frame = ttk.Frame(blue_frame)
                row_frame.pack()
            cb = ttk.Checkbutton(row_frame, text=str(i+1), variable=var)
            cb.pack(side='left', padx=2)
            
        # 计算按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text='计算注数',
                   command=self._calculate_dantuo).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='清空选择',
                   command=self._clear_dantuo).pack(side='left', padx=5)
                   
        # 结果显示
        self.dantuo_result_label = ttk.Label(frame, text='')
        self.dantuo_result_label.pack(pady=5)
        
        return frame
        
    def _create_smart_frame(self) -> ttk.Frame:
        """创建智能选号页"""
        frame = ttk.Frame(self.notebook)
        
        # 参数设置区
        param_frame = ttk.LabelFrame(frame, text='生成参数')
        param_frame.pack(fill='x', padx=5, pady=5)
        
        # 生成注数设置
        ttk.Label(param_frame, text='生成注数:').pack(side='left', padx=5)
        self.count_var = tk.StringVar(value='5')
        ttk.Entry(param_frame, textvariable=self.count_var, width=10).pack(side='left')
        
        # 生成策略选择
        ttk.Label(param_frame, text='生成策略:').pack(side='left', padx=5)
        self.strategy_var = tk.StringVar(value='hybrid')
        strategy_cb = ttk.Combobox(param_frame, textvariable=self.strategy_var, width=15)
        strategy_cb['values'] = ['random', 'frequency', 'pattern', 'hybrid']
        strategy_cb.pack(side='left', padx=5)
        
        # 高级参数设置
        advanced_frame = ttk.LabelFrame(frame, text='高级参数')
        advanced_frame.pack(fill='x', padx=5, pady=5)
        
        # 历史数据权重
        ttk.Label(advanced_frame, text='历史数据权重:').pack(side='left', padx=5)
        self.history_weight_var = tk.StringVar(value='0.5')
        ttk.Entry(advanced_frame, textvariable=self.history_weight_var, width=10).pack(side='left')
        
        # 模式匹配权重
        ttk.Label(advanced_frame, text='模式匹配权重:').pack(side='left', padx=5)
        self.pattern_weight_var = tk.StringVar(value='0.3')
        ttk.Entry(advanced_frame, textvariable=self.pattern_weight_var, width=10).pack(side='left')
        
        # 生成按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text='生成号码', 
                   command=self._generate_numbers).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='清空结果',
                   command=self._clear_generated).pack(side='left', padx=5)
        
        # 结果显示区
        result_frame = ttk.LabelFrame(frame, text='生成结果')
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建结果表格
        columns = ('序号', '红球号码', '蓝球号码', '评分')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)
        
        # 添加滚动条
        result_scroll = ttk.Scrollbar(result_frame, orient='vertical', 
                                    command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=result_scroll.set)
        self.result_tree.pack(side='left', fill='both', expand=True)
        result_scroll.pack(side='right', fill='y')
        
        return frame
        
    def _create_history_frame(self) -> ttk.Frame:
        """创建历史数据页"""
        frame = ttk.Frame(self.notebook)
        
        # 工具栏
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        # 日期范围选择
        ttk.Label(toolbar, text='起始日期:').pack(side='left', padx=5)
        self.start_date = ttk.Entry(toolbar, width=10)
        self.start_date.pack(side='left', padx=5)
        
        ttk.Label(toolbar, text='结束日期:').pack(side='left', padx=5)
        self.end_date = ttk.Entry(toolbar, width=10)
        self.end_date.pack(side='left', padx=5)
        
        # 查询按钮
        ttk.Button(toolbar, text='查询',
                   command=self._query_history).pack(side='left', padx=5)
        ttk.Button(toolbar, text='导出',
                   command=self._export_history).pack(side='left', padx=5)
        
        # 创建历史数据表格
        columns = ('期号', '开奖日期', '红球号码', '蓝球号码', '奖池金额', '一等奖注数', '一等奖金额')
        self.history_tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        # 添加滚动条
        y_scroll = ttk.Scrollbar(frame, orient='vertical', 
                                command=self.history_tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient='horizontal',
                                command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=y_scroll.set,
                                  xscrollcommand=x_scroll.set)
        
        # 布局
        self.history_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')
        
        return frame
        
    def _query_history(self):
        """查询历史数据"""
        try:
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            
            # 清空现有数据
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 获取历史数据
            history_data = self.analyzer.get_history_data(start_date, end_date)
            
            # 显示数据
            for data in history_data:
                self.history_tree.insert('', 'end', values=(
                    data['issue'],
                    data['date'],
                    ' '.join(f'{n:02d}' for n in data['red_numbers']),
                    f'{data["blue_number"]:02d}',
                    f'{data["pool_amount"]:,}',
                    data['first_prize_num'],
                    f'{data["first_prize_amount"]:,}'
                ))
                
        except Exception as e:
            messagebox.showerror('错误', f'查询历史数据失败: {str(e)}')
            
    def _export_history(self):
        """导出历史数据"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[('CSV文件', '*.csv'), ('所有文件', '*.*')]
            )
            if filename:
                data = []
                for item in self.history_tree.get_children():
                    values = self.history_tree.item(item)['values']
                    data.append(values)
                
                df = pd.DataFrame(data, columns=[
                    '期号', '开奖日期', '红球号码', '蓝球号码',
                    '奖池金额', '一等奖注数', '一等奖金额'
                ])
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                messagebox.showinfo('成功', '数据导出成功')
                
        except Exception as e:
            messagebox.showerror('错误', f'导出数据失败: {str(e)}')
            
    def _init_analysis_pages(self):
        """初始化分析页面"""
        periods = int(self.periods_var.get())
        
        # 频率分析页
        freq_frame = self._create_frequency_analysis_frame(self.analysis_notebook, periods)
        self.analysis_notebook.add(freq_frame, text='频率分析')
        
        # 遗漏分析页
        missing_frame = self._create_missing_analysis_frame(self.analysis_notebook, periods)
        self.analysis_notebook.add(missing_frame, text='遗漏分析')
        
        # 热温冷分析页
        temp_frame = self._create_temperature_analysis_frame(self.analysis_notebook, periods)
        self.analysis_notebook.add(temp_frame, text='热温冷分析')
        
    def _calculate_complex(self):
        """计算复式投注注数"""
        try:
            red_numbers = [i+1 for i, var in enumerate(self.red_vars) if var.get()]
            blue_numbers = [i+1 for i, var in enumerate(self.blue_vars) if var.get()]
            
            if len(red_numbers) < 6:
                messagebox.showwarning('警告', '红球至少选择6个号码')
                return
            if len(blue_numbers) < 1:
                messagebox.showwarning('警告', '蓝球至少选择1个号码')
                return
                
            # 计算注数
            red_count = len(red_numbers)
            blue_count = len(blue_numbers)
            total = self._calculate_combination(red_count, 6) * blue_count
            amount = total * 2  # 每注2元
            
            self.result_label.config(
                text=f'共{total}注，金额{amount}元'
            )
        except Exception as e:
            messagebox.showerror('错误', f'计算出错：{str(e)}')
            
    def _calculate_dantuo(self):
        """计算胆拖投注注数"""
        try:
            red_dan = [i+1 for i, var in enumerate(self.red_dan_vars) if var.get()]
            red_tuo = [i+1 for i, var in enumerate(self.red_tuo_vars) if var.get()]
            blue_numbers = [i+1 for i, var in enumerate(self.blue_dan_vars) if var.get()]
            
            # 验证选号
            if len(red_dan) > 5:
                messagebox.showwarning('警告', '红球胆码最多选择5个')
                return
            if len(red_dan) + len(red_tuo) < 7:
                messagebox.showwarning('警告', '红球胆码+拖码至少需要7个')
                return
            if len(blue_numbers) < 1:
                messagebox.showwarning('警告', '蓝球至少选择1个号码')
                return
                
            # 计算注数
            total = self._calculate_combination(len(red_tuo), 6-len(red_dan)) * len(blue_numbers)
            amount = total * 2  # 每注2元
            
            self.dantuo_result_label.config(
                text=f'共{total}注，金额{amount}元'
            )
        except Exception as e:
            messagebox.showerror('错误', f'计算出错：{str(e)}')
            
    def _generate_numbers(self):
        """生成号码"""
        try:
            count = int(self.count_var.get())
            strategy = self.strategy_var.get()
            history_weight = float(self.history_weight_var.get())
            pattern_weight = float(self.pattern_weight_var.get())
            
            # 清空现有结果
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
            
            # 生成号码
            numbers = self.number_generator.generate_numbers(
                count=count,
                strategy=strategy,
                history_weight=history_weight,
                pattern_weight=pattern_weight
            )
            
            # 显示结果
            for i, number in enumerate(numbers, 1):
                self.result_tree.insert('', 'end', values=(
                    i,
                    ' '.join(f'{n:02d}' for n in number['red_numbers']),
                    f'{number["blue_number"]:02d}',
                    f'{number["score"]:.2f}'
                ))
                
        except ValueError as e:
            messagebox.showerror('错误', '请输入有效的参数值')
        except Exception as e:
            messagebox.showerror('错误', f'生成号码失败: {str(e)}')
            
    def _refresh_analysis(self):
        """刷新分析数据"""
        try:
            periods = int(self.periods_var.get())
            if periods < 10 or periods > 1000:
                messagebox.showwarning('警告', '分析期数范围为10-1000')
                return
                
            # 清除现有页面
            for tab in self.analysis_notebook.tabs():
                self.analysis_notebook.forget(tab)
                
            # 重新初始化分析页面
            self._init_analysis_pages()
            
        except Exception as e:
            messagebox.showerror('错误', f'刷新数据出错：{str(e)}')
            
    def _update_statistics(self, history_data: List[Dict]):
        """更新统计信息"""
        self.stats_text.delete('1.0', tk.END)
        
        # 计算统计信息
        total_pool = sum(d['pool_amount'] for d in history_data)
        avg_pool = total_pool / len(history_data)
        
        total_first_prize = sum(d['first_prize_num'] for d in history_data)
        avg_first_prize = total_first_prize / len(history_data)
        
        max_pool = max(d['pool_amount'] for d in history_data)
        max_pool_period = next(d['period'] for d in history_data if d['pool_amount'] == max_pool)
        
        # 显示统计信息
        stats = (
            f"统计期数: {len(history_data)}期\n"
            f"平均奖池: {avg_pool:,.2f}元\n"
            f"平均一等奖注数: {avg_first_prize:.2f}注\n"
            f"最高奖池: {max_pool:,}元 (第{max_pool_period}期)\n"
        )
        self.stats_text.insert('1.0', stats)
        
    def _analyze_history(self):
        """分析历史数据"""
        try:
            periods = int(self.periods_var.get())
            analysis_window = tk.Toplevel(self)
            analysis_window.title('数据分析')
            analysis_window.geometry('800x600')
            
            # 创建分析结果显示区
            notebook = ttk.Notebook(analysis_window)
            notebook.pack(fill='both', expand=True, padx=5, pady=5)
            
            # 号码频率分析
            freq_frame = self._create_frequency_analysis_frame(notebook, periods)
            notebook.add(freq_frame, text='号码频率')
            
            # 遗漏值分析
            missing_frame = self._create_missing_analysis_frame(notebook, periods)
            notebook.add(missing_frame, text='遗漏分析')
            
            # 热温冷分析
            temp_frame = self._create_temperature_analysis_frame(notebook, periods)
            notebook.add(temp_frame, text='热温冷分析')
            
        except ValueError:
            messagebox.showerror('错误', '请输入有效的期数')
        except Exception as e:
            messagebox.showerror('错误', f'分析数据失败: {str(e)}')
            
    def _clear_complex(self):
        """清空复式投注选择"""
        for var in self.red_vars + self.blue_vars:
            var.set(False)
        self.result_label.config(text='')
        
    def _clear_dantuo(self):
        """清空胆拖投注选择"""
        for var in self.red_dan_vars + self.red_tuo_vars + self.blue_dan_vars:
            var.set(False)
        self.dantuo_result_label.config(text='')
        
    def _clear_generated(self):
        """清空生成结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
    @staticmethod
    def _calculate_combination(n: int, r: int) -> int:
        """计算组合数 C(n,r)"""
        if r > n:
            return 0
        r = min(r, n-r)
        numerator = 1
        denominator = 1
        for i in range(r):
            numerator *= (n - i)
            denominator *= (i + 1)
        return numerator // denominator
        
    def _create_frequency_analysis_frame(self, parent: ttk.Notebook, periods: int) -> ttk.Frame:
        """创建频率分析页面"""
        frame = ttk.Frame(parent)
        
        # 获取频率分析数据
        frequency_data = self.analyzer.analyze_frequency(periods)
        
        # 红球频率展示
        red_frame = ttk.LabelFrame(frame, text='红球频率分析')
        red_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建红球频率表格
        columns = ('号码', '出现次数', '出现频率', '最近出现')
        red_tree = ttk.Treeview(red_frame, columns=columns, show='headings', height=10)
        for col in columns:
            red_tree.heading(col, text=col)
            red_tree.column(col, width=100)
            
        # 填充红球数据
        for num, data in frequency_data['red_frequency'].items():
            red_tree.insert('', 'end', values=(
                f'{num:02d}',
                data['count'],
                f'{data["frequency"]:.2%}',
                data['last_appearance']
            ))
            
        # 添加滚动条
        red_scroll = ttk.Scrollbar(red_frame, orient='vertical', command=red_tree.yview)
        red_tree.configure(yscrollcommand=red_scroll.set)
        red_tree.pack(side='left', fill='both', expand=True)
        red_scroll.pack(side='right', fill='y')
        
        # 蓝球频率展示
        blue_frame = ttk.LabelFrame(frame, text='蓝球频率分析')
        blue_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建蓝球频率表格
        blue_tree = ttk.Treeview(blue_frame, columns=columns, show='headings', height=8)
        for col in columns:
            blue_tree.heading(col, text=col)
            blue_tree.column(col, width=100)
            
        # 填充蓝球数据
        for num, data in frequency_data['blue_frequency'].items():
            blue_tree.insert('', 'end', values=(
                f'{num:02d}',
                data['count'],
                f'{data["frequency"]:.2%}',
                data['last_appearance']
            ))
            
        # 添加滚动条
        blue_scroll = ttk.Scrollbar(blue_frame, orient='vertical', command=blue_tree.yview)
        blue_tree.configure(yscrollcommand=blue_scroll.set)
        blue_tree.pack(side='left', fill='both', expand=True)
        blue_scroll.pack(side='right', fill='y')
        
        return frame
        
    def _create_missing_analysis_frame(self, parent: ttk.Notebook, periods: int) -> ttk.Frame:
        """创建遗漏值分析页面"""
        frame = ttk.Frame(parent)
        
        # 获取遗漏值分析数据
        missing_data = self.analyzer.analyze_missing_numbers(periods)
        
        # 当前遗漏值展示
        current_frame = ttk.LabelFrame(frame, text='当前遗漏值')
        current_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建当前遗漏值表格
        columns = ('号码', '当前遗漏', '最大遗漏', '平均遗漏')
        
        # 红球遗漏值
        red_frame = ttk.LabelFrame(current_frame, text='红球遗漏值')
        red_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        red_tree = ttk.Treeview(red_frame, columns=columns, show='headings', height=10)
        for col in columns:
            red_tree.heading(col, text=col)
            red_tree.column(col, width=100)
            
        for num, data in missing_data['red'].items():
            red_tree.insert('', 'end', values=(
                f'{num:02d}',
                data['current'],
                data['max'],
                f'{data["average"]:.1f}'
            ))
            
        red_tree.pack(side='left', fill='both', expand=True)
        red_scroll = ttk.Scrollbar(red_frame, orient='vertical', command=red_tree.yview)
        red_tree.configure(yscrollcommand=red_scroll.set)
        red_scroll.pack(side='right', fill='y')
        
        # 蓝球遗漏值
        blue_frame = ttk.LabelFrame(current_frame, text='蓝球遗漏值')
        blue_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        blue_tree = ttk.Treeview(blue_frame, columns=columns, show='headings', height=8)
        for col in columns:
            blue_tree.heading(col, text=col)
            blue_tree.column(col, width=100)
            
        for num, data in missing_data['blue'].items():
            blue_tree.insert('', 'end', values=(
                f'{num:02d}',
                data['current'],
                data['max'],
                f'{data["average"]:.1f}'
            ))
            
        blue_tree.pack(side='left', fill='both', expand=True)
        blue_scroll = ttk.Scrollbar(blue_frame, orient='vertical', command=blue_tree.yview)
        blue_tree.configure(yscrollcommand=blue_scroll.set)
        blue_scroll.pack(side='right', fill='y')
        
        return frame
        
    def _create_temperature_analysis_frame(self, parent: ttk.Notebook, periods: int) -> ttk.Frame:
        """创建热温冷分析页面"""
        frame = ttk.Frame(parent)
        
        # 获取热温冷分析数据
        temp_data = self.analyzer.analyze_hot_cold_numbers(periods)
        
        # 创建分类标签
        label_frame = ttk.Frame(frame)
        label_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(label_frame, text='热号：近期出现频率较高的号码').pack(anchor='w')
        ttk.Label(label_frame, text='温号：近期出现频率中等的号码').pack(anchor='w')
        ttk.Label(label_frame, text='冷号：近期出现频率较低的号码').pack(anchor='w')
        
        # 红球热温冷展示
        red_frame = ttk.LabelFrame(frame, text='红球热温冷分析')
        red_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建红球表格
        columns = ('类型', '号码', '出现次数', '出现频率')
        red_tree = ttk.Treeview(red_frame, columns=columns, show='headings', height=10)
        for col in columns:
            red_tree.heading(col, text=col)
            red_tree.column(col, width=100)
            
        # 填充红球数据
        for category in ['hot', 'warm', 'cold']:
            for num_data in temp_data['red'][category]:
                red_tree.insert('', 'end', values=(
                    category.capitalize(),
                    f'{num_data["number"]:02d}',
                    num_data['count'],
                    f'{num_data["frequency"]:.2%}'
                ))
                
        # 添加滚动条
        red_scroll = ttk.Scrollbar(red_frame, orient='vertical', command=red_tree.yview)
        red_tree.configure(yscrollcommand=red_scroll.set)
        red_tree.pack(side='left', fill='both', expand=True)
        red_scroll.pack(side='right', fill='y')
        
        # 蓝球热温冷展示
        blue_frame = ttk.LabelFrame(frame, text='蓝球热温冷分析')
        blue_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建蓝球表格
        blue_tree = ttk.Treeview(blue_frame, columns=columns, show='headings', height=8)
        for col in columns:
            blue_tree.heading(col, text=col)
            blue_tree.column(col, width=100)
            
        # 填充蓝球数据
        for category in ['hot', 'warm', 'cold']:
            for num_data in temp_data['blue'][category]:
                blue_tree.insert('', 'end', values=(
                    category.capitalize(),
                    f'{num_data["number"]:02d}',
                    num_data['count'],
                    f'{num_data["frequency"]:.2%}'
                ))
                
        # 添加滚动条
        blue_scroll = ttk.Scrollbar(blue_frame, orient='vertical', command=blue_tree.yview)
        blue_tree.configure(yscrollcommand=blue_scroll.set)
        blue_tree.pack(side='left', fill='both', expand=True)
        blue_scroll.pack(side='right', fill='y')
        
        return frame

    def _create_prize_check_frame(self) -> ttk.Frame:
        """创建中奖对照页"""
        frame = ttk.Frame(self.notebook)
        
        # 投注号码输入区
        input_frame = ttk.LabelFrame(frame, text='投注号码')
        input_frame.pack(fill='x', padx=5, pady=5)
        
        # 红球输入
        red_frame = ttk.Frame(input_frame)
        red_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(red_frame, text='红球号码:').pack(side='left')
        self.red_entry = ttk.Entry(red_frame, width=30)
        self.red_entry.pack(side='left', padx=5)
        ttk.Label(red_frame, text='(用空格分隔)').pack(side='left')
        
        # 蓝球输入
        blue_frame = ttk.Frame(input_frame)
        blue_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(blue_frame, text='蓝球号码:').pack(side='left')
        self.blue_entry = ttk.Entry(blue_frame, width=10)
        self.blue_entry.pack(side='left', padx=5)
        
        # 开奖号码输入区
        draw_frame = ttk.LabelFrame(frame, text='开奖号码')
        draw_frame.pack(fill='x', padx=5, pady=5)
        
        # 期号输入
        issue_frame = ttk.Frame(draw_frame)
        issue_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(issue_frame, text='开奖期号:').pack(side='left')
        self.issue_entry = ttk.Entry(issue_frame, width=10)
        self.issue_entry.pack(side='left', padx=5)
        ttk.Button(issue_frame, text='获取开奖号码',
                   command=self._fetch_draw_numbers).pack(side='left', padx=5)
        
        # 开奖号码显示
        draw_numbers_frame = ttk.Frame(draw_frame)
        draw_numbers_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(draw_numbers_frame, text='红球:').pack(side='left')
        self.draw_red_var = tk.StringVar()
        ttk.Label(draw_numbers_frame, textvariable=self.draw_red_var).pack(side='left', padx=5)
        ttk.Label(draw_numbers_frame, text='蓝球:').pack(side='left')
        self.draw_blue_var = tk.StringVar()
        ttk.Label(draw_numbers_frame, textvariable=self.draw_blue_var).pack(side='left', padx=5)
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text='对照中奖',
                   command=self._check_prize).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='清空',
                   command=self._clear_prize_check).pack(side='left', padx=5)
        
        # 结果显示区
        result_frame = ttk.LabelFrame(frame, text='中奖结果')
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.result_text = tk.Text(result_frame, height=10)
        self.result_text.pack(fill='both', expand=True)
        
        return frame

    def _fetch_draw_numbers(self):
        """获取开奖号码"""
        try:
            issue = self.issue_entry.get().strip()
            if not issue:
                messagebox.showwarning('提示', '请输入开奖期号')
                return
            
            # 从数据管理器获取开奖号码
            draw_numbers = self.analyzer.get_draw_numbers(issue)
            if draw_numbers:
                self.draw_red_var.set(' '.join(f'{n:02d}' for n in draw_numbers['red']))
                self.draw_blue_var.set(f'{draw_numbers["blue"]:02d}')
            else:
                messagebox.showwarning('提示', '未找到该期开奖号码')
            
        except Exception as e:
            messagebox.showerror('错误', f'获取开奖号码失败: {str(e)}')

    def _check_prize(self):
        """对照中奖"""
        try:
            # 获取投注号码
            red_str = self.red_entry.get().strip()
            blue_str = self.blue_entry.get().strip()
            
            if not red_str or not blue_str:
                messagebox.showwarning('提示', '请输入投注号码')
                return
            
            # 解析投注号码
            try:
                red_numbers = [int(x) for x in red_str.split()]
                blue_number = int(blue_str)
                
                if len(red_numbers) != 6:
                    raise ValueError('红球必须是6个号码')
                if not all(1 <= x <= 33 for x in red_numbers):
                    raise ValueError('红球号码必须在1-33之间')
                if not 1 <= blue_number <= 16:
                    raise ValueError('蓝球号码必须在1-16之间')
                
            except ValueError as e:
                messagebox.showwarning('提示', f'投注号码格式错误: {str(e)}')
                return
            
            # 获取开奖号码
            draw_red = [int(x) for x in self.draw_red_var.get().split()]
            draw_blue = int(self.draw_blue_var.get())
            
            if not draw_red or not draw_blue:
                messagebox.showwarning('提示', '请先获取开奖号码')
                return
            
            # 计算中奖情况
            red_matches = len(set(red_numbers) & set(draw_red))
            blue_match = blue_number == draw_blue
            
            # 判断中奖等级
            prize_level = self._get_prize_level(red_matches, blue_match)
            
            # 显示结果
            result = f"投注号码: {' '.join(f'{n:02d}' for n in red_numbers)} + {blue_number:02d}\n"
            result += f"开奖号码: {' '.join(f'{n:02d}' for n in draw_red)} + {draw_blue:02d}\n"
            result += f"红球匹配: {red_matches}个\n"
            result += f"蓝球匹配: {'是' if blue_match else '否'}\n"
            result += f"中奖结果: {prize_level}"
            
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', result)
        
        except Exception as e:
            messagebox.showerror('错误', f'对照中奖失败: {str(e)}')

    def _get_prize_level(self, red_matches: int, blue_match: bool) -> str:
        """获取中奖等级"""
        if red_matches == 6 and blue_match:
            return "一等奖"
        elif red_matches == 6:
            return "二等奖"
        elif red_matches == 5 and blue_match:
            return "三等奖"
        elif red_matches == 5 or (red_matches == 4 and blue_match):
            return "四等奖"
        elif red_matches == 4 or (red_matches == 3 and blue_match):
            return "五等奖"
        elif blue_match:
            return "六等奖"
        else:
            return "未中奖"

    def _clear_prize_check(self):
        """清空中奖对照"""
        self.red_entry.delete(0, tk.END)
        self.blue_entry.delete(0, tk.END)
        self.issue_entry.delete(0, tk.END)
        self.draw_red_var.set('')
        self.draw_blue_var.set('')
        self.result_text.delete('1.0', tk.END)
