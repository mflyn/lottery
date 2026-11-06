#!/usr/bin/env python
"""Restricted candidate search by native single-ticket fusion F."""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0,str(PROJECT_ROOT))

from typing import List, Tuple
from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.fusion_search import search_fusion

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


def find_top_ssq(top_k=5, periods=180, pool_size=18, out_path=None,
                   config=None, history_file='data/ssq_history.json'):
    """Return at most top_k candidates, ranked by unrounded fusion F (K=1)."""
    return search_fusion(SSQNumberEvaluator(history_file),top_k,periods,pool_size,
                         passes_pattern_filters,config,out_path)


def main():
    parser=argparse.ArgumentParser(description='按融合效用 F 搜索候选号码')
    parser.add_argument('--top',type=int,default=5)
    parser.add_argument('--periods',type=int,default=180)
    parser.add_argument('--pool-size',type=int,default=18)
    parser.add_argument('--out',default='docs/TOP_SSQ_NUMBERS.md')
    parser.add_argument('--history-file',default='data/ssq_history.json')
    args=parser.parse_args()
    results=find_top_ssq(args.top,args.periods,args.pool_size,args.out,history_file=args.history_file)
    for i,item in enumerate(results,1):
        print(f'{i}. {item}')


if __name__=='__main__':
    main()
