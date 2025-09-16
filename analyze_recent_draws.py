#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
from pathlib import Path
import pandas as pd
from collections import Counter
import numpy as np

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def analyze_recent_draws():
    """Analyzes the last 30 draws for statistical patterns."""
    try:
        # --- 1. 加载数据 ---
        data_file = Path(__file__).parent / "data" / "ssq_history.json"
        if not data_file.exists():
            print(f"错误: 数据文件 {data_file} 不存在。")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            history = json.load(f)['data']
        
        df = pd.DataFrame(history)
        df['draw_date'] = pd.to_datetime(df['draw_date'])
        df = df.sort_values('draw_date', ascending=False).reset_index(drop=True)

        # --- 2. 定位最近30期 ---
        lookback_period = 30
        if len(df) < lookback_period:
            print(f"错误: 数据不足{lookback_period}期。")
            return
        
        recent_draws = df.head(lookback_period)
        start_date = recent_draws.iloc[-1]['draw_date'].date()
        end_date = recent_draws.iloc[0]['draw_date'].date()

        # --- 3. 逐期分析并汇总 ---
        sums = []
        odd_even_ratios = []
        big_small_ratios = []
        consecutive_counts = 0
        zone_distributions = []
        spans = []
        blue_balls = []

        for index, row in recent_draws.iterrows():
            reds = sorted(row['red_numbers'])
            
            # 和值
            sums.append(sum(reds))
            
            # 奇偶比
            odds = sum(1 for n in reds if n % 2 != 0)
            odd_even_ratios.append(f"{odds}: {6-odds}")
            
            # 大小比
            bigs = sum(1 for n in reds if n >= 17)
            big_small_ratios.append(f"{bigs}: {6-bigs}")
            
            # 连号
            has_consecutive = any(reds[i+1] - reds[i] == 1 for i in range(len(reds)-1))
            if has_consecutive:
                consecutive_counts += 1
            
            # 区间分布 (1-11, 12-22, 23-33)
            z1 = sum(1 for n in reds if 1 <= n <= 11)
            z2 = sum(1 for n in reds if 12 <= n <= 22)
            z3 = sum(1 for n in reds if 23 <= n <= 33)
            zone_distributions.append(f"{z1}:{z2}:{z3}")
            
            # 跨度
            spans.append(max(reds) - min(reds))

            # 蓝球
            blue_balls.append(row['blue_number'])

        # --- 4. 生成报告 ---
        print(f"\n--- 最近30期双色球开奖结果数学统计分析 --- ({start_date} 到 {end_date}) ---")
        
        print("\n一、红球分析")
        print("----------------------------------------")
        
        # 和值分析
        avg_sum = np.mean(sums)
        in_range = sum(1 for s in sums if 80 <= s <= 120)
        print("1. 和值 (Sum):")
        print(f"   - 平均和值: {avg_sum:.1f} (理论中心: 102)")
        print(f"   - 和值范围: {min(sums)} - {max(sums)}")
        print(f"   - {in_range}/{lookback_period} ({in_range/lookback_period:.1%}) 的期次和值落在 80-120 的核心区间。")

        # 比例分析
        print("\n2. 核心比例:")
        print("   - 奇偶比分布:")
        for ratio, count in Counter(odd_even_ratios).most_common():
            print(f"     - {ratio}: {count} 次")
        print("   - 大小比分布:")
        for ratio, count in Counter(big_small_ratios).most_common():
            print(f"     - {ratio}: {count} 次")

        # 形态分析
        print("\n3. 形态特征:")
        print(f"   - 连号: 在30期内共出现 {consecutive_counts} 次，出现率: {consecutive_counts/lookback_period:.1%}")
        print(f"   - 平均跨度: {np.mean(spans):.1f}")
        print("   - 区间分布 (格式 1-11区:12-22区:23-33区):")
        for dist, count in Counter(zone_distributions).most_common(5):
            print(f"     - {dist}: {count} 次")

        print("\n二、蓝球分析")
        print("----------------------------------------")
        blue_counts = Counter(blue_balls)
        hot_blues = blue_counts.most_common()
        all_blue_nums = set(range(1, 17))
        cold_blues = all_blue_nums - set(blue_balls)
        print("   - 热号 (出现次数最多):")
        for num, count in hot_blues:
            if count >= 3:
                 print(f"     - 号码 {num}: {count} 次")
        print("   - 温号 (出现1-2次):")
        warm_blues = [f"{num}({count}次)" for num, count in hot_blues if count in [1, 2]]
        print(f"     - {', '.join(warm_blues)}")
        print("   - 冷号 (30期内未出现):")
        print(f"     - {sorted(list(cold_blues))}")

    except Exception as e:
        print(f"执行分析过程中发生错误: {e}")

if __name__ == "__main__":
    analyze_recent_draws()
