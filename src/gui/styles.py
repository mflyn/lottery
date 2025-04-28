from tkinter import ttk

def configure_styles():
    """配置界面样式"""
    style = ttk.Style()
    
    # 配置普通按钮样式
    style.configure('TButton',
        padding=5,
        width=8,
        font=('微软雅黑', 10)
    )
    
    # 配置选中按钮样式
    style.configure('Selected.TButton',
        padding=5,
        width=8,
        font=('微软雅黑', 10),
        background='#4CAF50',
        foreground='white'
    )
    
    # 配置标题样式
    style.configure('Title.TLabel',
        font=('微软雅黑', 14, 'bold'),
        padding=10
    )
    
    # 配置结果框样式
    style.configure('Result.TLabelframe',
        padding=10,
        font=('微软雅黑', 10)
    )