#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去热门算法快速演示
"""

import sys
sys.path.insert(0, 'src')

from src.core.generators.smart_generator import SmartNumberGenerator


def main():
    print("\n" + "🎯" * 40)
    print("去热门算法快速演示")
    print("🎯" * 40 + "\n")
    
    # 1. 双色球去热门（适中模式）
    print("=" * 80)
    print("示例 1: 双色球去热门算法（适中模式）")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    
    numbers = generator.generate_anti_popular(5)
    
    print("\n生成的号码：")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")
    
    # 2. 大乐透去热门（适中模式）
    print("\n\n" + "=" * 80)
    print("示例 2: 大乐透去热门算法（适中模式）")
    print("=" * 80)
    
    generator_dlt = SmartNumberGenerator('dlt')
    generator_dlt.set_anti_popular_config(enabled=True, mode='moderate')
    
    numbers_dlt = generator_dlt.generate_anti_popular(5)
    
    print("\n生成的号码：")
    for i, num in enumerate(numbers_dlt, 1):
        print(f"  {i}. 前区: {' '.join(f'{x:02d}' for x in num.front)} | 后区: {' '.join(f'{x:02d}' for x in num.back)}")
    
    # 3. 混合模式
    print("\n\n" + "=" * 80)
    print("示例 3: 混合模式（50%去热门 + 50%统计优选）")
    print("=" * 80)
    
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    hybrid_numbers = generator.generate_hybrid(10, anti_popular_ratio=0.5)
    
    print("\n最终生成的号码：")
    for i, num in enumerate(hybrid_numbers, 1):
        print(f"  {i:2d}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")
    
    print("\n\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80)
    
    print("\n💡 使用建议:")
    print("  • moderate模式：推荐日常使用，平衡独特性和灵活性")
    print("  • strict模式：追求最大独特性，适合多人合买")
    print("  • light模式：轻度规避热门，保持较高灵活性")
    print("  • hybrid模式：结合两种算法优势，获得多样化号码")
    
    print("\n⚠️  重要提醒:")
    print("  • 去热门算法不会提高中奖概率")
    print("  • 目的是减少与他人撞号导致的分奖风险")
    print("  • 请理性购彩，量力而行！")
    
    print("\n📚 更多信息:")
    print("  • 详细文档: docs/anti_popular_algorithm_guide.md")
    print("  • 完整示例: examples/anti_popular_usage.py")
    print("  • 测试脚本: test_anti_popular.py")


if __name__ == "__main__":
    main()

