#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试详细分析功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator

def test_ssq_detail_analysis():
    """测试双色球详细分析"""
    print("=" * 80)
    print("测试双色球详细分析")
    print("=" * 80)
    
    # 创建评价器
    evaluator = SSQNumberEvaluator()
    
    # 测试号码
    red_numbers = [3, 9, 16, 17, 24, 33]
    blue_number = 15
    
    print(f"\n待评价号码: 红球 {red_numbers} | 蓝球 {blue_number}")
    print("\n正在评价...")
    
    # 评价
    result = evaluator.evaluate(red_numbers, blue_number)
    
    # 检查结果结构
    print("\n✓ 评价完成")
    print(f"\n综合得分: {result['total_score']:.1f}/100")
    print(f"评级: {result['rating']}")
    
    # 检查各个分析部分
    print("\n【检查数据结构】")
    print("-" * 80)
    
    # 1. 频率分析
    print("\n1. 频率分析:")
    freq = result['frequency']
    print(f"   - 红球详情数量: {len(freq['red_details'])}")
    print(f"   - 蓝球详情: {'存在' if 'blue_detail' in freq else '缺失'}")
    if freq['red_details']:
        detail = freq['red_details'][0]
        print(f"   - 示例数据: 号码{detail['number']:02d}, 频率{detail['frequency']}, {detail['classification']}")
    
    # 2. 遗漏分析
    print("\n2. 遗漏分析:")
    missing = result['missing']
    print(f"   - 红球详情数量: {len(missing['red_details'])}")
    print(f"   - 蓝球详情: {'存在' if 'blue_detail' in missing else '缺失'}")
    if missing['red_details']:
        detail = missing['red_details'][0]
        print(f"   - 示例数据: 号码{detail['number']:02d}, 遗漏{detail['missing']}期, {detail['classification']}")
    
    # 3. 模式分析
    print("\n3. 模式分析:")
    pattern = result['pattern']
    print(f"   - 奇偶比: {pattern['odd_even']['ratio']}")
    print(f"   - 大小比: {pattern['big_small']['ratio']}")
    print(f"   - 区间分布: {pattern['zone']['distribution']}")
    print(f"   - 连号: {pattern['consecutive']['count']}组")
    print(f"   - 和值: {pattern['sum']['value']}")
    print(f"   - 跨度: {pattern['span']['value']}")
    print(f"   - AC值: {pattern['ac_value']['value']}")
    
    # 4. 历史对比
    print("\n4. 历史对比:")
    historical = result['historical']
    print(f"   - 完全匹配: {'是' if historical['exact_match'] else '否'}")
    print(f"   - 红球最大匹配: {historical['max_red_match']}个")
    print(f"   - 红球平均匹配: {historical['avg_red_match']:.2f}个")
    print(f"   - 蓝球历史出现: {historical['blue_appearance']}次")
    
    # 5. 专家建议
    print("\n5. 专家建议:")
    suggestions = result['suggestions']
    print(f"   - 建议数量: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("✓ 双色球详细分析测试通过")
    print("=" * 80)
    
    return result

def test_dlt_detail_analysis():
    """测试大乐透详细分析"""
    print("\n" + "=" * 80)
    print("测试大乐透详细分析")
    print("=" * 80)
    
    # 创建评价器
    evaluator = DLTNumberEvaluator()
    
    # 测试号码
    front_numbers = [1, 5, 12, 23, 35]
    back_numbers = [3, 11]
    
    print(f"\n待评价号码: 前区 {front_numbers} | 后区 {back_numbers}")
    print("\n正在评价...")
    
    # 评价
    result = evaluator.evaluate(front_numbers, back_numbers)
    
    # 检查结果结构
    print("\n✓ 评价完成")
    print(f"\n综合得分: {result['total_score']:.1f}/100")
    print(f"评级: {result['rating']}")
    
    # 检查各个分析部分
    print("\n【检查数据结构】")
    print("-" * 80)
    
    # 1. 频率分析
    print("\n1. 频率分析:")
    freq = result['frequency']
    print(f"   - 前区详情数量: {len(freq['front_details'])}")
    print(f"   - 后区详情数量: {len(freq['back_details'])}")
    if freq['front_details']:
        detail = freq['front_details'][0]
        print(f"   - 示例数据: 号码{detail['number']:02d}, 频率{detail['frequency']}, {detail['classification']}")
    
    # 2. 遗漏分析
    print("\n2. 遗漏分析:")
    missing = result['missing']
    print(f"   - 前区详情数量: {len(missing['front_details'])}")
    print(f"   - 后区详情数量: {len(missing['back_details'])}")
    if missing['front_details']:
        detail = missing['front_details'][0]
        print(f"   - 示例数据: 号码{detail['number']:02d}, 遗漏{detail['missing']}期, {detail['classification']}")
    
    # 3. 模式分析
    print("\n3. 模式分析:")
    pattern = result['pattern']
    front = pattern['front']
    back = pattern['back']
    print(f"   【前区】")
    print(f"   - 奇偶比: {front['odd_even']['ratio']}")
    print(f"   - 大小比: {front['big_small']['ratio']}")
    print(f"   - 区间分布: {front['zone']['distribution']}")
    print(f"   - 连号: {front['consecutive']['count']}组")
    print(f"   - 和值: {front['sum']['value']}")
    print(f"   - 跨度: {front['span']['value']}")
    print(f"   - AC值: {front['ac_value']['value']}")
    print(f"   【后区】")
    print(f"   - 奇偶比: {back['odd_even']['ratio']}")
    
    # 4. 历史对比
    print("\n4. 历史对比:")
    historical = result['historical']
    print(f"   - 完全匹配: {'是' if historical['exact_match'] else '否'}")
    print(f"   - 前区最大匹配: {historical['max_front_match']}个")
    print(f"   - 后区最大匹配: {historical['max_back_match']}个")
    print(f"   - 总最大匹配: {historical['max_total_match']}个")
    print(f"   - 前区平均匹配: {historical['avg_front_match']:.2f}个")
    print(f"   - 后区平均匹配: {historical['avg_back_match']:.2f}个")
    
    # 5. 专家建议
    print("\n5. 专家建议:")
    suggestions = result['suggestions']
    print(f"   - 建议数量: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("✓ 大乐透详细分析测试通过")
    print("=" * 80)
    
    return result

def test_format_methods():
    """测试格式化方法"""
    print("\n" + "=" * 80)
    print("测试格式化方法")
    print("=" * 80)
    
    # 导入GUI框架
    try:
        from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
        print("\n✓ NumberEvaluationFrame 导入成功")
        
        # 检查格式化方法是否存在
        methods = [
            '_format_frequency_analysis',
            '_format_missing_analysis',
            '_format_pattern_analysis',
            '_format_historical_analysis',
            '_format_suggestions'
        ]
        
        print("\n【检查格式化方法】")
        for method in methods:
            if hasattr(NumberEvaluationFrame, method):
                print(f"   ✓ {method} 存在")
            else:
                print(f"   ✗ {method} 缺失")
        
        print("\n" + "=" * 80)
        print("✓ 格式化方法检查完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("详细分析功能测试")
    print("=" * 80)
    
    try:
        # 测试双色球
        ssq_result = test_ssq_detail_analysis()
        
        # 测试大乐透
        dlt_result = test_dlt_detail_analysis()
        
        # 测试格式化方法
        test_format_methods()
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)
        
        # 询问是否查看详细输出
        print("\n是否查看格式化后的详细分析？(y/n): ", end='')
        choice = input().strip().lower()
        
        if choice == 'y':
            from src.gui.frames.number_evaluation_frame import NumberEvaluationFrame
            
            # 创建一个临时的格式化器（不需要完整的GUI）
            class TempFormatter:
                def __init__(self):
                    pass
                
                def format_all(self, result, lottery_type):
                    """格式化所有分析"""
                    # 使用NumberEvaluationFrame的静态方法
                    frame = NumberEvaluationFrame.__new__(NumberEvaluationFrame)
                    
                    print("\n" + "=" * 80)
                    print("【频率分析】")
                    print("=" * 80)
                    print(frame._format_frequency_analysis(result['frequency'], lottery_type))
                    
                    print("\n" + "=" * 80)
                    print("【遗漏分析】")
                    print("=" * 80)
                    print(frame._format_missing_analysis(result['missing'], lottery_type))
                    
                    print("\n" + "=" * 80)
                    print("【模式分析】")
                    print("=" * 80)
                    print(frame._format_pattern_analysis(result['pattern'], lottery_type))
                    
                    print("\n" + "=" * 80)
                    print("【历史对比】")
                    print("=" * 80)
                    print(frame._format_historical_analysis(result['historical']))
                    
                    print("\n" + "=" * 80)
                    print("【专家建议】")
                    print("=" * 80)
                    print(frame._format_suggestions(result['suggestions']))
            
            formatter = TempFormatter()
            
            print("\n" + "=" * 80)
            print("双色球详细分析输出")
            print("=" * 80)
            formatter.format_all(ssq_result, 'ssq')
            
            print("\n" + "=" * 80)
            print("大乐透详细分析输出")
            print("=" * 80)
            formatter.format_all(dlt_result, 'dlt')
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

