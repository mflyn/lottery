# 号码评价GUI集成 - 实施指南

## 🎯 目标

将号码评价工具集成到GUI中，支持双色球和大乐透的号码评价。

---

## 📋 快速方案

### 方案A：最小化实施（推荐）⭐

**优点**: 快速实现，代码复用度高  
**工期**: 2-3天  
**难度**: ⭐⭐

#### 实施步骤

1. **复用现有代码** - 将 `evaluate_number.py` 改造为模块
2. **创建简单GUI** - 一个新的标签页
3. **集成到主窗口** - 添加到 `LotteryApp`

---

### 方案B：完整实施

**优点**: 架构清晰，可扩展性强  
**工期**: 7-10天  
**难度**: ⭐⭐⭐⭐

#### 实施步骤

1. **创建评价器模块** - 完整的OOP架构
2. **创建完整GUI** - 丰富的交互和可视化
3. **性能优化** - 缓存、异步、进度提示

---

## 🚀 推荐实施：方案A（最小化）

### Step 1: 创建评价器模块（1天）

#### 1.1 创建 `src/core/evaluators/ssq_evaluator.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双色球号码评价器
"""

import json
import numpy as np
from collections import Counter
from typing import List, Dict

class SSQNumberEvaluator:
    """双色球号码评价器"""
    
    def __init__(self, history_file='data/ssq_history.json'):
        """初始化评价器"""
        self.history_file = history_file
        self.history_data = None
    
    def load_history(self):
        """加载历史数据"""
        if self.history_data is None:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.history_data = data['data']
        return self.history_data
    
    def evaluate(self, red_numbers: List[int], blue_number: int) -> Dict:
        """评价号码
        
        Args:
            red_numbers: 红球号码列表
            blue_number: 蓝球号码
            
        Returns:
            评价结果字典
        """
        history_data = self.load_history()
        
        # 1. 频率分析
        freq_result = self._analyze_frequency(red_numbers, blue_number, history_data)
        
        # 2. 遗漏分析
        missing_result = self._analyze_missing(red_numbers, blue_number, history_data)
        
        # 3. 模式分析
        pattern_result = self._analyze_patterns(red_numbers)
        
        # 4. 历史对比
        historical_result = self._check_historical(red_numbers, blue_number, history_data)
        
        # 5. 计算得分
        scores = self._calculate_scores(freq_result, missing_result, pattern_result, historical_result)
        
        return {
            'frequency': freq_result,
            'missing': missing_result,
            'pattern': pattern_result,
            'historical': historical_result,
            'scores': scores,
            'total_score': scores['total'],
            'rating': scores['rating'],
            'suggestions': self._generate_suggestions(freq_result, missing_result, pattern_result, historical_result)
        }
    
    def _analyze_frequency(self, red_numbers, blue_number, history_data, periods=100):
        """频率分析（复用 evaluate_number.py 的逻辑）"""
        # ... 实现代码
        pass
    
    def _analyze_missing(self, red_numbers, blue_number, history_data):
        """遗漏分析"""
        # ... 实现代码
        pass
    
    def _analyze_patterns(self, red_numbers):
        """模式分析"""
        # ... 实现代码
        pass
    
    def _check_historical(self, red_numbers, blue_number, history_data):
        """历史对比"""
        # ... 实现代码
        pass
    
    def _calculate_scores(self, freq, missing, pattern, historical):
        """计算得分"""
        # ... 实现代码
        pass
    
    def _generate_suggestions(self, freq, missing, pattern, historical):
        """生成建议"""
        # ... 实现代码
        pass
```

#### 1.2 创建 `src/core/evaluators/dlt_evaluator.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大乐透号码评价器
"""

class DLTNumberEvaluator:
    """大乐透号码评价器"""
    
    def __init__(self, history_file='data/dlt_history.json'):
        """初始化评价器"""
        self.history_file = history_file
        self.history_data = None
    
    def evaluate(self, front_numbers: List[int], back_numbers: List[int]) -> Dict:
        """评价号码"""
        # 类似SSQ的实现，适配大乐透规则
        pass
