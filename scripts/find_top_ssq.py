#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从所有双色球号码组合中（在可行范围内通过剪枝保证质量）找到评分最高的5组号码，排除历史中奖号码。
说明：
- 评分体系使用现有 SSQNumberEvaluator，一致性完全对齐
- 蓝球不影响总分（当前评分实现只与红球有关），脚本为每组红球选择一个“推荐蓝球”
- 为保证可运行性，使用启发式剪枝：先选取高质量红球池，再组合并筛选模式
- 若分数并列，将全部列出

用法：
    python scripts/find_top_ssq.py --top 5 --periods 100 --pool-size 18 --out docs/TOP_SSQ_NUMBERS.md
"""

import argparse
import itertools
import os
import sys
import time
from collections import Counter
from typing import List, Tuple, Dict, Any

import numpy as np

# 允许直接运行脚本时导入 src 包
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator


def calc_ac_value(nums: List[int]) -> int:
    s = sorted(nums)
    diffs = set()
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n):
            diffs.add(s[j] - s[i])
    return len(diffs) - (n - 1)


def passes_pattern_filters(reds: Tuple[int, ...]) -> bool:
    # 奇偶 2..4
    odd = sum(1 for n in reds if n % 2)
    if not (2 <= odd <= 4):
        return False
    # 大小 2..4 (大: >=18)
    big = sum(1 for n in reds if n >= 18)
    if not (2 <= big <= 4):
        return False
    # 区间至少覆盖2个区（1-11,12-22,23-33）
    z1 = sum(1 for n in reds if 1 <= n <= 11)
    z2 = sum(1 for n in reds if 12 <= n <= 22)
    z3 = sum(1 for n in reds if 23 <= n <= 33)
    if (z1 > 0) + (z2 > 0) + (z3 > 0) < 2:
        return False
    # 跨度 10..32
    span = max(reds) - min(reds)
    if not (10 <= span <= 32):
        return False
    # 和值 70..150
    s = sum(reds)
    if not (70 <= s <= 150):
        return False
    # AC 值 >= 4
    if calc_ac_value(list(reds)) < 4:
        return False
    return True


def build_history_exact_set(history_data: List[Dict[str, Any]]) -> set:
    exact = set()
    for draw in history_data:
        r = tuple(sorted(draw['red_numbers']))
        b = int(draw['blue_number'])
        exact.add((r, b))
    return exact


def choose_recommended_blue(blue_counter: Dict[int, int], blue_missing: Dict[int, int],
                            history_exact: set, reds: Tuple[int, ...]) -> int:
    # 蓝球评分：频率标准化 60% + 反遗漏 40%
    periods = sum(blue_counter.values())
    blue_theory = periods / 16 if periods else 0
    avg_missing = float(np.mean(list(blue_missing.values()))) if blue_missing else 1.0

    scores = []
    for b in range(1, 17):
        if ((reds, b)) in history_exact:
            # 尽量避免历史完全相同
            continue
        freq = blue_counter.get(b, 0)
        freq_score = (freq / blue_theory) if blue_theory > 0 else 0
        miss = blue_missing.get(b, 0)
        inv_missing = max(0.0, 1.0 - (miss / (avg_missing * 1.5 if avg_missing > 0 else 1.0)))
        s = 0.6 * freq_score + 0.4 * inv_missing
        scores.append((s, b))

    if not scores:
        return -1
    scores.sort(reverse=True)
    return scores[0][1]


def build_red_pool(history_data: List[Dict[str, Any]], periods: int, pool_size: int) -> List[int]:
    recent = history_data[:periods]
    red_counter = Counter()
    for d in recent:
        red_counter.update(d['red_numbers'])
    red_theory = periods * 6 / 33 if periods else 0

    # 缺失（遗漏期数）
    red_missing = {i: 0 for i in range(1, 34)}
    for num in range(1, 34):
        for i, draw in enumerate(history_data):
            if num in draw['red_numbers']:
                red_missing[num] = i
                break
    avg_miss = float(np.mean(list(red_missing.values()))) if red_missing else 1.0

    # 单号评分：频率 60% + 反遗漏 40%
    scores = []
    for n in range(1, 34):
        freq = red_counter.get(n, 0)
        freq_score = (freq / red_theory) if red_theory > 0 else 0
        miss = red_missing.get(n, 0)
        inv_missing = max(0.0, 1.0 - (miss / (avg_miss * 1.5 if avg_miss > 0 else 1.0)))
        score = 0.6 * freq_score + 0.4 * inv_missing
        scores.append((score, n))

    scores.sort(reverse=True)
    pool = [n for _, n in scores[:pool_size]]
    return pool


def find_top_ssq(top_k: int = 5, periods: int = 100, pool_size: int = 18, out_path: str = None) -> List[Dict[str, Any]]:
    evaluator = SSQNumberEvaluator('data/ssq_history.json')
    history = evaluator.load_history()

    # 历史完全匹配集合（用于排除）
    history_exact = build_history_exact_set(history)

    # 预计算蓝球频率/遗漏用于推荐蓝球
    recent = history[:periods]
    blue_counter = Counter()
    for d in recent:
        blue_counter[d['blue_number']] += 1
    blue_missing = {i: 0 for i in range(1, 17)}
    for num in range(1, 17):
        for i, draw in enumerate(history):
            if num == draw['blue_number']:
                blue_missing[num] = i
                break

    # 构建高质量红球池并组合
    red_pool = build_red_pool(history, periods, pool_size)

    candidates = []
    total_checked = 0
    start = time.time()

    for reds in itertools.combinations(red_pool, 6):
        if not passes_pattern_filters(reds):
            continue
        # 评分（蓝球不影响总分，这里取任意蓝球占位）
        dummy_blue = 1
        res = evaluator.evaluate(list(reds), dummy_blue)
        score = res['total_score']
        # 排除历史完全匹配时需要考虑蓝球，故此处仅记录红球分数
        candidates.append((score, tuple(sorted(reds))))
        total_checked += 1

    # 去重（相同红球）并按分数降序
    best_by_red: Dict[Tuple[int, ...], float] = {}
    for score, r in candidates:
        if (r not in best_by_red) or (score > best_by_red[r]):
            best_by_red[r] = score

    ranked = sorted(((s, r) for r, s in best_by_red.items()), reverse=True)

    # 选择前 top_k（包含并列）
    results = []
    if ranked:
        cutoff_score = None
        count_groups = 0
        for s, r in ranked:
            if cutoff_score is None:
                cutoff_score = s
            if count_groups < top_k or np.isclose(s, cutoff_score):
                # 为该红球选择推荐蓝球，避免历史完全一致
                b = choose_recommended_blue(blue_counter, blue_missing, history_exact, r)
                if b == -1:
                    # 如果所有蓝球都会命中历史完全一致，跳过
                    continue
                results.append({
                    'red_numbers': list(r),
                    'blue_number': b,
                    'total_score': round(float(s), 1)
                })
                count_groups += 1
                if count_groups >= top_k:
                    cutoff_score = s  # 记录边界分
            else:
                break

    elapsed = time.time() - start

    # 输出报告
    if out_path:
        lines = []
        lines.append('# 双色球最高评分号码（剪枝搜索）')
        lines.append('')
        lines.append(f'- 评分时间: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append(f'- 搜索设置: periods={periods}, pool_size={pool_size}')
        lines.append(f'- 候选组合数: {total_checked}, 用时: {elapsed:.2f}s')
        lines.append('')
        if not results:
            lines.append('> 未找到符合条件的组合（可能全部命中历史完全一致）。')
        else:
            top_score = results[0]['total_score']
            lines.append(f'## Top 评分: {top_score}/100')
            lines.append('')
            for i, item in enumerate(results, 1):
                reds = ' '.join(f"{n:02d}" for n in item['red_numbers'])
                b = item['blue_number']
                lines.append(f"{i}. 红球: {reds} | 蓝球: {b:02d} | 评分: {item['total_score']}")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    return results


def main():
    parser = argparse.ArgumentParser(description='搜索评分最高的双色球号码（排除历史完全一致）。')
    parser.add_argument('--top', type=int, default=5, help='返回前N组（含并列）')
    parser.add_argument('--periods', type=int, default=100, help='频率统计所用最近期数')
    parser.add_argument('--pool-size', type=int, default=18, help='红球候选池大小（越大越慢）')
    parser.add_argument('--out', type=str, default='docs/TOP_SSQ_NUMBERS.md', help='结果输出Markdown文件路径')

    args = parser.parse_args()

    results = find_top_ssq(top_k=args.top, periods=args.periods, pool_size=args.pool_size, out_path=args.out)
    # 控制台输出简表
    if not results:
        print('未找到结果')
        return
    top_score = results[0]['total_score']
    print(f"Top评分: {top_score}")
    for i, item in enumerate(results, 1):
        reds = ' '.join(f"{n:02d}" for n in item['red_numbers'])
        print(f"{i}. 红球: {reds} | 蓝球: {item['blue_number']:02d} | 评分: {item['total_score']}")


if __name__ == '__main__':
    main()

