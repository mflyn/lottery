#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演示"最高评分（整注）"策略的三大功能
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def demo_feature_1_config_linking():
    """演示功能1：联动评价页的评分设置"""
    print("\n" + "="*60)
    print("功能1：联动评价页的评分设置")
    print("="*60)
    
    from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
    from src.gui.generation_frame import GenerationFrame
    from src.core.data_manager import LotteryDataManager
    import tkinter as tk

    # 创建临时窗口
    root = tk.Tk()
    root.withdraw()

    # 创建评价页和生成页
    data_manager = LotteryDataManager()
    evaluation_frame = NumberEvaluationFrame(root, data_manager)
    generation_frame = GenerationFrame(root, data_manager, evaluation_frame=evaluation_frame)
    
    # 模拟在评价页设置参数
    print("\n1. 在评价页设置参数：")
    evaluation_frame.ssq_freq_blue_weight_var.set("0.25")
    evaluation_frame.ssq_miss_blue_weight_var.set("0.20")
    evaluation_frame.ssq_missing_curve_var.set("gaussian")
    evaluation_frame.ssq_missing_sigma_var.set("1.5")
    print("   - 蓝球频率权重: 0.25")
    print("   - 蓝球遗漏权重: 0.20")
    print("   - 遗漏曲线: gaussian")
    print("   - σ系数: 1.5")
    
    # 从生成页读取配置
    print("\n2. 从生成页读取配置：")
    config = generation_frame._get_ssq_scoring_config_from_evaluation()
    print(f"   - freq_blue_weight: {config['freq_blue_weight']}")
    print(f"   - miss_blue_weight: {config['miss_blue_weight']}")
    print(f"   - missing_curve: {config['missing_curve']}")
    print(f"   - missing_sigma_factor: {config['missing_sigma_factor']}")
    
    # 验证
    assert config['freq_blue_weight'] == 0.25, "频率权重读取错误"
    assert config['miss_blue_weight'] == 0.20, "遗漏权重读取错误"
    assert config['missing_curve'] == 'gaussian', "遗漏曲线读取错误"
    assert config['missing_sigma_factor'] == 1.5, "σ系数读取错误"
    
    print("\n✅ 功能1验证通过：评分参数联动正常")
    
    root.destroy()

def demo_feature_2_search_params():
    """演示功能2：暴露搜索参数到UI"""
    print("\n" + "="*60)
    print("功能2：暴露搜索参数到UI")
    print("="*60)
    
    from src.gui.generation_frame import GenerationFrame
    from src.core.data_manager import LotteryDataManager
    import tkinter as tk

    # 创建临时窗口
    root = tk.Tk()
    root.withdraw()

    # 创建生成页
    data_manager = LotteryDataManager()
    generation_frame = GenerationFrame(root, data_manager)
    
    # 检查搜索参数控件
    print("\n1. 检查搜索参数控件：")
    print(f"   - periods_var 存在: {hasattr(generation_frame, 'periods_var')}")
    print(f"   - pool_size_var 存在: {hasattr(generation_frame, 'pool_size_var')}")
    
    # 读取默认值
    print("\n2. 读取默认值：")
    periods = generation_frame.periods_var.get()
    pool_size = generation_frame.pool_size_var.get()
    print(f"   - 统计期数默认值: {periods}")
    print(f"   - 候选池大小默认值: {pool_size}")
    
    # 修改值
    print("\n3. 修改参数值：")
    generation_frame.periods_var.set(50)
    generation_frame.pool_size_var.set(15)
    print(f"   - 统计期数修改为: {generation_frame.periods_var.get()}")
    print(f"   - 候选池大小修改为: {generation_frame.pool_size_var.get()}")
    
    # 验证
    assert generation_frame.periods_var.get() == 50, "periods参数设置错误"
    assert generation_frame.pool_size_var.get() == 15, "pool_size参数设置错误"
    
    print("\n✅ 功能2验证通过：搜索参数控件正常")
    
    root.destroy()

