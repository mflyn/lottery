#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试"最高评分（整注）"策略对大乐透的支持
"""

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_dlt_search_script():
    """测试大乐透搜索脚本"""
    print("=" * 70)
    print(" " * 15 + "测试大乐透搜索脚本")
    print("=" * 70)
    print()
    
    try:
        from scripts.find_top_dlt import find_top_dlt
        print("✅ 成功导入 find_top_dlt")
        
        # 测试搜索（使用较小的参数以加快速度）
        print("\n正在搜索大乐透最高评分号码（periods=50, pool_size=15, top_k=3）...")
        results = find_top_dlt(top_k=3, periods=50, pool_size=15, out_path=None)
        
        if results:
            print(f"\n✅ 搜索成功！找到 {len(results)} 注号码")
            print(f"   最高评分: {results[0]['total_score']}")
            print("\n前3注号码:")
            for i, item in enumerate(results[:3], 1):
                front = ' '.join(f"{n:02d}" for n in item['front_numbers'])
                back = ' '.join(f"{n:02d}" for n in item['back_numbers'])
                print(f"   {i}. 前区: {front} | 后区: {back} | 评分: {item['total_score']}")
        else:
            print("⚠️  未找到符合条件的号码")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generation_frame_dlt_support():
    """测试生成页面对大乐透的支持"""
    print("\n" + "=" * 70)
    print(" " * 15 + "测试生成页面大乐透支持")
    print("=" * 70)
    print()
    
    try:
        from src.gui.generation_frame import GenerationFrame
        print("✅ 成功导入 GenerationFrame")
        
        # 检查方法是否存在
        import inspect
        source = inspect.getsource(GenerationFrame._background_top_scored_generation)
        
        if "lottery_type == 'dlt'" in source:
            print("✅ 方法中包含大乐透支持代码")
        else:
            print("❌ 方法中未找到大乐透支持代码")
            return False
        
        if "find_top_dlt" in source:
            print("✅ 方法中调用了 find_top_dlt")
        else:
            print("❌ 方法中未调用 find_top_dlt")
            return False
        
        print("\n✅ 生成页面已支持大乐透")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print(" " * 10 + "最高评分策略 - 大乐透支持测试")
    print("=" * 70)
    print()
    
    # 测试1: 大乐透搜索脚本
    test1_passed = test_dlt_search_script()
    
    # 测试2: 生成页面支持
    test2_passed = test_generation_frame_dlt_support()
    
    # 总结
    print("\n" + "=" * 70)
    print(" " * 20 + "测试总结")
    print("=" * 70)
    print()
    print(f"  测试1 - 大乐透搜索脚本: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"  测试2 - 生成页面支持: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print()
    
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！最高评分策略现已支持大乐透")
        print()
        print("使用方法:")
        print("  1. 启动GUI: python main.py")
        print("  2. 切换到'号码推荐'标签页")
        print("  3. 选择彩票类型: 大乐透")
        print("  4. 选择策略: 最高评分（整注）")
        print("  5. 设置生成注数和搜索参数")
        print("  6. 点击'生成号码'")
        print()
    else:
        print("❌ 部分测试失败，请检查错误信息")
    
    print("=" * 70)


if __name__ == '__main__':
    main()

