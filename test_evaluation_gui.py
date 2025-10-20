#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试号码评价GUI功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_evaluators():
    """测试评价器"""
    print("=" * 80)
    print("测试评价器模块")
    print("=" * 80)
    
    # 测试双色球评价器
    print("\n【测试1：双色球评价器】")
    print("-" * 80)
    try:
        from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
        
        evaluator = SSQNumberEvaluator()
        print("✓ 双色球评价器初始化成功")
        
        # 测试评价
        red_numbers = [3, 9, 16, 17, 24, 33]
        blue_number = 15
        
        print(f"\n评价号码: 红球 {red_numbers} | 蓝球 {blue_number}")
        print("正在评价...")
        
        result = evaluator.evaluate(red_numbers, blue_number)
        
        print(f"\n✓ 评价完成")
        print(f"  综合得分: {result['total_score']:.1f}/100")
        print(f"  评级: {result['rating']} {result['stars']}")
        print(f"  频率得分: {result['scores']['frequency']:.1f}/100")
        print(f"  遗漏得分: {result['scores']['missing']:.1f}/100")
        print(f"  模式得分: {result['scores']['pattern']:.1f}/100")
        print(f"  独特性得分: {result['scores']['uniqueness']:.1f}/100")
        print(f"  建议数量: {len(result['suggestions'])} 条")
        
    except Exception as e:
        print(f"✗ 双色球评价器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试大乐透评价器
    print("\n【测试2：大乐透评价器】")
    print("-" * 80)
    try:
        from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator
        
        evaluator = DLTNumberEvaluator()
        print("✓ 大乐透评价器初始化成功")
        
        # 测试评价
        front_numbers = [1, 5, 12, 23, 35]
        back_numbers = [3, 11]
        
        print(f"\n评价号码: 前区 {front_numbers} | 后区 {back_numbers}")
        print("正在评价...")
        
        result = evaluator.evaluate(front_numbers, back_numbers)
        
        print(f"\n✓ 评价完成")
        print(f"  综合得分: {result['total_score']:.1f}/100")
        print(f"  评级: {result['rating']} {result['stars']}")
        print(f"  频率得分: {result['scores']['frequency']:.1f}/100")
        print(f"  遗漏得分: {result['scores']['missing']:.1f}/100")
        print(f"  模式得分: {result['scores']['pattern']:.1f}/100")
        print(f"  独特性得分: {result['scores']['uniqueness']:.1f}/100")
        print(f"  建议数量: {len(result['suggestions'])} 条")
        
    except Exception as e:
        print(f"✗ 大乐透评价器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("✓ 所有评价器测试通过")
    print("=" * 80)
    return True

def test_gui_import():
    """测试GUI导入"""
    print("\n" + "=" * 80)
    print("测试GUI模块导入")
    print("=" * 80)
    
    try:
        from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
        print("✓ NumberEvaluationFrame 导入成功")
        
        from src.gui.main_window import LotteryApp
        print("✓ LotteryApp 导入成功")
        
        print("\n" + "=" * 80)
        print("✓ 所有GUI模块导入成功")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"✗ GUI模块导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def launch_gui():
    """启动GUI"""
    print("\n" + "=" * 80)
    print("启动GUI应用")
    print("=" * 80)
    
    try:
        import tkinter as tk
        from src.gui.main_window import LotteryApp
        
        root = tk.Tk()
        app = LotteryApp(root)
        
        print("\n✓ GUI应用已启动")
        print("\n请在GUI中测试以下功能:")
        print("  1. 切换到\"号码评价\"标签页")
        print("  2. 选择彩种（双色球/大乐透）")
        print("  3. 点击\"随机生成\"按钮")
        print("  4. 点击\"评价号码\"按钮")
        print("  5. 查看评价结果和详细分析")
        print("  6. 尝试导出报告")
        print("\n关闭窗口以退出测试...")
        
        root.mainloop()
        
        print("\n✓ GUI应用已关闭")
        return True
        
    except Exception as e:
        print(f"✗ GUI启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("号码评价GUI功能测试")
    print("=" * 80)
    
    # 测试评价器
    if not test_evaluators():
        print("\n✗ 评价器测试失败，停止测试")
        sys.exit(1)
    
    # 测试GUI导入
    if not test_gui_import():
        print("\n✗ GUI导入测试失败，停止测试")
        sys.exit(1)
    
    # 询问是否启动GUI
    print("\n" + "=" * 80)
    response = input("是否启动GUI进行手动测试？(y/n): ")
    
    if response.lower() == 'y':
        launch_gui()
    else:
        print("\n跳过GUI测试")
    
    print("\n" + "=" * 80)
    print("✓ 所有测试完成")
    print("=" * 80)

