#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去热门算法使用示例
展示如何使用去热门算法生成彩票号码
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.generators.smart_generator import SmartNumberGenerator


def example_1_basic_usage():
    """示例1：基础用法"""
    print("=" * 80)
    print("示例 1: 基础用法 - 使用默认适中模式")
    print("=" * 80)
    
    # 创建生成器
    generator = SmartNumberGenerator('ssq')
    
    # 启用去热门模式（默认适中模式）
    generator.set_anti_popular_config(enabled=True)
    
    # 生成5注号码
    numbers = generator.generate_anti_popular(5)
    
    print("\n生成的号码：")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def example_2_different_modes():
    """示例2：不同模式对比"""
    print("\n\n" + "=" * 80)
    print("示例 2: 不同模式对比")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    modes = ['strict', 'moderate', 'light']
    
    for mode in modes:
        print(f"\n【{mode.upper()} 模式】")
        print("-" * 80)
        
        generator.set_anti_popular_config(enabled=True, mode=mode)
        numbers = generator.generate_anti_popular(3)
        
        for i, num in enumerate(numbers, 1):
            print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def example_3_custom_config():
    """示例3：自定义配置"""
    print("\n\n" + "=" * 80)
    print("示例 3: 自定义配置 - 超严格模式")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    
    # 自定义超严格配置
    generator.set_anti_popular_config(
        enabled=True,
        mode='strict',
        max_score=1,           # 只接受热门度≤1的号码
        max_run=1,             # 不允许连号
        max_red_overlap=1,     # 红球最多重叠1个
        tries_per_ticket=80    # 增加尝试次数
    )
    
    # 查看配置
    config = generator.get_anti_popular_config()
    print("\n当前配置：")
    print(f"  模式: {config['mode']}")
    print(f"  最大热门分数: {config['lottery_config']['max_score']}")
    print(f"  最大连号: {config['lottery_config']['max_run']}")
    print(f"  红球最大重叠: {config['lottery_config']['max_red_overlap']}")
    print()
    
    numbers = generator.generate_anti_popular(3)
    
    print("\n生成的号码：")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def example_4_hybrid_mode():
    """示例4：混合模式"""
    print("\n\n" + "=" * 80)
    print("示例 4: 混合模式 - 结合统计优选和去热门")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    
    # 生成10注：50%去热门 + 50%统计优选
    print("\n生成10注号码（50%去热门 + 50%统计优选）")
    numbers = generator.generate_hybrid(10, anti_popular_ratio=0.5)
    
    print("\n最终号码（已打乱顺序）：")
    for i, num in enumerate(numbers, 1):
        print(f"  {i:2d}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def example_5_dlt():
    """示例5：大乐透去热门"""
    print("\n\n" + "=" * 80)
    print("示例 5: 大乐透去热门算法")
    print("=" * 80)
    
    generator = SmartNumberGenerator('dlt')
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    
    numbers = generator.generate_anti_popular(5)
    
    print("\n生成的大乐透号码：")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 前区: {' '.join(f'{x:02d}' for x in num.front)} | 后区: {' '.join(f'{x:02d}' for x in num.back)}")


def example_6_analyze_popularity():
    """示例6：分析号码热门度"""
    print("\n\n" + "=" * 80)
    print("示例 6: 分析号码热门度")
    print("=" * 80)

    from core.generators.anti_popular import PopularityDetector
    
    # 测试几组号码
    test_cases = [
        ([1, 2, 3, 4, 5, 6], 8, "连号组合"),
        ([5, 10, 15, 20, 25, 30], 10, "等差数列"),
        ([3, 13, 23, 7, 17, 27], 9, "同尾数多"),
        ([2, 8, 15, 21, 28, 33], 5, "分散组合"),
    ]
    
    print("\n热门度分析：")
    print("-" * 80)
    
    for red, blue, desc in test_cases:
        score = PopularityDetector.calculate_ssq_score(red, blue, (70, 140))
        
        if score <= 2:
            level = "✅ 独特"
        elif score <= 5:
            level = "⚠️ 中等"
        else:
            level = "❌ 热门"
        
        print(f"\n{desc}:")
        print(f"  红球: {' '.join(f'{x:02d}' for x in red)} | 蓝球: {blue:02d}")
        print(f"  热门度: {score} 分 - {level}")


def example_7_batch_generation():
    """示例7：批量生成并筛选"""
    print("\n\n" + "=" * 80)
    print("示例 7: 批量生成并筛选最优号码")
    print("=" * 80)

    from core.generators.anti_popular import PopularityDetector
    
    generator = SmartNumberGenerator('ssq')
    generator.set_anti_popular_config(enabled=True, mode='light')
    
    # 生成20注号码
    print("\n生成20注号码...")
    all_numbers = generator.generate_anti_popular(20)
    
    # 筛选热门度≤1的号码
    print("\n筛选热门度≤1的号码...")
    filtered = []
    for num in all_numbers:
        score = PopularityDetector.calculate_ssq_score(num.red, num.blue, (70, 140))
        if score <= 1:
            filtered.append((num, score))
    
    print(f"\n筛选结果：从20注中筛选出 {len(filtered)} 注极度独特的号码")
    print("-" * 80)
    
    for i, (num, score) in enumerate(filtered, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d} | 热门度: {score}")


def example_8_comparison():
    """示例8：算法对比"""
    print("\n\n" + "=" * 80)
    print("示例 8: 三种算法对比")
    print("=" * 80)

    from core.generators.random_generator import RandomGenerator
    
    # 1. 完全随机
    print("\n【完全随机算法】")
    print("-" * 80)
    random_gen = RandomGenerator('ssq')
    for i in range(3):
        num = random_gen.generate_single()
        red = num['red']
        blue = num['blue']
        print(f"  {i+1}. 红球: {' '.join(f'{x:02d}' for x in red)} | 蓝球: {blue:02d}")
    
    # 2. 统计优选
    print("\n【统计优选算法】")
    print("-" * 80)
    smart_gen = SmartNumberGenerator('ssq')
    numbers = smart_gen.generate_recommended(3)
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")
    
    # 3. 去热门
    print("\n【去热门算法】")
    print("-" * 80)
    smart_gen.set_anti_popular_config(enabled=True, mode='moderate')
    numbers = smart_gen.generate_anti_popular(3)
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def main():
    """主函数"""
    print("\n" + "🎯" * 40)
    print("去热门算法使用示例")
    print("🎯" * 40 + "\n")
    
    try:
        # 运行所有示例
        example_1_basic_usage()
        example_2_different_modes()
        example_3_custom_config()
        example_4_hybrid_mode()
        example_5_dlt()
        example_6_analyze_popularity()
        example_7_batch_generation()
        example_8_comparison()
        
        print("\n\n" + "=" * 80)
        print("✅ 所有示例运行完成！")
        print("=" * 80)
        
        print("\n💡 快速开始：")
        print("```python")
        print("from core.generators.smart_generator import SmartNumberGenerator")
        print("")
        print("# 创建生成器并启用去热门模式")
        print("generator = SmartNumberGenerator('ssq')")
        print("generator.set_anti_popular_config(enabled=True, mode='moderate')")
        print("")
        print("# 生成号码")
        print("numbers = generator.generate_anti_popular(10)")
        print("```")
        
        print("\n📚 更多信息：")
        print("  • 详细文档: docs/anti_popular_algorithm_guide.md")
        print("  • 测试脚本: test_anti_popular.py")
        print("  • 源代码: src/core/generators/anti_popular/")
        
        print("\n⚠️  重要提醒：")
        print("  去热门算法不会提高中奖概率，只是减少分奖风险")
        print("  请理性购彩，量力而行！")
        
    except Exception as e:
        print(f"\n❌ 运行示例时出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

