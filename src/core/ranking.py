
from typing import List, Dict, Optional
from collections import Counter
from .models import SSQNumber, DLTNumber

def rank_and_select_best(candidates: List[SSQNumber]) -> Optional[SSQNumber]:
    """Ranks a list of SSQNumber candidates and returns the one with the highest score."""
    best_score = -1
    best_candidate = None

    # 根据最近50期分析, 热门蓝球为 5, 14, 15, 16
    hot_blues = {5, 14, 15, 16}

    for candidate in candidates:
        score = 0
        reds = sorted(candidate.red)
        blue = candidate.blue

        # 1. 和值评分
        s = sum(reds)
        if 80 <= s <= 120:
            score += 2
        
        # 2. 奇偶比评分
        odds = sum(1 for n in reds if n % 2 != 0)
        oe_ratio = f"{odds}:{6-odds}"
        if oe_ratio == '3:3':
            score += 2
        elif oe_ratio in ['4:2', '2:4']:
            score += 1

        # 3. 大小比评分
        bigs = sum(1 for n in reds if n >= 17)
        bs_ratio = f"{bigs}:{6-bigs}"
        if bs_ratio == '3:3':
            score += 2
        elif bs_ratio in ['4:2', '2:4']:
            score += 1

        # 4. 连号评分
        has_consecutive = any(reds[j+1] - reds[j] == 1 for j in range(len(reds)-1))
        if has_consecutive:
            score += 1 # 连号在SSQ中是加分项, 但不如其他指标关键

        # 5. 区间比评分
        z1 = sum(1 for n in reds if 1 <= n <= 11)
        z2 = sum(1 for n in reds if 12 <= n <= 22)
        z3 = sum(1 for n in reds if 23 <= n <= 33)
        if z1 > 0 and z2 > 0 and z3 > 0: # 无断区
            if f"{z1}:{z2}:{z3}" == '2:2:2':
                score += 2 # 完美区间比
            else:
                score += 1 # 仅无断区

        # 6. 蓝球评分
        if blue in hot_blues:
            score += 3

        candidate.score = score

        if score > best_score:
            best_score = score
            best_candidate = candidate

    return best_candidate

def rank_and_select_best_dlt(candidates: List[DLTNumber]) -> Optional[DLTNumber]:
    """Ranks a list of DLTNumber candidates and returns the one with the highest score."""
    best_score = -1
    best_candidate = None

    # 基于最近30期分析的热号
    hot_backs = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12}

    for candidate in candidates:
        score = 0
        fronts = sorted(candidate.front)
        backs = sorted(candidate.back)

        # --- 前区评分 ---
        # 1. 和值
        front_sum = sum(fronts)
        if 70 <= front_sum <= 110:
            score += 2

        # 2. 奇偶比
        front_odds = sum(1 for n in fronts if n % 2 != 0)
        front_oe_ratio = f"{front_odds}:{5-front_odds}"
        if front_oe_ratio in ['2:3', '3:2']:
            score += 2
        elif front_oe_ratio in ['1:4', '4:1']:
            score += 1

        # 3. 大小比
        front_bigs = sum(1 for n in fronts if n >= 18)
        front_bs_ratio = f"{front_bigs}:{5-front_bigs}"
        if front_bs_ratio in ['2:3', '3:2']:
            score += 2

        # 4. 区间比
        z1 = sum(1 for n in fronts if 1 <= n <= 12)
        z2 = sum(1 for n in fronts if 13 <= n <= 24)
        z3 = sum(1 for n in fronts if 25 <= n <= 35)
        if z1 > 0 and z2 > 0 and z3 > 0: # 无断区
            if f"{z1}:{z2}:{z3}" == '2:1:2':
                score += 2 # 最佳区间比
            else:
                score += 1 # 仅无断区

        # --- 后区评分 ---
        # 5. 奇偶比
        back_odds = sum(1 for n in backs if n % 2 != 0)
        if f"{back_odds}:{2-back_odds}" == '1:1':
            score += 2

        # 6. 跨度
        if len(backs) == 2 and (backs[1] - backs[0]) in [1, 2, 3]:
            score += 1

        # 7. 热号
        score += sum(1 for n in backs if n in hot_backs) # 命中一个热号+1分

        candidate.score = score

        if score > best_score:
            best_score = score
            best_candidate = candidate

    return best_candidate
