#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试号码生成和验证功能
"""

import sys
from pathlib import Path
from core.generators.factory import create_generator
from core.validators.number_validator import NumberValidator
from core.models import DLTNumber, SSQNumber

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_random_generator():
    """测试随机号码生成器"""
    print("=== 测试随机号码生成器 ===")
    
    # 测试双色球
    print("\n1. 双色球随机生成:")
    ssq_generator = create_generator('random', 'ssq')
    ssq_numbers = ssq_generator.generate(count=3)
    
    for i, number in enumerate(ssq_numbers, 1):
        print(f"  第{i}注: 红球 {number.red}, 蓝球 {number.blue}")
    
    # 测试大乐透
    print("\n2. 大乐透随机生成:")
    dlt_generator = create_generator('random', 'dlt')
    dlt_numbers = dlt_generator.generate(count=3)
    
    for i, number in enumerate(dlt_numbers, 1):
        print(f"  第{i}注: 前区 {number.front}, 后区 {number.back}")

def test_smart_generator():
    """测试智能号码生成器"""
    print("\n=== 测试智能号码生成器 ===")
    
    try:
        # 测试双色球智能生成
        print("\n1. 双色球智能生成:")
        ssq_smart_generator = create_generator('smart', 'ssq')
        ssq_smart_numbers = ssq_smart_generator.generate(count=2)
        
        for i, number in enumerate(ssq_smart_numbers, 1):
            print(f"  第{i}注: 红球 {number.red}, 蓝球 {number.blue}")
        
        # 测试大乐透智能生成
        print("\n2. 大乐透智能生成:")
        dlt_smart_generator = create_generator('smart', 'dlt')
        dlt_smart_numbers = dlt_smart_generator.generate(count=2)
        
        for i, number in enumerate(dlt_smart_numbers, 1):
            print(f"  第{i}注: 前区 {number.front}, 后区 {number.back}")
            
    except Exception as e:
        print(f"智能生成器测试失败: {e}")

def test_number_validation():
    """测试号码验证功能"""
    print("\n=== 测试号码验证功能 ===")
    
    # 测试双色球验证
    print("\n1. 双色球号码验证:")
    ssq_validator = NumberValidator('ssq')
    
    # 有效号码
    valid_ssq = SSQNumber(red=[1, 5, 10, 15, 20, 25], blue=8)
    result = ssq_validator.validate(valid_ssq)
    print(f"  有效号码验证: {result}")
    
    # 无效号码（重复）
    invalid_ssq = SSQNumber(red=[1, 5, 10, 15, 20, 20], blue=8)
    result = ssq_validator.validate(invalid_ssq)
    print(f"  无效号码验证: {result}")
    
    # 测试大乐透验证
    print("\n2. 大乐透号码验证:")
    dlt_validator = NumberValidator('dlt')
    
    # 有效号码
    valid_dlt = DLTNumber(front=[2, 8, 15, 22, 30], back=[3, 9])
    result = dlt_validator.validate(valid_dlt)
    print(f"  有效号码验证: {result}")
    
    # 无效号码（超出范围）
    invalid_dlt = DLTNumber(front=[2, 8, 15, 22, 40], back=[3, 9])
    result = dlt_validator.validate(invalid_dlt)
    print(f"  无效号码验证: {result}")

def test_special_generation_strategies():
    """测试特殊生成策略"""
    print("\n=== 测试特殊生成策略 ===")
    
    try:
        # 测试热冷号生成
        print("\n1. 热冷号组合生成:")
        generator = create_generator('random', 'ssq')
        hot_cold_numbers = generator.generate_hot_cold(count=2, hot_ratio=0.5, cold_ratio=0.3)
        
        for i, number in enumerate(hot_cold_numbers, 1):
            print(f"  第{i}注: 红球 {number.red}, 蓝球 {number.blue}")
        
        # 测试连号生成
        print("\n2. 连号组合生成:")
        consecutive_numbers = generator.generate_consecutive(count=2, max_consecutive=3)
        
        for i, number in enumerate(consecutive_numbers, 1):
            print(f"  第{i}注: 红球 {number.red}, 蓝球 {number.blue}")
        
        # 测试和值范围生成
        print("\n3. 和值范围生成:")
        sum_range_numbers = generator.generate_by_sum_range(count=2, min_sum=80, max_sum=120)
        
        for i, number in enumerate(sum_range_numbers, 1):
            red_sum = sum(number.red)
            print(f"  第{i}注: 红球 {number.red} (和值: {red_sum}), 蓝球 {number.blue}")
            
    except Exception as e:
        print(f"特殊策略测试失败: {e}")

def test_generator_factory():
    """测试生成器工厂"""
    print("\n=== 测试生成器工厂 ===")
    
    from core.generators.factory import get_generator_factory
    
    factory = get_generator_factory()
    
    # 获取可用生成器
    available_generators = factory.get_available_generators()
    print(f"可用生成器: {available_generators}")
    
    # 获取生成器信息
    for gen_type in available_generators:
        info = factory.get_generator_info(gen_type)
        print(f"  {gen_type}: {info}")

def main():
    """主函数"""
    print("彩票号码生成和验证功能测试")
    print("=" * 50)
    
    try:
        test_random_generator()
        test_smart_generator()
        test_number_validation()
        test_special_generation_strategies()
        test_generator_factory()
        
        print("\n" + "=" * 50)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 