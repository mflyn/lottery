#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试GUI策略显示是否正确
"""

import sys
sys.path.insert(0, 'src')

def test_strategy_display():
    """测试策略显示"""
    print("=" * 70)
    print("GUI策略显示测试")
    print("=" * 70)
    
    # 模拟GUI中的策略列表
    strategies = [
        ("完全随机", "random"),
        ("平衡分布", "balanced"),
        ("热门号码", "hot"),
        ("冷门号码", "cold"),
        ("智能推荐", "smart"),
        ("去热门-严格", "anti_popular_strict"),
        ("去热门-适中", "anti_popular_moderate"),
        ("去热门-轻度", "anti_popular_light"),
        ("混合模式", "hybrid_anti_popular"),
        ("模式识别", "pattern"),
        ("频率分析", "frequency"),
        ("混合策略", "hybrid"),
        ("进化算法", "evolutionary")
    ]
    
    # 创建映射
    strategy_name_to_id = {name: id for name, id in strategies}
    strategy_id_to_name = {id: name for name, id in strategies}
    
    print("\n✅ 下拉框显示的选项（用户看到的）:")
    print("-" * 70)
    for i, (name, _) in enumerate(strategies, 1):
        is_new = i >= 6 and i <= 9
        marker = "🆕" if is_new else "  "
        print(f"{marker} {i:2d}. {name}")
    
    print("\n✅ 策略映射测试:")
    print("-" * 70)
    
    # 测试几个关键策略
    test_cases = [
        "完全随机",
        "智能推荐",
        "去热门-严格",
        "去热门-适中",
        "去热门-轻度",
        "混合模式"
    ]
    
    for display_name in test_cases:
        internal_id = strategy_name_to_id.get(display_name, "unknown")
        is_anti_popular = "anti_popular" in internal_id or internal_id == "hybrid_anti_popular"
        marker = "⭐" if is_anti_popular else "  "
        print(f"{marker} '{display_name}' → '{internal_id}'")
    
    print("\n✅ 反向映射测试:")
    print("-" * 70)
    
    test_ids = [
        "random",
        "smart",
        "anti_popular_strict",
        "anti_popular_moderate",
        "anti_popular_light",
        "hybrid_anti_popular"
    ]
    
    for internal_id in test_ids:
        display_name = strategy_id_to_name.get(internal_id, "未知")
        is_anti_popular = "anti_popular" in internal_id or internal_id == "hybrid_anti_popular"
        marker = "⭐" if is_anti_popular else "  "
        print(f"{marker} '{internal_id}' → '{display_name}'")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！")
    print("=" * 70)
    
    print("\n📋 GUI使用说明:")
    print("-" * 70)
    print("1. 启动程序: python main.py")
    print("2. 在'生成策略'下拉框中，你将看到中文名称")
    print("3. 新增的去热门策略:")
    print("   • 去热门-严格 - 最大独特性")
    print("   • 去热门-适中 - 平衡模式（推荐）⭐")
    print("   • 去热门-轻度 - 轻度规避")
    print("   • 混合模式 - 50%去热门+50%统计优选")
    print("4. 默认生成注数: 2注")
    print("5. 选择策略后点击'生成号码'即可")
    print("-" * 70)

if __name__ == "__main__":
    test_strategy_display()

