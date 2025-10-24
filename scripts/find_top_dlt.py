#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从所有大乐透号码组合中（在可行范围内通过剪枝保证质量）找到评分最高的号码，排除历史中奖号码。
说明：
- 评分体系使用现有 DLTNumberEvaluator，一致性完全对齐
- 后区已纳入总分计算
- 为保证可运行性，使用启发式剪枝：先选取高质量前区池，再组合并筛选模式
- 若分数并列，将全部列出

用法：
    python scripts/find_top_dlt.py --top 5 --periods 100 --pool-size 20 --out docs/TOP_DLT_NUMBERS.md
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

from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator


def calc_ac_value(nums: List[int]) -> int:
    """计算AC值（号码复杂度）"""
    s = sorted(nums)
    diffs = set()
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n):
            diffs.add(s[j] - s[i])
    return len(diffs) - (n - 1)


def passes_pattern_filters(front: Tuple[int, ...]) -> bool:
    """前区模式过滤器"""
    # 奇偶 2..3
    odd = sum(1 for n in front if n % 2)
    if not (2 <= odd <= 3):
        return False
    
    # 大小 2..3 (大: >=18)
    big = sum(1 for n in front if n >= 18)
    if not (2 <= big <= 3):
        return False
    
    # 区间至少覆盖2个区（1-12,13-24,25-35）
    z1 = sum(1 for n in front if 1 <= n <= 12)
    z2 = sum(1 for n in front if 13 <= n <= 24)
    z3 = sum(1 for n in front if 25 <= n <= 35)
    if (z1 > 0) + (z2 > 0) + (z3 > 0) < 2:
        return False
    
    # 跨度 10..34
    span = max(front) - min(front)
    if not (10 <= span <= 34):
        return False
    
    # 和值 70..130
    s = sum(front)
    if not (70 <= s <= 130):
        return False
    
    # AC 值 >= 3
    if calc_ac_value(list(front)) < 3:
        return False
    
    return True


def build_history_exact_set(history_data: List[Dict[str, Any]]) -> set:
    """构建历史完全匹配集合（前区+后区）"""
    exact = set()
    for draw in history_data:
        f = tuple(sorted(draw['front_numbers']))
        b = tuple(sorted(draw['back_numbers']))
        exact.add((f, b))
    return exact


def build_front_pool(history_data: List[Dict[str, Any]], periods: int, pool_size: int) -> List[int]:
    """构建高质量前区号码池"""
    recent = history_data[:periods]
    front_counter = Counter()
    for d in recent:
        front_counter.update(d['front_numbers'])
    front_theory = periods * 5 / 35 if periods else 0

    # 计算遗漏期数
    front_missing = {i: 0 for i in range(1, 36)}
    for num in range(1, 36):
        for i, draw in enumerate(history_data):
            if num in draw['front_numbers']:
                front_missing[num] = i
                break
    avg_miss = float(np.mean(list(front_missing.values()))) if front_missing else 1.0

    # 单号评分：频率 60% + 反遗漏 40%
    scores = []
    for n in range(1, 36):
        freq = front_counter.get(n, 0)
        freq_score = (freq / front_theory) if front_theory > 0 else 0
        miss = front_missing.get(n, 0)
        inv_missing = max(0.0, 1.0 - (miss / (avg_miss * 1.5 if avg_miss > 0 else 1.0)))
        score = 0.6 * freq_score + 0.4 * inv_missing
        scores.append((score, n))

    scores.sort(reverse=True)
    pool = [n for _, n in scores[:pool_size]]
    return pool


def build_back_pool(history_data: List[Dict[str, Any]], periods: int) -> List[int]:
    """构建后区号码池（返回所有12个号码，按评分排序）"""
    recent = history_data[:periods]
    back_counter = Counter()
    for d in recent:
        back_counter.update(d['back_numbers'])
    back_theory = periods * 2 / 12 if periods else 0

    # 计算遗漏期数
    back_missing = {i: 0 for i in range(1, 13)}
    for num in range(1, 13):
        for i, draw in enumerate(history_data):
            if num in draw['back_numbers']:
                back_missing[num] = i
                break
    avg_miss = float(np.mean(list(back_missing.values()))) if back_missing else 1.0

    # 单号评分
    scores = []
    for n in range(1, 13):
        freq = back_counter.get(n, 0)
        freq_score = (freq / back_theory) if back_theory > 0 else 0
        miss = back_missing.get(n, 0)
        inv_missing = max(0.0, 1.0 - (miss / (avg_miss * 1.5 if avg_miss > 0 else 1.0)))
        score = 0.6 * freq_score + 0.4 * inv_missing
        scores.append((score, n))

    scores.sort(reverse=True)
    pool = [n for _, n in scores]
    return pool


