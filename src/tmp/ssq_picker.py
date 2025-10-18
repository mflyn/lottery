#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSQ（双色球）选号器 —— 去热门模式 + 跨注去相关 + 蓝球分散
-------------------------------------------------------
声明（请读完）：
- 本工具不会提高被开出的概率（数学上做不到）；做的是“工程化规避热门模式”，
  在中奖概率不变的前提下，尽量减少与他人撞号导致的“分奖”风险，并让资金曲线更平滑。
- 逻辑参考常见的人类选号“审美”偏好：等差/连号/生日化（≤31）/同尾过多/整齐倍数等。

规则摘要：
- 红球（1..33 选 6）：硬性约束 + 热门打分；多注之间控制重叠。
- 蓝球（1..16 选 1）：默认在多注之间不重复（可通过参数放宽）。
- 热门打分越高越“大众”，默认阈值 max-score=2，未命中阈值时会在有限次尝试后选取当轮“最好候选”。

用法示例：
  python ssq_picker.py -n 10 --seed 42 --export picks.csv
  python ssq_picker.py -n 5 --max-red-overlap 2 --max-score 1 --max-blue-dup-per-number 1
  python ssq_picker.py -n 20 --sum-low 75 --sum-high 135 --tries-per-ticket 80
"""
import argparse
import csv
import random
from itertools import combinations
from collections import Counter, defaultdict
from typing import List, Tuple

RED_N = 6
RED_MAX = 33
BLUE_MAX = 16

# ---------- 抽样工具 ----------
def sample_reds() -> List[int]:
    return sorted(random.sample(range(1, RED_MAX + 1), RED_N))

def sample_blue() -> int:
    return random.randint(1, BLUE_MAX)

# ---------- 序列工具 ----------
def max_consecutive_run(nums: List[int]) -> int:
    if not nums:
        return 0
    run, best = 1, 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1] + 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best

def is_ap(seq: List[int]) -> bool:
    if len(seq) <= 2:
        return True
    d = seq[1] - seq[0]
    for i in range(2, len(seq)):
        if seq[i] - seq[i-1] != d:
            return False
    return True

def has_ap_k_of_m(seq: List[int], k: int) -> bool:
    """是否存在长度>=k 的等差子序列（严格等差）。"""
    for comb in combinations(seq, k):
        s = sorted(comb)
        if is_ap(s):
            return True
    return False

def overlap_count(a: List[int], b: List[int]) -> int:
    return len(set(a) & set(b))

def zone_counts(nums: List[int]) -> Tuple[int, int, int]:
    """三区分布：1-11, 12-22, 23-33"""
    z1 = sum(1 for x in nums if 1 <= x <= 11)
    z2 = sum(1 for x in nums if 12 <= x <= 22)
    z3 = RED_N - z1 - z2
    return z1, z2, z3

# ---------- 热门模式打分（越高越大众） ----------
def popularity_score(reds: List[int], blue: int,
                     sum_bounds: Tuple[int, int]) -> int:
    s = 0
    # 1) 连号偏好
    run = max_consecutive_run(reds)
    if run >= 5:
        s += 5
    elif run == 4:
        s += 3
    elif run == 3:
        s += 1

    # 2) 等差偏好
    if is_ap(reds):
        s += 5
    elif has_ap_k_of_m(reds, 5):
        s += 3
    elif has_ap_k_of_m(reds, 4):
        s += 1

    # 3) 生日化（≤31 过多）
    birth_like = sum(1 for x in reds if x <= 31)
    if birth_like == 6:
        s += 3
    elif birth_like >= 5:
        s += 2

    # 4) 同尾数过多（同一尾数≥3）
    ld_cnt = Counter(x % 10 for x in reds)
    if any(c >= 4 for c in ld_cnt.values()):
        s += 3
    elif any(c == 3 for c in ld_cnt.values()):
        s += 2

    # 5) 整齐倍数（5 的倍数过多：5,10,15,20,25,30）
    mult5 = sum(1 for x in reds if x % 5 == 0)
    if mult5 >= 4:
        s += 3
    elif mult5 == 3:
        s += 1

    # 6) 奇偶极端
    odd = sum(1 for x in reds if x % 2 == 1)
    if odd in (0, 6):
        s += 1

    # 7) 和值偏离（轻惩罚；硬规则外的缓冲）
    rsum = sum(reds)
    lo, hi = sum_bounds
    if rsum < lo or rsum > hi:
        s += 1

    # 8) 区间过度集中（全部在一个区间 or 5+集中）
    z1, z2, z3 = zone_counts(reds)
    if max(z1, z2, z3) == 6:
        s += 3
    elif max(z1, z2, z3) >= 5:
        s += 1

    # 9) 蓝球“撞大众”（这里仅轻微惩罚中位常见数字）
    if 7 <= blue <= 10:
        s += 1

    # 打分范围大致 0-15，实际以规则组合为准
    return s

# ---------- 硬性规则（直接拒绝） ----------
def hard_reject(reds: List[int], blue: int,
                max_run_allowed: int,
                max_same_last_digit: int,
                odd_bounds: Tuple[int, int],
                sum_bounds: Tuple[int, int]) -> bool:
    # 连号长度限制
    if max_consecutive_run(reds) > max_run_allowed:
        return True
    # 同尾限制
    ld_cnt = Counter(x % 10 for x in reds)
    if any(c > max_same_last_digit for c in ld_cnt.values()):
        return True
    # 奇偶限制
    odd = sum(1 for x in reds if x % 2 == 1)
    if not (odd_bounds[0] <= odd <= odd_bounds[1]):
        return True
    # 和值限制
    rsum = sum(reds)
    if not (sum_bounds[0] <= rsum <= sum_bounds[1]):
        return True
    return False

# ---------- 主生成器 ----------
def generate_tickets(n_tickets: int,
                     max_red_overlap: int,
                     max_blue_dup_per_number: int,
                     max_score: int,
                     max_run_allowed: int,
                     max_same_last_digit: int,
                     odd_low: int,
                     odd_high: int,
                     sum_low: int,
                     sum_high: int,
                     tries_per_ticket: int):
    picks: List[Tuple[List[int], int, int]] = []
    blue_use = defaultdict(int)

    for _ in range(n_tickets):
        best = None  # (reds, blue, score)
        best_score = 10**9
        for _t in range(tries_per_ticket):
            reds = sample_reds()
            blue = sample_blue()

            # 硬规则拒绝
            if hard_reject(
                reds, blue,
                max_run_allowed=max_run_allowed,
                max_same_last_digit=max_same_last_digit,
                odd_bounds=(odd_low, odd_high),
                sum_bounds=(sum_low, sum_high)
            ):
                continue

            # 跨注去相关：红球重叠
            too_similar = False
            for (pr, pb, _sc) in picks:
                if overlap_count(reds, pr) > max_red_overlap:
                    too_similar = True
                    break
            if too_similar:
                continue

            # 蓝球分散：同一蓝球出现次数限制
            if blue_use[blue] >= max_blue_dup_per_number:
                continue

            sc = popularity_score(reds, blue, (sum_low, sum_high))
            if sc <= max_score:
                picks.append((reds, blue, sc))
                blue_use[blue] += 1
                break

            # 记录最好候选
            if sc < best_score:
                best = (reds, blue, sc)
                best_score = sc
        else:
            # 达不到阈值，接受当前“最好候选”，同时登记蓝球使用
            if best is None:
                # 极端兜底
                best = (sample_reds(), sample_blue(), 99)
            picks.append(best)
            blue_use[best[1]] += 1

    return picks

def fmt_line(reds: List[int], blue: int) -> str:
    R = " ".join(f"{x:02d}" for x in reds)
    return f"R: {R}  |  B: {blue:02d}"

def main():
    parser = argparse.ArgumentParser(description="SSQ 去热门 & 去相关 选号器")
    parser.add_argument("-n", "--num", type=int, default=10, help="要生成的注数，默认10")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")

    # 跨注去相关与蓝球分散
    parser.add_argument("--max-red-overlap", type=int, default=2,
                        help="任意两注红球最多允许重叠的号码个数，默认2（期望≈1.09，取2较保守）")
    parser.add_argument("--max-blue-dup-per-number", type=int, default=1,
                        help="同一蓝球在全部注中最多允许出现的次数，默认1（即不重复）")

    # 热门阈值与硬规则
    parser.add_argument("--max-score", type=int, default=2,
                        help="热门打分阈值，<=该值才接受；默认2（越小越严）")
    parser.add_argument("--max-run", type=int, default=2,
                        help="红球允许的最大连号长度，默认2（>2 直接拒绝）")
    parser.add_argument("--max-same-last-digit", type=int, default=2,
                        help="红球同尾数最大允许计数，默认2（>=3 拒绝）")
    parser.add_argument("--odd-low", type=int, default=2, help="红球奇数个数下界，默认2")
    parser.add_argument("--odd-high", type=int, default=4, help="红球奇数个数上界，默认4")
    parser.add_argument("--sum-low", type=int, default=70, help="红球和值下界，默认70")
    parser.add_argument("--sum-high", type=int, default=140, help="红球和值上界，默认140")
    parser.add_argument("--tries-per-ticket", type=int, default=60,
                        help="每注最大尝试次数，默认60；过严时会降级接受最好候选")

    parser.add_argument("--export", type=str, default=None,
                        help="导出到 CSV 文件路径（可选）")

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    picks = generate_tickets(
        n_tickets=args.num,
        max_red_overlap=args.max_red_overlap,
        max_blue_dup_per_number=args.max_blue_dup_per_number,
        max_score=args.max_score,
        max_run_allowed=args.max_run,
        max_same_last_digit=args.max_same_last_digit,
        odd_low=args.odd_low,
        odd_high=args.odd_high,
        sum_low=args.sum_low,
        sum_high=args.sum_high,
        tries_per_ticket=args.tries_per_ticket
    )

    print("—— SSQ 去热门 & 去相关 选号结果 ——")
    for i, (r, b, sc) in enumerate(picks, 1):
        print(f"[{i:02d}] {fmt_line(r, b)}    score={sc}")

    if args.export:
        with open(args.export, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow(["index", "red_numbers", "blue_number", "popularity_score"])
            for i, (r, b, sc) in enumerate(picks, 1):
                writer.writerow([i, " ".join(map(str, r)), b, sc])
        print(f"\n已导出到：{args.export}")

if __name__ == "__main__":
    main()
