import tkinter as tk
from tkinter import ttk, messagebox
from src.core.strategy.number_evaluator import NumberEvaluator
from src.core.models.lottery_types import SSQNumber

class NumberScoreFrame(ttk.Frame):
    """号码评分界面"""
    
    def __init__(self, master):
        super().__init__(master)
        self.evaluator = NumberEvaluator()
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 号码输入区域
        input_frame = ttk.LabelFrame(self, text='号码输入')
        input_frame.pack(fill='x', padx=5, pady=5)
        
        # 红球输入
        ttk.Label(input_frame, text='红球:').pack(side='left', padx=5)
        self.red_entry = ttk.Entry(input_frame, width=30)
        self.red_entry.pack(side='left', padx=5)
        ttk.Label(input_frame, text='(用空格分隔)').pack(side='left')
        
        # 蓝球输入
        ttk.Label(input_frame, text='蓝球:').pack(side='left', padx=5)
        self.blue_entry = ttk.Entry(input_frame, width=5)
        self.blue_entry.pack(side='left', padx=5)
        
        # 评分按钮
        ttk.Button(input_frame, text='评分',
                  command=self._evaluate_numbers).pack(side='left', padx=10)
        
        # 评分结果区域
        result_frame = ttk.LabelFrame(self, text='评分结果')
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 总分显示
        score_frame = ttk.Frame(result_frame)
        score_frame.pack(fill='x', padx=5, pady=5)
        
        self.score_label = ttk.Label(score_frame, text='总分: --', font=('Arial', 16, 'bold'))
        self.score_label.pack(side='left')
        
        # 维度得分
        dimensions_frame = ttk.LabelFrame(result_frame, text='维度得分')
        dimensions_frame.pack(fill='x', padx=5, pady=5)
        
        self.dimension_labels = {}
        for dim in ['平衡性', '模式匹配', '频率', '历史表现']:
            frame = ttk.Frame(dimensions_frame)
            frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(frame, text=f'{dim}:').pack(side='left')
            label = ttk.Label(frame, text='--')
            label.pack(side='left', padx=5)
            self.dimension_labels[dim] = label
            
        # 详细分析
        self.detail_text = tk.Text(result_frame, height=8)
        self.detail_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _evaluate_numbers(self):
        """评估号码"""
        try:
            # 获取输入号码
            red_numbers = [int(x) for x in self.red_entry.get().split()]
            blue_number = int(self.blue_entry.get())
            
            # 创建号码对象
            number = SSQNumber(red=red_numbers, blue=blue_number)
            
            # 获取评分结果
            result = self.evaluator.evaluate_number(number)
            
            # 更新显示
            self.score_label.config(text=f'总分: {result["total_score"]:.2f}')
            
            # 更新维度得分
            scores = result['dimension_scores']
            self.dimension_labels['平衡性'].config(text=f'{scores["balance"]:.2f}')
            self.dimension_labels['模式匹配'].config(text=f'{scores["pattern"]:.2f}')
            self.dimension_labels['频率'].config(text=f'{scores["frequency"]:.2f}')
            self.dimension_labels['历史表现'].config(text=f'{scores["historical"]:.2f}')
            
            # 更新详细分析
            self.detail_text.delete('1.0', tk.END)
            self.detail_text.insert('1.0', self._format_details(result['details']))
            
        except ValueError:
            messagebox.showerror('输入错误', '请输入有效的号码格式')
        except Exception as e:
            messagebox.showerror('错误', f'评分失败: {str(e)}')
            
    def _format_details(self, details: dict) -> str:
        """格式化详细信息"""
        text = "详细分析:\n\n"
        
        # 平衡性分析
        text += "1. 平衡性分析\n"
        text += f"- 号码分布: {details['balance']['distribution']}\n"
        text += f"- 奇偶比例: {details['balance']['odd_even']}\n"
        text += f"- 和值: {details['balance']['sum_value']}\n\n"
        
        # 模式分析
        text += "2. 模式分析\n"
        text += "- 匹配模式:\n"
        for pattern in details['pattern']['matched_patterns'][:3]:
            text += f"  * {pattern}\n"
        text += "\n"
        
        # 频率分析
        text += "3. 频率分析\n"
        text += "- 热门号码:\n"
        for num in details['frequency']['hot_numbers']:
            text += f"  * {num}\n"
        text += "- 冷门号码:\n"
        for num in details['frequency']['cold_numbers']:
            text += f"  * {num}\n\n"
        
        # 历史表现
        text += "4. 历史表现\n"
        text += f"- 相似中奖号码数: {len(details['historical']['similar_winners'])}\n"
        text += "- 奖级分布:\n"
        for level, count in details['historical']['prize_distribution'].items():
            text += f"  * {level}等奖: {count}次\n"
            
        return text