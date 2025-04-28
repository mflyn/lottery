#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试双色球API数据获取功能
"""

from ssq_api_fetcher import SSQApiFetcher

def main():
    """主函数"""
    print("=" * 50)
    print("测试双色球API数据获取功能")
    print("=" * 50)
    
    fetcher = SSQApiFetcher()
    
    # 测试获取最新一期开奖数据
    print("\n1. 获取最新一期开奖数据:")
    latest = fetcher.fetch_latest()
    if latest:
        print(f"期号: {latest['term']}")
        print(f"日期: {latest['date']}")
        print(f"红球号码: {latest['red_numbers']}")
        print(f"蓝球号码: {latest['blue_numbers']}")
    else:
        print("获取最新一期开奖数据失败")
    
    # 测试获取特定期号的开奖数据
    term = input("\n2. 请输入要查询的期号(如23001): ")
    print(f"获取期号 {term} 的开奖数据:")
    result = fetcher.fetch_by_term(term)
    if result:
        print(f"日期: {result['date']}")
        print(f"红球号码: {result['red_numbers']}")
        print(f"蓝球号码: {result['blue_numbers']}")
    else:
        print(f"未找到期号 {term} 的开奖数据")

if __name__ == "__main__":
    main()
