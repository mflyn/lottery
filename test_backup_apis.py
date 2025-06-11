#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试备选API功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.data_manager import LotteryDataManager
from core.logging_config import setup_logging

def test_backup_apis():
    """测试备选API功能"""
    # 设置日志
    setup_logging()
    
    # 创建数据管理器
    data_manager = LotteryDataManager()
    
    print("=" * 60)
    print("测试大乐透备选API功能")
    print("=" * 60)
    
    # 测试大乐透数据获取
    print("\n1. 测试大乐透数据获取...")
    try:
        result = data_manager._fetch_online_data_as_list('dlt', page_size=5)
        if result:
            print(f"✅ 成功获取到 {len(result)} 条大乐透数据")
            print("前3条数据示例:")
            for i, item in enumerate(result[:3]):
                print(f"  {i+1}. 期号: {item.get('draw_num')}, 日期: {item.get('draw_date')}")
                print(f"     前区: {item.get('front_numbers')}, 后区: {item.get('back_numbers')}")
        else:
            print("❌ 未能获取到大乐透数据")
    except Exception as e:
        print(f"❌ 获取大乐透数据时出错: {e}")
    
    print("\n2. 测试双色球数据获取...")
    try:
        result = data_manager._fetch_online_data_as_list('ssq', page_size=5)
        if result:
            print(f"✅ 成功获取到 {len(result)} 条双色球数据")
            print("前3条数据示例:")
            for i, item in enumerate(result[:3]):
                print(f"  {i+1}. 期号: {item.get('draw_num')}, 日期: {item.get('draw_date')}")
                print(f"     红球: {item.get('red_numbers')}, 蓝球: {item.get('blue_number')}")
        else:
            print("❌ 未能获取到双色球数据")
    except Exception as e:
        print(f"❌ 获取双色球数据时出错: {e}")
    
    print("\n3. 测试完整数据更新流程...")
    try:
        # 测试大乐透更新
        success = data_manager.update_data('dlt')
        if success:
            print("✅ 大乐透数据更新成功")
            # 获取最新数据验证
            df = data_manager.get_history_data('dlt', periods=3)
            if not df.empty:
                print(f"   本地数据验证: 共 {len(df)} 条记录")
                print(f"   最新期号: {df.iloc[0]['draw_num']}")
            else:
                print("   ⚠️ 本地数据为空")
        else:
            print("❌ 大乐透数据更新失败")
    except Exception as e:
        print(f"❌ 大乐透数据更新时出错: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_backup_apis() 