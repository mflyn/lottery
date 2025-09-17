#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def rank_candidates():
    """Ranks 10 generated candidates based on statistical profile."""
    candidates = [
        {'red': [4, 7, 11, 18, 24, 30], 'blue': 12},
        {'red': [7, 13, 16, 17, 21, 25], 'blue': 16},
        {'red': [1, 4, 8, 9, 12, 15], 'blue': 4},
        {'red': [15, 17, 18, 20, 21, 22], 'blue': 8},
        {'red': [5, 14, 16, 17, 23, 33], 'blue': 11},
        {'red': [3, 6, 8, 18, 26, 33], 'blue': 16},
        {'red': [5, 9, 11, 20, 22, 25], 'blue': 15},
        {'red': [5, 6, 8, 9, 13, 24], 'blue': 2},
        {'red': [2, 4, 9, 11, 24, 33], 'blue': 8},
        {'red': [16, 17, 23, 26, 27, 28], 'blue': 11},
    ]

    best_score = -1
    best_candidate = None
    best_analysis = ""

    hot_blues = {5, 14, 15, 16}

    for i, cand in enumerate(candidates, 1):
        score = 0
        analysis = []
        reds = sorted(cand['red'])
        blue = cand['blue']

        # 1. Sum Score
        s = sum(reds)
        if 80 <= s <= 120:
            score += 2
            analysis.append(f"和值({s})得2分")
        
        # 2. Odd/Even Score
        odds = sum(1 for n in reds if n % 2 != 0)
        oe_ratio = f"{odds}:{6-odds}"
        if oe_ratio == '3:3':
            score += 2
            analysis.append(f"奇偶比({oe_ratio})得2分")
        elif oe_ratio in ['4:2', '2:4']:
            score += 1
            analysis.append(f"奇偶比({oe_ratio})得1分")

        # 3. Big/Small Score
        bigs = sum(1 for n in reds if n >= 17)
        bs_ratio = f"{bigs}:{6-bigs}"
        if bs_ratio == '3:3':
            score += 2
            analysis.append(f"大小比({bs_ratio})得2分")
        elif bs_ratio in ['4:2', '2:4']:
            score += 1
            analysis.append(f"大小比({bs_ratio})得1分")

        # 4. Consecutive Score
        has_consecutive = any(reds[j+1] - reds[j] == 1 for j in range(len(reds)-1))
        if has_consecutive:
            score += 2
            analysis.append("包含连号得2分")

        # 5. Zone Score
        z1 = sum(1 for n in reds if 1 <= n <= 11)
        z2 = sum(1 for n in reds if 12 <= n <= 22)
        z3 = sum(1 for n in reds if 23 <= n <= 33)
        zone_dist = f"{z1}:{z2}:{z3}"
        if zone_dist == '2:2:2':
            score += 2
            analysis.append(f"区间比({zone_dist})得2分")
        elif z1 > 0 and z2 > 0 and z3 > 0:
            score += 1
            analysis.append(f"区间比({zone_dist})无断区得1分")

        # 6. Blue Ball Score
        if blue in hot_blues:
            score += 3
            analysis.append(f"命中热号蓝球({blue})得3分")

        if score > best_score:
            best_score = score
            best_candidate = cand
            best_analysis = ", ".join(analysis)

    print("\n--- 最终择优结果 ---")
    if best_candidate:
        red_str = ', '.join(map(str, sorted(best_candidate['red'])))
        blue_str = best_candidate['blue']
        print(f"最佳号码: 红球 [{red_str}] | 蓝球 [{blue_str}]")
        print(f"综合得分: {best_score}")
        print(f"得分依据: {best_analysis}")
    else:
        print("未能选出最佳号码。")

if __name__ == "__main__":
    rank_candidates()
