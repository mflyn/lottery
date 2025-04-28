import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import markdown2
import webbrowser
from pathlib import Path

class HelpWindow:
    """帮助窗口"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("使用帮助")
        self.window.geometry("800x600")
        
        # 创建帮助内容
        self._create_widgets()
        self._load_help_content()
        
    def _create_widgets(self):
        """创建窗口部件"""
        # 创建左侧目录树
        self.tree_frame = ttk.Frame(self.window)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # 创建右侧内容区
        self.content_frame = ttk.Frame(self.window)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.content = ScrolledText(self.content_frame, wrap=tk.WORD)
        self.content.pack(fill=tk.BOTH, expand=True)
        
    def _load_help_content(self):
        """加载帮助内容"""
        # 添加目录项
        self.help_topics = {
            '快速开始': 'docs/quickstart.md',
            '功能介绍': {
                '大乐透': 'docs/dlt_guide.md',
                '双色球': 'docs/ssq_guide.md',
                '数据分析': 'docs/analysis_guide.md',
                '特征工程': 'docs/feature_guide.md'
            },
            '高级功能': {
                '智能选号': 'docs/smart_pick.md',
                '模式分析': 'docs/pattern_analysis.md',
                '概率预测': 'docs/probability_prediction.md'
            },
            '常见问题': 'docs/faq.md',
            '技术支持': 'docs/support.md'
        }
        
        # 构建目录树
        self._build_tree('', self.help_topics)
        
    def _build_tree(self, parent, items):
        """递归构建目录树"""
        for key, value in items.items():
            if isinstance(value, dict):
                # 如果是字典,创建父节点
                node = self.tree.insert(parent, 'end', text=key)
                self._build_tree(node, value)
            else:
                # 如果是文件路径,创建叶子节点
                self.tree.insert(parent, 'end', text=key, values=(value,))
                
    def _on_select(self, event):
        """处理目录选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item)['values']
        if not values:
            return
            
        help_file = values[0]
        self._show_help_content(help_file)
        
    def _show_help_content(self, help_file):
        """显示帮助内容"""
        try:
            with open(help_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 转换Markdown为HTML
            html = markdown2.markdown(content)
            
            # 清空并显示新内容
            self.content.delete('1.0', tk.END)
            self.content.insert('1.0', html)
            
        except FileNotFoundError:
            self.content.delete('1.0', tk.END)
            self.content.insert('1.0', f"帮助文件不存在: {help_file}")