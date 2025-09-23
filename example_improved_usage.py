#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
改进蓝球算法的使用示例
展示如何在实际应用中使用新的多因子加权算法
"""

import sys
import os
sys.path.insert(0, 'src')

from core.generators.smart_generator import SmartNumberGenerator

def demonstrate_improved_algorithm():
    """演示改进算法的使用方法"""
    print("🎯 改进的双色球蓝球选择算法使用示例\n")
    
    # 1. 创建智能生成器
    generator = SmartNumberGenerator('ssq')
    
    # 2. 查看当前配置
    print("1. 当前算法配置:")
    config = generator.get_blue_algorithm_info()
    print(f"   算法方法: {config['current_method']}")
    print(f"   分析期数: {config['analysis_periods']}")
    print("   权重配置:")
    for factor, weight in config['weights'].items():
        print(f"     {factor}: {weight:.2f}")
    
    # 3. 使用默认配置生成号码
    print("\n2. 使用默认配置生成推荐号码:")
    try:
        numbers = generator.generate_recommended(3)
        for i, num in enumerate(numbers, 1):
            if hasattr(num, 'red') and hasattr(num, 'blue'):
                print(f"   推荐 {i}: 红球 {num.red} 蓝球 {num.blue}")
    except Exception as e:
        print(f"   生成失败: {e}")
    
    # 4. 切换到简单算法
    print("\n3. 切换到简单频率算法:")
    generator.set_blue_algorithm_config(method='simple')
    try:
        numbers = generator.generate_recommended(2)
        for i, num in enumerate(numbers, 1):
            if hasattr(num, 'red') and hasattr(num, 'blue'):
                print(f"   简单算法 {i}: 红球 {num.red} 蓝球 {num.blue}")
    except Exception as e:
        print(f"   生成失败: {e}")
    
    # 5. 使用集成算法
    print("\n4. 使用集成算法:")
    generator.set_blue_algorithm_config(method='ensemble')
    try:
        numbers = generator.generate_recommended(2)
        for i, num in enumerate(numbers, 1):
            if hasattr(num, 'red') and hasattr(num, 'blue'):
                print(f"   集成算法 {i}: 红球 {num.red} 蓝球 {num.blue}")
    except Exception as e:
        print(f"   生成失败: {e}")
    
    # 6. 自定义权重配置
    print("\n5. 自定义权重配置示例:")
    
    # 频率优先配置
    freq_weights = {
        'frequency': 0.6,
        'missing': 0.2,
        'trend': 0.1,
        'pattern': 0.05,
        'random': 0.05
    }
    
    print("   频率优先配置:")
    generator.set_blue_algorithm_config(method='enhanced', weights=freq_weights)
    try:
        numbers = generator.generate_recommended(2)
        for i, num in enumerate(numbers, 1):
            if hasattr(num, 'red') and hasattr(num, 'blue'):
                print(f"     频率优先 {i}: 红球 {num.red} 蓝球 {num.blue}")
    except Exception as e:
        print(f"     生成失败: {e}")
    
    # 遗漏优先配置
    missing_weights = {
        'frequency': 0.2,
        'missing': 0.6,
        'trend': 0.1,
        'pattern': 0.05,
        'random': 0.05
    }
    
    print("\n   遗漏优先配置:")
    generator.set_blue_algorithm_config(method='enhanced', weights=missing_weights)
    try:
        numbers = generator.generate_recommended(2)
        for i, num in enumerate(numbers, 1):
            if hasattr(num, 'red') and hasattr(num, 'blue'):
                print(f"     遗漏优先 {i}: 红球 {num.red} 蓝球 {num.blue}")
    except Exception as e:
        print(f"     生成失败: {e}")
    
    # 7. 算法对比
    print("\n6. 不同算法效果对比:")
    methods = ['simple', 'enhanced', 'ensemble']
    
    for method in methods:
        print(f"\n   {method.upper()} 方法:")
        generator.set_blue_algorithm_config(method=method)
        
        blue_numbers = []
        try:
            for _ in range(5):
                numbers = generator.generate_recommended(1)
                if numbers and hasattr(numbers[0], 'blue'):
                    blue_numbers.append(numbers[0].blue)
            
            if blue_numbers:
                from collections import Counter
                distribution = Counter(blue_numbers)
                print(f"     生成的蓝球: {blue_numbers}")
                print(f"     分布情况: {dict(distribution)}")
                print(f"     唯一号码数: {len(set(blue_numbers))}")
            else:
                print("     生成失败")
        except Exception as e:
            print(f"     错误: {e}")

def show_algorithm_comparison():
    """展示算法改进前后的对比"""
    print("\n" + "="*60)
    print("📊 算法改进对比分析")
    print("="*60)
    
    print("\n🔍 原始算法特点:")
    print("   ✓ 实现简单，计算效率高")
    print("   ✓ 基于频率统计，有一定合理性")
    print("   ✗ 只考虑单一频率因素")
    print("   ✗ 忽略遗漏和趋势信息")
    print("   ✗ 容易过度拟合历史数据")
    
    print("\n🚀 改进算法特点:")
    print("   ✓ 多因子综合评估（频率+遗漏+趋势+模式）")
    print("   ✓ 可配置的权重系统")
    print("   ✓ 三种算法模式可选")
    print("   ✓ 加入随机性防过拟合")
    print("   ✓ 更好的鲁棒性和适应性")
    
    print("\n📈 算法模式说明:")
    print("   • SIMPLE: 基于历史频率的简单概率选择")
    print("   • ENHANCED: 多因子加权模型，综合考虑多个维度")
    print("   • ENSEMBLE: 集成多种策略，提供最佳鲁棒性")
    
    print("\n⚙️ 权重因子说明:")
    print("   • frequency: 历史出现频率权重")
    print("   • missing: 遗漏期数权重")
    print("   • trend: 近期趋势权重")
    print("   • pattern: 数学模式权重（奇偶、大小、质数等）")
    print("   • random: 随机性权重（防过拟合）")
    
    print("\n💡 使用建议:")
    print("   1. 日常使用推荐 'enhanced' 方法")
    print("   2. 追求稳定性选择 'ensemble' 方法")
    print("   3. 可根据个人偏好调整权重")
    print("   4. 定期评估算法表现并调整参数")
    print("   5. 保持理性，算法仅供参考")

def main():
    """主函数"""
    try:
        demonstrate_improved_algorithm()
        show_algorithm_comparison()
        
        print("\n" + "="*60)
        print("✅ 改进算法演示完成")
        print("="*60)
        print("\n📝 总结:")
        print("   • 改进的算法提供了更全面的分析维度")
        print("   • 用户可以根据需要选择不同的算法模式")
        print("   • 权重配置允许个性化调整")
        print("   • 集成方法提供了最佳的鲁棒性")
        print("\n⚠️  重要提醒:")
        print("   • 彩票本质上是随机事件")
        print("   • 任何算法都无法保证中奖")
        print("   • 请理性购彩，量力而行")
        
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
