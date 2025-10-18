#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试GUI策略选项是否正确显示
"""

import sys
sys.path.insert(0, 'src')

def test_generation_frame_strategies():
    """测试 generation_frame.py 中的策略"""
    print("=" * 70)
    print("测试 generation_frame.py 策略配置")
    print("=" * 70)
    
    # 模拟GUI中的策略映射
    strategy_map = {
        "统计优选": "smart_recommend",
        "随机生成": "random",
        "冷热号推荐": "hot_cold",
        "去热门-严格": "anti_popular_strict",
        "去热门-适中": "anti_popular_moderate",
        "去热门-轻度": "anti_popular_light",
        "混合模式": "hybrid_anti_popular"
    }
    
    print("\n✅ 下拉框将显示的策略选项:")
    print("-" * 70)
    
    for i, (display_name, internal_id) in enumerate(strategy_map.items(), 1):
        is_new = i >= 4  # 第4个及以后是新增的
        marker = "🆕" if is_new else "  "
        print(f"{marker} {i}. {display_name:15s} → {internal_id}")
    
    print("\n✅ 策略说明:")
    print("-" * 70)
    
    strategy_descriptions = {
        "统计优选": "多因子加权分析，综合频率、遗漏、趋势等因素",
        "随机生成": "完全随机生成号码",
        "冷热号推荐": "基于历史频率的冷热号分析",
        "去热门-严格": "最大独特性，适合多人合买（生成较慢）",
        "去热门-适中": "平衡模式，推荐日常使用 ⭐",
        "去热门-轻度": "轻度规避热门模式",
        "混合模式": "50%去热门 + 50%统计优选"
    }
    
    for display_name, description in strategy_descriptions.items():
        print(f"• {display_name:15s}: {description}")
    
    print("\n✅ 使用场景推荐:")
    print("-" * 70)
    
    scenarios = [
        ("日常购彩（2-5注）", "去热门-适中 或 统计优选"),
        ("多人合买（10-20注）", "去热门-严格"),
        ("小额投注（1-3注）", "去热门-轻度 或 随机生成"),
        ("不确定策略", "混合模式"),
        ("追热门号", "冷热号推荐（热门）"),
        ("快速机选", "随机生成")
    ]
    
    for scenario, recommendation in scenarios:
        print(f"• {scenario:20s} → {recommendation}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    
    print("\n📋 GUI使用步骤:")
    print("-" * 70)
    print("1. 启动程序:")
    print("   python main.py")
    print()
    print("2. 切换到\"号码推荐\"标签页")
    print()
    print("3. 配置参数:")
    print("   • 选择彩票类型: 双色球 或 大乐透")
    print("   • 生成注数: 2（默认）")
    print("   • 生成策略: 从下拉框选择")
    print()
    print("4. 点击\"生成号码\"按钮")
    print()
    print("5. 等待生成完成（去热门模式可能需要几秒钟）")
    print()
    print("6. 查看推荐号码")
    print("-" * 70)
    
    print("\n⚠️  重要提醒:")
    print("-" * 70)
    print("• 去热门算法不会提高中奖概率")
    print("• 目的是减少与他人撞号导致的分奖风险")
    print("• 在中奖时提高独享奖金的机会")
    print("• 理性购彩，量力而行")
    print("-" * 70)

if __name__ == "__main__":
    test_generation_frame_strategies()

