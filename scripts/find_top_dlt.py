#!/usr/bin/env python
"""Restricted candidate search by native single-ticket fusion F."""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0,str(PROJECT_ROOT))

from typing import List, Tuple
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator
from src.core.evaluators.fusion_search import search_fusion

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


def find_top_dlt(top_k=5, periods=180, pool_size=20, out_path=None,
                   config=None, history_file='data/dlt_history.json'):
    """Return at most top_k candidates, ranked by unrounded fusion F (K=1)."""
    return search_fusion(DLTNumberEvaluator(history_file),top_k,periods,pool_size,
                         passes_pattern_filters,config,out_path)


def main():
    parser=argparse.ArgumentParser(description='按融合效用 F 搜索候选号码')
    parser.add_argument('--top',type=int,default=5)
    parser.add_argument('--periods',type=int,default=180)
    parser.add_argument('--pool-size',type=int,default=20)
    parser.add_argument('--out',default='docs/TOP_DLT_NUMBERS.md')
    parser.add_argument('--history-file',default='data/dlt_history.json')
    args=parser.parse_args()
    results=find_top_dlt(args.top,args.periods,args.pool_size,args.out,history_file=args.history_file)
    for i,item in enumerate(results,1):
        print(f'{i}. {item}')


if __name__=='__main__':
    main()
