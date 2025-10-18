#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试去热门算法功能
"""

import sys
sys.path.insert(0, 'src')

from src.core.generators.smart_generator import SmartNumberGenerator


def test_ssq_anti_popular():
    """测试双色球去热门算法"""
    print("=" * 80)
    print("测试 1: 双色球去热门算法")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    
    # 测试不同模式
    modes = ['strict', 'moderate', 'light']
    
    for mode in modes:
        print(f"\n{'='*80}")
        print(f"测试模式: {mode.upper()}")
        print(f"{'='*80}")
        
        generator.set_anti_popular_config(enabled=True, mode=mode)
        
        # 查看配置
        config = generator.get_anti_popular_config()
        print(f"\n配置信息:")
        print(f"  模式: {config['mode']}")
        print(f"  描述: {config['description'][mode]}")
        print(f"  最大热门分数: {config['lottery_config']['max_score']}")
        print(f"  最大连号: {config['lottery_config']['max_run']}")
        print(f"  红球最大重叠: {config['lottery_config']['max_red_overlap']}")
        print()
        
        # 生成号码
        numbers = generator.generate_anti_popular(5)
        
        print(f"\n生成的号码:")
        for i, num in enumerate(numbers, 1):
            print(f"  {i}. 红球: {num.red} | 蓝球: {num.blue}")


def test_dlt_anti_popular():
    """测试大乐透去热门算法"""
    print("\n\n" + "=" * 80)
    print("测试 2: 大乐透去热门算法")
    print("=" * 80)
    
    generator = SmartNumberGenerator('dlt')
    
    # 测试适中模式
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    
    config = generator.get_anti_popular_config()
    print(f"\n配置信息:")
    print(f"  模式: {config['mode']}")
    print(f"  最大热门分数: {config['lottery_config']['max_score']}")
    print(f"  前区最大重叠: {config['lottery_config']['max_front_overlap']}")
    print(f"  后区最大重叠: {config['lottery_config']['max_back_overlap']}")
    print()
    
    # 生成号码
    numbers = generator.generate_anti_popular(5)
    
    print(f"\n生成的号码:")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 前区: {num.front} | 后区: {num.back}")


def test_hybrid_mode():
    """测试混合模式"""
    print("\n\n" + "=" * 80)
    print("测试 3: 混合模式（50%去热门 + 50%统计优选）")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    
    # 生成混合号码
    numbers = generator.generate_hybrid(10, anti_popular_ratio=0.5)
    
    print(f"\n最终生成的 {len(numbers)} 注号码:")
    for i, num in enumerate(numbers, 1):
        print(f"  {i:2d}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def test_custom_config():
    """测试自定义配置"""
    print("\n\n" + "=" * 80)
    print("测试 4: 自定义配置")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    
    # 自定义配置：超严格模式
    generator.set_anti_popular_config(
        enabled=True,
        mode='strict',
        max_score=0,  # 只接受0分的号码
        max_run=1,    # 不允许连号
        max_red_overlap=0,  # 不允许红球重叠
        tries_per_ticket=100  # 增加尝试次数
    )
    
    config = generator.get_anti_popular_config()
    print(f"\n自定义配置:")
    print(f"  最大热门分数: {config['lottery_config']['max_score']}")
    print(f"  最大连号: {config['lottery_config']['max_run']}")
    print(f"  红球最大重叠: {config['lottery_config']['max_red_overlap']}")
    print(f"  每注尝试次数: {config['lottery_config']['tries_per_ticket']}")
    print()
    
    # 生成号码（可能会降级接受）
    numbers = generator.generate_anti_popular(3)
    
    print(f"\n生成的号码:")
    for i, num in enumerate(numbers, 1):
        print(f"  {i}. 红球: {num.red} | 蓝球: {num.blue}")


def test_comparison():
    """对比测试：统计优选 vs 去热门"""
    print("\n\n" + "=" * 80)
    print("测试 5: 对比测试（统计优选 vs 去热门）")
    print("=" * 80)
    
    generator = SmartNumberGenerator('ssq')
    
    # 统计优选
    print("\n【统计优选算法】")
    print("-" * 80)
    smart_numbers = generator.generate_recommended(5)
    for i, num in enumerate(smart_numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")
    
    # 去热门
    print("\n【去热门算法】")
    print("-" * 80)
    generator.set_anti_popular_config(enabled=True, mode='moderate')
    anti_pop_numbers = generator.generate_anti_popular(5)
    for i, num in enumerate(anti_pop_numbers, 1):
        print(f"  {i}. 红球: {' '.join(f'{x:02d}' for x in num.red)} | 蓝球: {num.blue:02d}")


def main():
    """主测试函数"""
    print("\n" + "🎯" * 40)
    print("去热门算法功能测试")
    print("🎯" * 40 + "\n")
    
    try:
        # 测试1: SSQ去热门
        test_ssq_anti_popular()
        
        # 测试2: DLT去热门
        test_dlt_anti_popular()
        
        # 测试3: 混合模式
        test_hybrid_mode()
        
        # 测试4: 自定义配置
        test_custom_config()
        
        # 测试5: 对比测试
        test_comparison()
        
        print("\n\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
        print("\n💡 使用建议:")
        print("  1. strict模式：追求最大独特性，适合多人合买")
        print("  2. moderate模式：平衡独特性和灵活性，推荐日常使用")
        print("  3. light模式：轻度规避热门，保持较高灵活性")
        print("  4. hybrid模式：结合两种算法优势，获得多样化号码")
        
        print("\n⚠️  重要提醒:")
        print("  • 去热门算法不会提高中奖概率")
        print("  • 目的是减少与他人撞号导致的分奖风险")
        print("  • 在中奖概率不变的前提下，提高独享奖金的机会")
        print("  • 请理性购彩，量力而行")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