```

---

### Step 2: 创建GUI框架（1天）

#### 2.1 创建 `src/gui/frames/number_evaluation_frame.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
号码评价GUI框架
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator

class NumberEvaluationFrame(ttk.Frame):
    """号码评价框架"""
    
    def __init__(self, master, data_manager=None):
        super().__init__(master)
        self.data_manager = data_manager
        
        # 创建评价器
        self.ssq_evaluator = SSQNumberEvaluator()
        self.dlt_evaluator = DLTNumberEvaluator()
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        # 1. 彩种选择
        self._create_lottery_type_selector()
        
        # 2. 号码输入
        self._create_number_input_area()
        
        # 3. 评价结果
        self._create_result_display_area()
        
        # 4. 详细分析
        self._create_detail_analysis_area()
        
        # 5. 操作按钮
        self._create_action_buttons()
    
    def _create_lottery_type_selector(self):
        """创建彩种选择器"""
        frame = ttk.LabelFrame(self, text="彩种选择", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lottery_type_var = tk.StringVar(value='ssq')
        
        ttk.Radiobutton(
            frame, 
            text="双色球", 
            variable=self.lottery_type_var, 
            value='ssq',
            command=self._on_lottery_type_changed
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            frame, 
            text="大乐透", 
            variable=self.lottery_type_var, 
            value='dlt',
            command=self._on_lottery_type_changed
        ).pack(side=tk.LEFT, padx=10)
    
    def _create_number_input_area(self):
        """创建号码输入区"""
        frame = ttk.LabelFrame(self, text="号码输入", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 双色球输入
        self.ssq_input_frame = ttk.Frame(frame)
        
        ttk.Label(self.ssq_input_frame, text="红球:").grid(row=0, column=0, padx=5, sticky='w')
        self.ssq_red_entry = ttk.Entry(self.ssq_input_frame, width=40)
        self.ssq_red_entry.grid(row=0, column=1, padx=5)
        ttk.Label(self.ssq_input_frame, text="(6个号码，空格分隔，如: 03 09 16 17 24 33)").grid(row=0, column=2, padx=5)
        
        ttk.Label(self.ssq_input_frame, text="蓝球:").grid(row=1, column=0, padx=5, sticky='w')
        self.ssq_blue_entry = ttk.Entry(self.ssq_input_frame, width=10)
        self.ssq_blue_entry.grid(row=1, column=1, padx=5, sticky='w')
        ttk.Label(self.ssq_input_frame, text="(1个号码，如: 15)").grid(row=1, column=2, padx=5)
        
        # 大乐透输入
        self.dlt_input_frame = ttk.Frame(frame)
        
        ttk.Label(self.dlt_input_frame, text="前区:").grid(row=0, column=0, padx=5, sticky='w')
        self.dlt_front_entry = ttk.Entry(self.dlt_input_frame, width=40)
        self.dlt_front_entry.grid(row=0, column=1, padx=5)
        ttk.Label(self.dlt_input_frame, text="(5个号码，空格分隔)").grid(row=0, column=2, padx=5)
        
        ttk.Label(self.dlt_input_frame, text="后区:").grid(row=1, column=0, padx=5, sticky='w')
        self.dlt_back_entry = ttk.Entry(self.dlt_input_frame, width=20)
        self.dlt_back_entry.grid(row=1, column=1, padx=5, sticky='w')
        ttk.Label(self.dlt_input_frame, text="(2个号码，空格分隔)").grid(row=1, column=2, padx=5)
        
        # 默认显示双色球输入
        self.ssq_input_frame.pack(fill=tk.X)
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="清空", command=self._clear_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="随机", command=self._random_numbers).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="评价号码", command=self._evaluate_numbers, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
    
    def _create_result_display_area(self):
        """创建结果显示区"""
        frame = ttk.LabelFrame(self, text="评价结果", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 左侧：综合得分
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(left_frame, text="综合得分", font=('Arial', 12, 'bold')).pack()
        self.total_score_label = ttk.Label(left_frame, text="--", font=('Arial', 36, 'bold'), foreground='#28a745')
        self.total_score_label.pack()
        self.rating_label = ttk.Label(left_frame, text="", font=('Arial', 14))
        self.rating_label.pack()
        
        # 右侧：各维度得分
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        ttk.Label(right_frame, text="各维度得分", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        self.dimension_labels = {}
        dimensions = ['频率得分', '遗漏得分', '模式得分', '独特性得分']
        
        for dim in dimensions:
            dim_frame = ttk.Frame(right_frame)
            dim_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(dim_frame, text=f"{dim}:", width=12).pack(side=tk.LEFT)
            label = ttk.Label(dim_frame, text="--", width=15)
            label.pack(side=tk.LEFT)
            self.dimension_labels[dim] = label
    
    def _create_detail_analysis_area(self):
        """创建详细分析区"""
        frame = ttk.LabelFrame(self, text="详细分析", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建标签页
        self.detail_notebook = ttk.Notebook(frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 各个分析标签页
        self.freq_text = self._create_text_tab(self.detail_notebook, "频率分析")
        self.missing_text = self._create_text_tab(self.detail_notebook, "遗漏分析")
        self.pattern_text = self._create_text_tab(self.detail_notebook, "模式分析")
        self.historical_text = self._create_text_tab(self.detail_notebook, "历史对比")
        self.suggestion_text = self._create_text_tab(self.detail_notebook, "专家建议")
    
    def _create_text_tab(self, notebook, title):
        """创建文本标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        
        text = tk.Text(frame, wrap=tk.WORD, font=('Consolas', 10))
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
        
        return text
    
    def _create_action_buttons(self):
        """创建操作按钮"""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(frame, text="导出报告", command=self._export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="保存号码", command=self._save_numbers).pack(side=tk.LEFT, padx=5)
    
    def _on_lottery_type_changed(self):
        """彩种切换"""
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            self.dlt_input_frame.pack_forget()
            self.ssq_input_frame.pack(fill=tk.X)
        else:
            self.ssq_input_frame.pack_forget()
            self.dlt_input_frame.pack(fill=tk.X)
    
    def _clear_input(self):
        """清空输入"""
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            self.ssq_red_entry.delete(0, tk.END)
            self.ssq_blue_entry.delete(0, tk.END)
        else:
            self.dlt_front_entry.delete(0, tk.END)
            self.dlt_back_entry.delete(0, tk.END)
    
    def _random_numbers(self):
        """随机生成号码"""
        import random
        
        lottery_type = self.lottery_type_var.get()
        
        if lottery_type == 'ssq':
            red = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)
            
            self.ssq_red_entry.delete(0, tk.END)
            self.ssq_red_entry.insert(0, ' '.join(f'{n:02d}' for n in red))
            
            self.ssq_blue_entry.delete(0, tk.END)
            self.ssq_blue_entry.insert(0, f'{blue:02d}')
        else:
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            
            self.dlt_front_entry.delete(0, tk.END)
            self.dlt_front_entry.insert(0, ' '.join(f'{n:02d}' for n in front))
            
            self.dlt_back_entry.delete(0, tk.END)
            self.dlt_back_entry.insert(0, ' '.join(f'{n:02d}' for n in back))
    
    def _evaluate_numbers(self):
        """评价号码"""
        try:
            lottery_type = self.lottery_type_var.get()
            
            if lottery_type == 'ssq':
                # 获取输入
                red_text = self.ssq_red_entry.get().strip()
                blue_text = self.ssq_blue_entry.get().strip()
                
                if not red_text or not blue_text:
                    messagebox.showwarning("输入错误", "请输入完整的号码")
                    return
                
                red_numbers = [int(x) for x in red_text.split()]
                blue_number = int(blue_text)
                
                # 验证
                if len(red_numbers) != 6:
                    messagebox.showwarning("输入错误", "红球必须是6个号码")
                    return
                
                if not all(1 <= n <= 33 for n in red_numbers):
                    messagebox.showwarning("输入错误", "红球号码范围: 01-33")
                    return
                
                if not (1 <= blue_number <= 16):
                    messagebox.showwarning("输入错误", "蓝球号码范围: 01-16")
                    return
                
                # 异步评价
                self._evaluate_ssq_async(red_numbers, blue_number)
            
            else:
                # 大乐透评价（类似实现）
                pass
        
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")
        except Exception as e:
            messagebox.showerror("错误", f"评价失败: {str(e)}")
    
    def _evaluate_ssq_async(self, red_numbers, blue_number):
        """异步评价双色球号码"""
        # 显示进度
        self.total_score_label.config(text="评价中...")
        self.rating_label.config(text="请稍候")
        
        def do_evaluate():
            try:
                # 调用评价器
                result = self.ssq_evaluator.evaluate(red_numbers, blue_number)
                
                # 更新UI（必须在主线程）
                self.after(0, lambda: self._update_result_display(result))
            
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", f"评价失败: {str(e)}"))
        
        # 启动线程
        thread = threading.Thread(target=do_evaluate)
        thread.daemon = True
        thread.start()
    
    def _update_result_display(self, result):
        """更新结果显示"""
        # 更新综合得分
        total_score = result['total_score']
        self.total_score_label.config(text=f"{total_score:.1f}")
        self.rating_label.config(text=result['rating'])
        
        # 更新各维度得分
        scores = result['scores']
        self.dimension_labels['频率得分'].config(text=f"{scores['frequency']:.1f}/100")
        self.dimension_labels['遗漏得分'].config(text=f"{scores['missing']:.1f}/100")
        self.dimension_labels['模式得分'].config(text=f"{scores['pattern']:.1f}/100")
        self.dimension_labels['独特性得分'].config(text=f"{scores['uniqueness']:.1f}/100")
        
        # 更新详细分析
        self._update_detail_text(self.freq_text, result['frequency'])
        self._update_detail_text(self.missing_text, result['missing'])
        self._update_detail_text(self.pattern_text, result['pattern'])
        self._update_detail_text(self.historical_text, result['historical'])
        self._update_detail_text(self.suggestion_text, {'suggestions': result['suggestions']})
    
    def _update_detail_text(self, text_widget, data):
        """更新详细文本"""
        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', self._format_detail_data(data))
    
    def _format_detail_data(self, data):
        """格式化详细数据"""
        # 将字典数据格式化为可读文本
        # TODO: 实现格式化逻辑
        return str(data)
    
    def _export_report(self):
        """导出报告"""
        # TODO: 实现导出功能
        messagebox.showinfo("提示", "导出功能开发中...")
    
    def _save_numbers(self):
        """保存号码"""
        # TODO: 实现保存功能
        messagebox.showinfo("提示", "保存功能开发中...")
```

---

### Step 3: 集成到主窗口（0.5天）

#### 3.1 修改 `src/gui/main_window.py`

在 `LotteryApp.__init__()` 方法中添加：

```python
# 添加号码评价标签页
from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame

self.evaluation_tab = NumberEvaluationFrame(
    self.notebook, 
    self.analysis_tab.data_manager
)
self.notebook.add(self.evaluation_tab, text="号码评价")
```

---

## ✅ 验证测试

### 测试清单

- [ ] 双色球号码输入
- [ ] 大乐透号码输入
- [ ] 随机生成功能
- [ ] 评价功能（双色球）
- [ ] 评价功能（大乐透）
- [ ] 结果显示
- [ ] 详细分析显示
- [ ] 导出报告
- [ ] 保存号码

---

## 📚 后续优化

### 可选功能

1. **号码选择器** - 点击按钮选择号码
2. **历史号码** - 从历史记录中选择
3. **批量评价** - 一次评价多注号码
4. **对比功能** - 对比多注号码
5. **可视化** - 图表展示分析结果

---

## 🎉 完成标志

当你能够：

1. ✅ 在GUI中看到"号码评价"标签页
2. ✅ 输入双色球号码并评价
3. ✅ 输入大乐透号码并评价
4. ✅ 看到综合得分和各维度得分
5. ✅ 查看详细分析报告

**恭喜！集成完成！🎉**

---

**文档版本**: v1.0  
**更新时间**: 2025-10-20