def find_top_dlt(top_k: int = 5, periods: int = 100, pool_size: int = 20, out_path: str = None) -> List[Dict[str, Any]]:
    """
    搜索评分最高的大乐透号码组合
    
    Args:
        top_k: 返回前K名（包含并列）
        periods: 统计期数
        pool_size: 前区候选池大小
        out_path: 输出文件路径（可选）
    
    Returns:
        评分最高的号码组合列表
    """
    evaluator = DLTNumberEvaluator('data/dlt_history.json')
    history = evaluator.load_history()

    # 历史完全匹配集合（用于排除）
    history_exact = build_history_exact_set(history)

    # 构建高质量前区池和后区池
    front_pool = build_front_pool(history, periods, pool_size)
    back_pool = build_back_pool(history, periods)

    candidates = []
    total_checked = 0
    start = time.time()

    # 遍历前区组合
    for front in itertools.combinations(front_pool, 5):
        if not passes_pattern_filters(front):
            continue
        f_sorted = tuple(sorted(front))
        
        # 遍历后区组合
        for back in itertools.combinations(back_pool, 2):
            b_sorted = tuple(sorted(back))
            if (f_sorted, b_sorted) in history_exact:
                continue
            
            res = evaluator.evaluate(list(f_sorted), list(b_sorted))
            score = res['total_score']
            candidates.append((score, f_sorted, b_sorted))
            total_checked += 1

    # 全量按分数降序
    ranked = sorted(candidates, key=lambda x: x[0], reverse=True)

    # 选择前 top_k（包含并列）
    results = []
    if ranked:
        # 第K名的分数作为截断，包含并列
        kth_index = min(top_k, len(ranked)) - 1
        cutoff_score = ranked[kth_index][0]
        for s, f, b in ranked:
            if s < cutoff_score and not np.isclose(s, cutoff_score):
                break
            results.append({
                'front_numbers': list(f),
                'back_numbers': list(b),
                'total_score': round(float(s), 1)
            })

    elapsed = time.time() - start

    # 输出报告
    if out_path:
        lines = []
        lines.append('# 大乐透最高评分号码（剪枝搜索）')
        lines.append('')
        lines.append(f'- 评分时间: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append(f'- 搜索设置: periods={periods}, pool_size={pool_size}')
        lines.append(f'- 评估组合数: {total_checked}, 用时: {elapsed:.2f}s')
        lines.append('')
        if not results:
            lines.append('> 未找到符合条件的组合（可能全部命中历史完全一致）。')
        else:
            top_score = results[0]['total_score']
            lines.append(f'## Top 评分: {top_score}/100')
            lines.append('')
            for i, item in enumerate(results, 1):
                front = ' '.join(f"{n:02d}" for n in item['front_numbers'])
                back = ' '.join(f"{n:02d}" for n in item['back_numbers'])
                lines.append(f"{i}. 前区: {front} | 后区: {back} | 评分: {item['total_score']}")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    return results


def main():
    parser = argparse.ArgumentParser(description='搜索评分最高的大乐透号码（排除历史完全一致）。')
    parser.add_argument('--top', type=int, default=5, help='返回前K名（包含并列），默认5')
    parser.add_argument('--periods', type=int, default=100, help='统计期数，默认100')
    parser.add_argument('--pool-size', type=int, default=20, help='前区候选池大小，默认20')
    parser.add_argument('--out', type=str, default='docs/TOP_DLT_NUMBERS.md', help='输出文件路径')
    args = parser.parse_args()

    print(f"开始搜索大乐透最高评分号码...")
    print(f"  - 统计期数: {args.periods}")
    print(f"  - 前区候选池: {args.pool_size}")
    print(f"  - 返回数量: {args.top}")
    print()

    results = find_top_dlt(
        top_k=args.top,
        periods=args.periods,
        pool_size=args.pool_size,
        out_path=args.out
    )

    print(f"\n搜索完成！")
    print(f"  - 找到 {len(results)} 注号码")
    if results:
        print(f"  - 最高评分: {results[0]['total_score']}")
    print(f"  - 结果已保存到: {args.out}")


if __name__ == '__main__':
    main()

