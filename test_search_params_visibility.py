#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索参数可见性和候选池标签动态更新功能

功能1：搜索参数只在"最高评分（整注）"策略时显示
功能2：候选池标签根据彩票类型动态更新
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import tkinter as tk
from tkinter import ttk

def test_search_params_visibility():
    """测试搜索参数的显示/隐藏功能"""
    print("="*70)
    print(" "*15 + "搜索参数可见性测试")
    print("="*70)
    print()
    
    from src.gui.generation_frame import GenerationFrame
    from src.core.data_manager import LotteryDataManager

    root = tk.Tk()
    root.title("搜索参数可见性测试")
    root.geometry("900x700")

    # 创建数据管理器
    data_manager = LotteryDataManager()

    # 创建生成页（analyzer 参数已废弃）
    generation_frame = GenerationFrame(root, data_manager)
    generation_frame.pack(fill=tk.BOTH, expand=True)
    
    print("✅ GUI已创建")
    print()
    print("📋 测试说明：")
    print()
    print("【功能1：搜索参数可见性】")
    print("  1. 默认策略为'统计优选'，搜索参数应该是隐藏的")
    print("  2. 切换到'最高评分（整注）'策略，搜索参数应该显示")
    print("  3. 切换回其他策略，搜索参数应该再次隐藏")
    print()
    print("【功能2：候选池标签动态更新】")
    print("  1. 选择'双色球'，候选池标签应显示'候选池(红):'")
    print("  2. 选择'大乐透'，候选池标签应显示'候选池(前区):'")
    print("  3. 切换策略到'最高评分（整注）'后再切换彩票类型，标签应正确更新")
    print()
    print("【测试步骤】")
    print("  步骤1：观察默认状态（统计优选策略）")
    print("         → 搜索参数（统计期数、候选池）应该是隐藏的")
    print()
    print("  步骤2：切换策略到'最高评分（整注）'")
    print("         → 搜索参数应该显示")
    print("         → 评分参数提示应该显示（蓝色文字）")
    print("         → 候选池标签应显示'候选池(红):'（因为默认是双色球）")
    print()
    print("  步骤3：保持'最高评分（整注）'策略，切换彩票类型到'大乐透'")
    print("         → 候选池标签应更新为'候选池(前区):'")
    print("         → 搜索参数仍然显示")
    print()
    print("  步骤4：切换彩票类型回'双色球'")
    print("         → 候选池标签应更新为'候选池(红):'")
    print()
    print("  步骤5：切换策略到'随机生成'")
    print("         → 搜索参数应该隐藏")
    print("         → 评分参数提示应该隐藏")
    print()
    print("  步骤6：再次切换策略到'最高评分（整注）'")
    print("         → 搜索参数应该再次显示")
    print("         → 候选池标签应正确显示当前彩票类型对应的文字")
    print()
    print("="*70)
    print()
    print("💡 提示：")
    print("  - 搜索参数包括：'统计期数' 和 '候选池(红/前区)'")
    print("  - 只有'最高评分（整注）'策略需要这些参数")
    print("  - 其他策略不使用这些参数，因此应该隐藏以避免混淆")
    print()
    print("🚀 GUI已启动，请按照上述步骤进行测试...")
    print()
    
    root.mainloop()

def test_programmatic():
    """程序化测试（不启动GUI）"""
    print("="*70)
    print(" "*15 + "程序化测试")
    print("="*70)
    print()
    
    from src.gui.generation_frame import GenerationFrame
    from src.core.data_manager import LotteryDataManager

    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    data_manager = LotteryDataManager()
    generation_frame = GenerationFrame(root, data_manager)
    
    print("测试1：检查控件是否正确创建")
    assert hasattr(generation_frame, 'periods_label'), "❌ periods_label 未创建"
    assert hasattr(generation_frame, 'periods_spinbox'), "❌ periods_spinbox 未创建"
    assert hasattr(generation_frame, 'pool_size_label'), "❌ pool_size_label 未创建"
    assert hasattr(generation_frame, 'pool_size_spinbox'), "❌ pool_size_spinbox 未创建"
    print("  ✅ 所有搜索参数控件已创建")
    print()
    
    print("测试2：检查方法是否存在")
    assert hasattr(generation_frame, '_show_search_params'), "❌ _show_search_params 方法不存在"
    assert hasattr(generation_frame, '_hide_search_params'), "❌ _hide_search_params 方法不存在"
    assert hasattr(generation_frame, '_update_pool_size_label'), "❌ _update_pool_size_label 方法不存在"
    print("  ✅ 所有新增方法已实现")
    print()
    
    print("测试3：测试候选池标签更新")
    # 测试双色球
    generation_frame.lottery_type_var.set('ssq')
    generation_frame._update_pool_size_label()
    label_text = generation_frame.pool_size_label.cget('text')
    assert label_text == "候选池(红):", f"❌ 双色球标签错误: {label_text}"
    print(f"  ✅ 双色球: {label_text}")
    
    # 测试大乐透
    generation_frame.lottery_type_var.set('dlt')
    generation_frame._update_pool_size_label()
    label_text = generation_frame.pool_size_label.cget('text')
    assert label_text == "候选池(前区):", f"❌ 大乐透标签错误: {label_text}"
    print(f"  ✅ 大乐透: {label_text}")
    print()
    
    print("测试4：测试显示/隐藏功能")
    # 显示
    generation_frame._show_search_params()
    print("  ✅ _show_search_params() 调用成功")
    
    # 隐藏
    generation_frame._hide_search_params()
    print("  ✅ _hide_search_params() 调用成功")
    print()
    
    print("="*70)
    print(" "*20 + "所有程序化测试通过 ✅")
    print("="*70)
    print()
    
    root.destroy()

if __name__ == "__main__":
    print()
    print("="*70)
    print(" "*10 + "搜索参数可见性和候选池标签测试")
    print("="*70)
    print()
    print("选择测试模式：")
    print("  1. GUI测试（手动验证）")
    print("  2. 程序化测试（自动验证）")
    print("  3. 两者都运行")
    print()
    
    choice = input("请选择 (1/2/3，默认1): ").strip() or "1"
    print()
    
    if choice == "1":
        test_search_params_visibility()
    elif choice == "2":
        test_programmatic()
    elif choice == "3":
        test_programmatic()
        print()
        print("按回车键继续GUI测试...")
        input()
        test_search_params_visibility()
    else:
        print("无效选择，退出")

