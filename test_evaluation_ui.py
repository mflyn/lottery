#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
号码评价界面测试脚本
用于测试号码评价界面的布局和功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主测试函数"""
    try:
        import tkinter as tk
        from tkinter import ttk
        from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
        
        # 创建主窗口
        root = tk.Tk()
        root.title('号码评价界面测试')
        
        # 设置窗口大小（模拟全屏）
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 使用80%的屏幕大小
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 创建号码评价框架
        frame = NumberEvaluationFrame(root)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加测试说明
        print("=" * 80)
        print(" " * 25 + "号码评价界面测试")
        print("=" * 80)
        print()
        print("✅ 界面创建成功")
        print()
        print(f"窗口大小: {window_width}x{window_height}")
        print()
        print("请检查以下内容：")
        print()
        print("1. 📏 详细分析区域是否占据了足够的空间")
        print("   - 应该占据窗口的大部分高度")
        print("   - 各个标签页（频率分析、遗漏分析等）应该有足够的显示空间")
        print()
        print("2. 📌 操作按钮是否固定在底部")
        print("   - '导出报告'和'保存号码'按钮应该在窗口底部")
        print("   - 底部应该有警告提示文字")
        print()
        print("3. 📦 上部区域是否紧凑")
        print("   - 彩种选择、号码输入、评价结果、评分设置应该紧凑排列")
        print("   - 不应该占用过多垂直空间")
        print()
        print("4. 🔄 尝试调整窗口大小")
        print("   - 详细分析区域应该随窗口大小自动调整")
        print("   - 上部和底部区域应该保持固定高度")
        print()
        print("5. 🎯 测试功能")
        print("   - 尝试输入号码并点击'评价号码'")
        print("   - 查看详细分析区域是否正常显示结果")
        print()
        print("6. 🌓 暗色模式测试（如果系统使用暗色模式）")
        print("   - 详细分析区域的文字应该清晰可见")
        print("   - 文字颜色应该是深色（#212529）")
        print("   - 背景颜色应该是浅色（#f8f9fa）")
        print("   - 不应该出现文字与背景同色的情况")
        print()
        print("=" * 80)
        print()
        print("关闭窗口以结束测试...")
        print()
        
        # 运行主循环
        root.mainloop()
        
        print()
        print("测试结束！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

