#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试"最高评分（整注）"生成策略的完整功能
包括：
1. 联动评价页的评分设置
2. 暴露搜索参数（periods、pool-size）
3. 显示每注的评分值
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import tkinter as tk
from tkinter import ttk
from src.gui.main_window import LotteryApp

def test_top_scored_generation():
    """启动GUI并测试最高评分生成策略"""
    print("=" * 60)
    print("测试：最高评分（整注）生成策略")
    print("=" * 60)
    print("\n测试步骤：")
    print("1. 切换到【号码评价】标签页")
    print("   - 找到"评分设置（双色球）"面板")
    print("   - 修改蓝球频率权重（例如：0.20）")
    print("   - 修改蓝球遗漏权重（例如：0.20）")
    print("   - 修改遗漏曲线（例如：gaussian）")
    print("   - 修改σ系数（例如：1.5）")
    print()
    print("2. 切换到【号码推荐】标签页")
    print("   - 选择彩票类型：双色球")
    print("   - 设置生成注数：3")
    print("   - 选择生成策略：最高评分（整注）")
    print("   - 观察是否显示"当前评分参数"（蓝色字体）")
    print("   - 调整统计期数（例如：50）")
    print("   - 调整候选池(红)（例如：15）")
    print()
    print("3. 点击【生成号码】按钮")
    print("   - 观察状态提示：'正在搜索最高评分组合，请稍候...'（橙色）")
    print("   - 等待生成完成（约10-30秒，取决于参数）")
    print("   - 观察状态提示变为：'生成完成'（绿色）")
    print()
    print("4. 检查结果")
    print("   - 每注号码后应显示：| 评分: xx.x")
    print("   - 评分应该是从高到低排列")
    print("   - 评分应该反映你在评价页设置的参数")
    print()
    print("5. 验证联动")
    print("   - 返回【号码评价】页，修改评分参数")
    print("   - 返回【号码推荐】页，观察"当前评分参数"是否更新")
    print("   - 重新生成，观察评分是否变化")
    print()
    print("=" * 60)
    print("启动GUI...")
    print("=" * 60)
    
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()

if __name__ == "__main__":
    test_top_scored_generation()

