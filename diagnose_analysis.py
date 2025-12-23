#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据分析诊断工具
用于检查数据分析功能是否正常工作
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主诊断函数"""
    print("=" * 80)
    print(" " * 25 + "数据分析诊断工具")
    print("=" * 80)
    print()
    
    # 1. 检查模块导入
    print("1. 检查模块导入...")
    try:
        from src.core.data_manager import LotteryDataManager
        from src.core.analyzers.dlt_analyzer import DLTAnalyzer
        from src.core.ssq_analyzer import SSQAnalyzer
        from src.core.analyzers import FrequencyAnalyzer, PatternAnalyzer
        import pandas as pd
        print("   ✅ 所有模块导入成功")
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return
    print()
    
    # 2. 检查数据文件
    print("2. 检查数据文件...")
    import os
    data_files = {
        'ssq': 'data/ssq_history.json',
        'dlt': 'data/dlt_history.json'
    }
    
    for lottery_type, file_path in data_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {lottery_type.upper()}: {file_path} ({file_size:,} 字节)")
        else:
            print(f"   ⚠️ {lottery_type.upper()}: {file_path} 不存在")
    print()
    
    # 3. 测试数据管理器
    print("3. 测试数据管理器...")
    try:
        data_manager = LotteryDataManager('data')
        print("   ✅ 数据管理器初始化成功")
    except Exception as e:
        print(f"   ❌ 数据管理器初始化失败: {e}")
        return
    print()
    
    # 4. 测试加载数据
    print("4. 测试加载数据...")
    for lottery_type in ['ssq', 'dlt']:
        try:
            data = data_manager.get_history_data(lottery_type, periods=10)
            if data.empty:
                print(f"   ⚠️ {lottery_type.upper()}: 数据为空")
            else:
                print(f"   ✅ {lottery_type.upper()}: 成功加载 {len(data)} 条数据")
                print(f"      列名: {', '.join(data.columns[:5])}...")
        except Exception as e:
            print(f"   ❌ {lottery_type.upper()}: 加载失败 - {e}")
    print()
    
    # 5. 测试大乐透分析
    print("5. 测试大乐透分析...")
    try:
        dlt_data = data_manager.get_history_data('dlt', periods=50)
        if not dlt_data.empty:
            # 准备数据
            def _ensure_int_list(value):
                if isinstance(value, list):
                    return [int(x) for x in value]
                elif isinstance(value, str):
                    return [int(x.strip()) for x in value.split(',')]
                else:
                    return []
            
            records = []
            for _, row in dlt_data.head(20).iterrows():
                front_list = _ensure_int_list(row.get('front_numbers'))
                back_list = _ensure_int_list(row.get('back_numbers'))
                
                if len(front_list) >= 5 and len(back_list) >= 2:
                    records.append({
                        'front_numbers': front_list,
                        'back_numbers': back_list
                    })
            
            if records:
                analyzer = DLTAnalyzer()
                
                # 测试频率分析
                try:
                    result = analyzer.analyze_frequency(records, periods=len(records))
                    print(f"   ✅ 频率分析: 成功 (分析了 {result.get('periods')} 期)")
                except Exception as e:
                    print(f"   ❌ 频率分析: 失败 - {e}")
                
                # 测试热冷号分析
                try:
                    result = analyzer.analyze_hot_cold_numbers(records)
                    print(f"   ✅ 热冷号分析: 成功")
                except Exception as e:
                    print(f"   ❌ 热冷号分析: 失败 - {e}")
                
                # 测试走势分析
                try:
                    result = analyzer.analyze_trends(records)
                    print(f"   ✅ 走势分析: 成功")
                except Exception as e:
                    print(f"   ❌ 走势分析: 失败 - {e}")
                
                # 测试组合分析
                try:
                    result = analyzer.analyze_combinations(records)
                    print(f"   ✅ 组合分析: 成功")
                except Exception as e:
                    print(f"   ❌ 组合分析: 失败 - {e}")
                
                # 测试智能生成
                try:
                    result = analyzer.generate_smart_numbers(records, count=3)
                    print(f"   ✅ 智能生成: 成功 (生成了 {len(result)} 组号码)")
                except Exception as e:
                    print(f"   ❌ 智能生成: 失败 - {e}")
            else:
                print("   ⚠️ 无有效数据进行分析")
        else:
            print("   ⚠️ 大乐透数据为空")
    except Exception as e:
        print(f"   ❌ 大乐透分析失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 6. 测试双色球分析
    print("6. 测试双色球分析...")
    try:
        ssq_data = data_manager.get_history_data('ssq', periods=50)
        if not ssq_data.empty:
            # 准备数据
            def _ensure_int_list(value):
                if isinstance(value, list):
                    return [int(x) for x in value]
                elif isinstance(value, str):
                    return [int(x.strip()) for x in value.split(',')]
                else:
                    return []
            
            records = []
            for _, row in ssq_data.head(20).iterrows():
                red_list = _ensure_int_list(row.get('red_numbers'))
                blue_val = row.get('blue_number')
                
                if isinstance(blue_val, list):
                    blue_str = str(blue_val[0])
                else:
                    blue_str = str(blue_val)
                
                if len(red_list) >= 6:
                    records.append({
                        'red': ','.join(str(x) for x in red_list),
                        'blue': blue_str
                    })
            
            if records:
                analyzer = SSQAnalyzer()
                
                # 测试频率分析
                try:
                    result = analyzer.analyze_frequency(records)
                    print(f"   ✅ 频率分析: 成功")
                except Exception as e:
                    print(f"   ❌ 频率分析: 失败 - {e}")
                
                # 测试走势分析
                try:
                    result = analyzer.analyze_trends(records)
                    print(f"   ✅ 走势分析: 成功")
                except Exception as e:
                    print(f"   ❌ 走势分析: 失败 - {e}")
            else:
                print("   ⚠️ 无有效数据进行分析")
        else:
            print("   ⚠️ 双色球数据为空")
    except Exception as e:
        print(f"   ❌ 双色球分析失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 7. 测试 FrequencyAnalyzer
    print("7. 测试 FrequencyAnalyzer...")
    try:
        dlt_data = data_manager.get_history_data('dlt', periods=50)
        if not dlt_data.empty:
            analyzer = FrequencyAnalyzer('dlt')
            result = analyzer.analyze(dlt_data)
            print(f"   ✅ FrequencyAnalyzer: 成功")
        else:
            print("   ⚠️ 数据为空")
    except Exception as e:
        print(f"   ❌ FrequencyAnalyzer: 失败 - {e}")
    print()
    
    # 8. 测试 PatternAnalyzer
    print("8. 测试 PatternAnalyzer...")
    try:
        dlt_data = data_manager.get_history_data('dlt', periods=50)
        if not dlt_data.empty:
            analyzer = PatternAnalyzer('dlt')
            result = analyzer.analyze(dlt_data)
            print(f"   ✅ PatternAnalyzer: 成功")
        else:
            print("   ⚠️ 数据为空")
    except Exception as e:
        print(f"   ❌ PatternAnalyzer: 失败 - {e}")
    print()
    
    print("=" * 80)
    print(" " * 30 + "诊断完成")
    print("=" * 80)
    print()
    print("如果所有测试都通过，说明数据分析功能正常。")
    print("如果有测试失败，请查看上面的错误信息。")
    print()

if __name__ == "__main__":
    main()