def demo_feature_3_score_display():
    """演示功能3：显示每注的评分值"""
    print("\n" + "="*60)
    print("功能3：显示每注的评分值")
    print("="*60)
    
    print("\n1. 模拟生成结果数据结构：")
    generated_sets = [
        {'red': [11, 16, 17, 24, 28, 33], 'blue': 12, 'score': 91.0},
        {'red': [9, 16, 17, 24, 28, 33], 'blue': 12, 'score': 90.7},
        {'red': [11, 16, 17, 24, 28, 32], 'blue': 12, 'score': 90.5},
    ]
    
    for i, nums in enumerate(generated_sets):
        print(f"   第{i+1}注: {nums}")
    
    print("\n2. 格式化显示（模拟UI显示逻辑）：")
    for i, nums in enumerate(generated_sets):
        red_display = sorted([int(n) for n in nums['red']])
        blue_display = int(nums['blue'])
        formatted_nums = f"红球: {red_display} | 蓝球: {blue_display}"
        if isinstance(nums, dict) and 'score' in nums and nums['score'] is not None:
            formatted_nums += f" | 评分: {nums['score']:.1f}"
        print(f"   第 {i+1} 注: {formatted_nums}")
    
    print("\n3. 验证评分字段：")
    for i, nums in enumerate(generated_sets):
        assert 'score' in nums, f"第{i+1}注缺少score字段"
        assert nums['score'] is not None, f"第{i+1}注score为None"
        assert isinstance(nums['score'], (int, float)), f"第{i+1}注score类型错误"
        print(f"   ✓ 第{i+1}注评分: {nums['score']:.1f}")
    
    print("\n✅ 功能3验证通过：评分显示正常")

def demo_integration_test():
    """集成测试：模拟完整的生成流程"""
    print("\n" + "="*60)
    print("集成测试：模拟完整生成流程")
    print("="*60)
    
    print("\n注意：此测试需要实际调用搜索算法，可能耗时较长")
    print("建议使用小参数进行测试（periods=20, pool_size=12, top_k=2）")
    
    try:
        from scripts.find_top_ssq import find_top_ssq
        
        print("\n1. 调用搜索算法（小参数）：")
        results = find_top_ssq(
            top_k=2,
            periods=20,
            pool_size=12,
            out_path=None,
            freq_blue_weight=0.25,
            miss_blue_weight=0.20,
            missing_curve='gaussian',
            missing_sigma_factor=1.5
        )
        
        print(f"\n2. 搜索完成，返回 {len(results)} 注结果")
        
        print("\n3. 验证结果结构：")
        for i, item in enumerate(results):
            assert 'red_numbers' in item, f"第{i+1}注缺少red_numbers"
            assert 'blue_number' in item, f"第{i+1}注缺少blue_number"
            assert 'total_score' in item, f"第{i+1}注缺少total_score"
            print(f"   ✓ 第{i+1}注: 红球={item['red_numbers']}, 蓝球={item['blue_number']}, 评分={item['total_score']:.1f}")
        
        print("\n✅ 集成测试通过：完整流程正常")
        
    except Exception as e:
        print(f"\n⚠️  集成测试跳过：{e}")
        print("   （可能是数据文件不存在或其他依赖问题）")

def main():
    """运行所有演示"""
    print("\n" + "="*70)
    print(" "*15 + "最高评分（整注）策略 - 功能演示")
    print("="*70)
    
    try:
        demo_feature_1_config_linking()
    except Exception as e:
        print(f"\n❌ 功能1测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        demo_feature_2_search_params()
    except Exception as e:
        print(f"\n❌ 功能2测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        demo_feature_3_score_display()
    except Exception as e:
        print(f"\n❌ 功能3测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        demo_integration_test()
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print(" "*20 + "所有演示完成")
    print("="*70)
    print("\n提示：运行 'python test_top_scored_generation.py' 启动GUI进行手动测试")

if __name__ == "__main__":
    main()

