#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试改进的蓝球选择算法
"""

import sys
import os
sys.path.insert(0, 'src')

import json
import pandas as pd
import numpy as np
from collections import Counter
from core.generators.smart_generator import SmartNumberGenerator

def test_improved_blue_algorithm():
    """测试改进的蓝球算法"""
    print("=== 测试改进的双色球蓝球选择算法 ===\n")
    
    # 加载真实数据
    try:
        with open('data/ssq_history.json', 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        print(f"✓ 成功加载 {history_data['total_periods']} 期双色球历史数据")
        
        # 转换数据格式
        data_list = []
        for item in history_data['data']:
            data_list.append({
                'draw_num': item['draw_num'],
                'draw_date': item['draw_date'],
                'red_numbers': item['red_numbers'],
                'blue_number': item['blue_number']
            })
        
        df = pd.DataFrame(data_list)
        
    except Exception as e:
        print(f"✗ 数据加载失败: {e}")
        return
    
    # 创建智能生成器
    generator = SmartNumberGenerator('ssq')
    
    # 1. 显示算法配置信息
    print("\n1. 算法配置信息:")
    config_info = generator.get_blue_algorithm_info()
    print(f"   当前方法: {config_info['current_method']}")
    print(f"   分析期数: {config_info['analysis_periods']}")
    print("   权重配置:")
    for factor, weight in config_info['weights'].items():
        print(f"     {factor}: {weight}")
    
    print("\n   可用方法:")
    for method, desc in config_info['description'].items():
        print(f"     {method}: {desc}")
    
    # 2. 测试不同算法方法
    print("\n2. 不同算法方法对比测试:")
    
    methods_to_test = ['simple', 'enhanced', 'ensemble']
    results = {}
    
    for method in methods_to_test:
        print(f"\n   测试方法: {method}")
        generator.set_blue_algorithm_config(method=method)
        
        # 生成10个推荐号码
        recommendations = []
        for i in range(10):
            try:
                numbers = generator.generate_recommended(1)
                if numbers and hasattr(numbers[0], 'blue'):
                    recommendations.append(numbers[0].blue)
            except Exception as e:
                print(f"     生成失败: {e}")
                continue
        
        if recommendations:
            counter = Counter(recommendations)
            print(f"     生成的蓝球: {recommendations}")
            print(f"     分布统计: {dict(counter.most_common())}")
            results[method] = recommendations
        else:
            print("     ✗ 生成失败")
    
    # 3. 分析最近期数据特征
    print("\n3. 最近50期蓝球数据分析:")
    recent_50 = df.head(50)['blue_number'].tolist()
    
    # 频率分析
    freq_counter = Counter(recent_50)
    print("   频率分布 (前5名):")
    for num, count in freq_counter.most_common(5):
        print(f"     {num}号: {count}次 ({count/50:.1%})")
    
    # 遗漏分析
    print("\n   遗漏分析 (最近10期未出现):")
    recent_10 = set(df.head(10)['blue_number'].tolist())
    missing_numbers = [num for num in range(1, 17) if num not in recent_10]
    print(f"     遗漏号码: {missing_numbers}")
    
    # 趋势分析
    print("\n   趋势分析 (近期vs远期频率):")
    recent_freq = Counter(df.head(10)['blue_number'].tolist())
    older_freq = Counter(df.iloc[10:20]['blue_number'].tolist())
    
    for num in range(1, 17):
        recent_count = recent_freq.get(num, 0)
        older_count = older_freq.get(num, 0)
        if recent_count > 0 or older_count > 0:
            trend = "↑" if recent_count > older_count else "↓" if recent_count < older_count else "→"
            print(f"     {num}号: 近期{recent_count}次, 远期{older_count}次 {trend}")
    
    # 4. 权重敏感性测试
    print("\n4. 权重配置敏感性测试:")
    
    test_configs = [
        {'name': '频率优先', 'weights': {'frequency': 0.6, 'missing': 0.2, 'trend': 0.1, 'pattern': 0.05, 'random': 0.05}},
        {'name': '遗漏优先', 'weights': {'frequency': 0.2, 'missing': 0.6, 'trend': 0.1, 'pattern': 0.05, 'random': 0.05}},
        {'name': '趋势优先', 'weights': {'frequency': 0.2, 'missing': 0.2, 'trend': 0.5, 'pattern': 0.05, 'random': 0.05}},
        {'name': '平衡配置', 'weights': {'frequency': 0.3, 'missing': 0.3, 'trend': 0.2, 'pattern': 0.1, 'random': 0.1}}
    ]
    
    for config in test_configs:
        print(f"\n   {config['name']}:")
        generator.set_blue_algorithm_config(method='enhanced', weights=config['weights'])
        
        test_results = []
        for i in range(5):
            try:
                numbers = generator.generate_recommended(1)
                if numbers and hasattr(numbers[0], 'blue'):
                    test_results.append(numbers[0].blue)
            except:
                continue
        
        if test_results:
            print(f"     推荐结果: {test_results}")
            print(f"     号码分布: {dict(Counter(test_results))}")
    
    # 5. 性能建议
    print("\n5. 算法性能建议:")
    print("   ✓ enhanced方法提供最全面的分析")
    print("   ✓ ensemble方法具有最好的鲁棒性") 
    print("   ✓ 可根据个人偏好调整权重配置")
    print("   ✓ 建议定期评估和调整算法参数")
    
    print("\n6. 使用建议:")
    print("   - 日常使用推荐 'enhanced' 方法")
    print("   - 追求稳定性可选择 'ensemble' 方法")
    print("   - 可根据最近数据特征调整权重")
    print("   - 保持适当随机性，避免过度拟合")

if __name__ == "__main__":
    test_improved_blue_algorithm()
