#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLT (大乐透) 选号器 —— 去热门模式 + 跨注去相关
------------------------------------------------
目标：在不改变中奖概率的前提下，尽量避开“热门”人类选号模式（生日/整齐/连号/等差等），并让多注之间
相互“去相关”（前区重叠尽量小、后区不完全相同），从而在真中时更不容易“分奖”。

【数学事实】：
- 任何策略都不会提高“被开出来”的概率；这里做的是“去热门”和“去重叠”工程化优化。
- 这能提高“独享奖金”的机会（同样中奖概率下，减少撞车）。

默认规则（可用参数微调）：
- 前区（1..35 选5）：避免3+连号、避免等差、避免尾数过度集中、生日化（≤31过多）等；
- 后区（1..12 选2）：尽量避免一对连续数；
- 多注之间：默认前区最多重叠2个数、后区不完全相同。
- 和值（前区）适度约束（默认60~120），奇偶不过度极端。

用法示例：
  python dlt_picker.py -n 10 --seed 42 --export picks.csv
  python dlt_picker.py -n 5 --max-front-overlap 1 --max-score 2

参数说明见 `python dlt_picker.py -h`
"""
import argparse
import csv
import random
from itertools import combinations
from collections import Counter
from typing import List, Tuple

FRONT_N = 5
FRONT_MAX = 35
BACK_N = 2
BACK_MAX = 12

# ---------- 组合工具 ----------
def sample_sorted(a: int, k: int) -> List[int]:
    return sorted(random.sample(range(1, a + 1), k))

def max_consecutive_run(nums: List[int]) -> int:
    run, best = 1, 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best if nums else 0

def is_arithmetic_progression(seq: List[int]) -> bool:
    if len(seq) <= 2:
        return True
    d = seq[1] - seq[0]
    for i in range(2, len(seq)):
        if seq[i] - seq[i-1] != d:
            return False
    return True

def has_ap_k_of_m(seq: List[int], k: int) -> bool:
    # 是否存在长度>=k 的等差子序列（严格等差）
    for combi in combinations(seq, k):
        s = sorted(combi)
        if is_arithmetic_progression(s):
            return True
    return False

def overlap_count(a: List[int], b: List[int]) -> int:
    return len(set(a) & set(b))

# ---------- 热门模式打分 ----------
def popularity_score(front: List[int], back: List[int]) -> int:
    """
    越高越“热门”，我们倾向拒绝或降低优先级。
    """
    score = 0
    # 1) 前区连号过多
    max_run = max_consecutive_run(front)
    if max_run >= 4:
        score += 4
    elif max_run == 3:
        score += 2

    # 2) 等差结构（人类常选整齐差值）
    if is_arithmetic_progression(front):
        score += 4
    elif has_ap_k_of_m(front, 4):  # 4/5 形成等差
        score += 2

    # 3) 生日化（≤31 过多）
    birthday_like = sum(1 for x in front if x <= 31)
    if birthday_like == 5:
        score += 4
    elif birthday_like >= 4:
        score += 2

    # 4) 尾数过于集中（同一尾数≥3）
    last_digits = [x % 10 for x in front]
    ld_cnt = Counter(last_digits)
    if any(c >= 3 for c in ld_cnt.values()):
        score += 2

    # 5) 0/5 尾数过多（整齐感强）
    zero_five = sum(1 for x in front if x % 5 == 0)
    if zero_five >= 3:
        score += 2

    # 6) 奇偶极端（全奇/全偶）
    odd = sum(1 for x in front if x % 2 == 1)
    if odd in (0, 5):
        score += 1

    # 7) 和值太极端（默认 60~120 更自然）
    s = sum(front)
    if s < 60 or s > 120:
        score += 1

    # 8) 后区连号（人类常用，略加惩罚）
    if abs(back[0] - back[1]) == 1:
        score += 1

    return score

# ---------- 硬性规则（直接拒绝） ----------
def hard_reject(front: List[int], back: List[int],
                 max_run_allowed: int,
                 max_same_last_digit: int,
                 odd_bounds: Tuple[int, int],
                 sum_bounds: Tuple[int, int],
                 avoid_back_consecutive: bool) -> bool:
    # 连号长度限制
    if max_consecutive_run(front) > max_run_allowed:
        return True
    # 尾数集中限制
    ld_cnt = Counter([x % 10 for x in front])
    if any(c > max_same_last_digit for c in ld_cnt.values()):
        return True
    # 奇偶限制
    odd = sum(1 for x in front if x % 2 == 1)
    if odd < odd_bounds[0] or odd > odd_bounds[1]:
        return True
    # 和值限制
    s = sum(front)
    if s < sum_bounds[0] or s > sum_bounds[1]:
        return True
    # 后区是否拒绝连续
    if avoid_back_consecutive and abs(back[0] - back[1]) == 1:
        return True
    return False

# ---------- 主生成器 ----------
def generate_tickets(n_tickets: int,
                     max_front_overlap: int,
                     max_back_overlap: int,
                     max_score: int,
                     max_run_allowed: int,
                     max_same_last_digit: int,
                     odd_low: int,
                     odd_high: int,
                     sum_low: int,
                     sum_high: int,
                     avoid_back_consecutive: bool,
                     tries_per_ticket: int):
    picks = []
    for _ in range(n_tickets):
        best = None  # (front, back, score)
        best_score = 10**9
        for _t in range(tries_per_ticket):
            front = sample_sorted(FRONT_MAX, FRONT_N)
            back = sample_sorted(BACK_MAX, BACK_N)
            # 硬拒绝
            if hard_reject(front, back,
                           max_run_allowed=max_run_allowed,
                           max_same_last_digit=max_same_last_digit,
                           odd_bounds=(odd_low, odd_high),
                           sum_bounds=(sum_low, sum_high),
                           avoid_back_consecutive=avoid_back_consecutive):
                continue
            # 跨注去重叠
            too_similar = False
            for (pf, pb, _sc) in picks:
                if overlap_count(front, pf) > max_front_overlap:
                    too_similar = True
                    break
                if overlap_count(back, pb) > max_back_overlap:
                    too_similar = True
                    break
            if too_similar:
                continue

            # 热门分数
            sc = popularity_score(front, back)
            if sc <= max_score:
                picks.append((front, back, sc))
                break
            # 记录最好的以便必要时降级接受
            if sc < best_score:
                best = (front, back, sc)
                best_score = sc
        else:
            # 没找到达到阈值的，用当前最好的（提示：阈值可能过严）
            if best is None:
                best = (sample_sorted(FRONT_MAX, FRONT_N),
                        sample_sorted(BACK_MAX, BACK_N),
                        99)
            picks.append(best)
    return picks

def fmt_line(front, back) -> str:
    F = " ".join(f"{x:02d}" for x in front)
    B = " ".join(f"{x:02d}" for x in back)
    return f"F: {F}  |  B: {B}"

def main():
    parser = argparse.ArgumentParser(description="DLT 去热门 & 去相关 选号器")
    parser.add_argument("-n", "--num", type=int, default=10, help="要生成的注数，默认10")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")

    # 跨注相关性
    parser.add_argument("--max-front-overlap", type=int, default=2,
                        help="任意两注前区最多允许重叠的号码个数，默认2")
    parser.add_argument("--max-back-overlap", type=int, default=1,
                        help="任意两注后区最多允许重叠的号码个数，默认1（即后区不完全相同）")

    # 热门阈值与硬规则
    parser.add_argument("--max-score", type=int, default=2,
                        help="热门打分阈值，<=该分数才接受；默认2（越严越小）")
    parser.add_argument("--max-run", type=int, default=2,
                        help="前区允许的最大连号长度，默认2（>2直接拒绝）")
    parser.add_argument("--max-same-last-digit", type=int, default=2,
                        help="前区同尾数最大允许计数，默认2（>=3拒绝）")
    parser.add_argument("--odd-low", type=int, default=1, help="前区奇数下界，默认1")
    parser.add_argument("--odd-high", type=int, default=4, help="前区奇数上界，默认4")
    parser.add_argument("--sum-low", type=int, default=60, help="前区和值下界，默认60")
    parser.add_argument("--sum-high", type=int, default=120, help="前区和值上界，默认120")
    parser.add_argument("--avoid-back-consecutive", action="store_true",
                        help="后区强制不允许连续数（默认只是加分惩罚，不强制）")
    parser.add_argument("--tries-per-ticket", type=int, default=60,
                        help="每注最大尝试次数，默认60；过严时会降级接受最好候选")

    parser.add_argument("--export", type=str, default=None,
                        help="导出到 CSV 文件路径（可选）")

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    picks = generate_tickets(
        n_tickets=args.num,
        max_front_overlap=args.max_front_overlap,
        max_back_overlap=args.max_back_overlap,
        max_score=args.max_score,
        max_run_allowed=args.max_run,
        max_same_last_digit=args.max_same_last_digit,
        odd_low=args.odd_low,
        odd_high=args.odd_high,
        sum_low=args.sum_low,
        sum_high=args.sum_high,
        avoid_back_consecutive=args.avoid_back_consecutive,
        tries_per_ticket=args.tries_per_ticket
    )

    print("—— DLT 去热门 & 去相关 选号结果 ——")
    for i, (f, b, sc) in enumerate(picks, 1):
        print(f"[{i:02d}] {fmt_line(f, b)}    score={sc}")

    if args.export:
        with open(args.export, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow(["index", "front_numbers", "back_numbers", "popularity_score"])
            for i, (f, b, sc) in enumerate(picks, 1):
                writer.writerow([i, " ".join(map(str, f)), " ".join(map(str, b)), sc])
        print(f"\n已导出到：{args.export}")

if __name__ == "__main__":
    main()
