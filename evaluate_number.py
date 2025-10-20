#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双色球号码评价工具
根据历史数据从统计角度评价指定号码
"""

import json
import sys
from collections import Counter
from typing import Dict, List, Tuple
import numpy as np

def load_history_data(file_path: str) -> List[Dict]:
    """加载历史数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['data']

def analyze_frequency(history_data: List[Dict], periods: int = 100) -> Dict:
    """分析号码频率"""
    recent_data = history_data[:periods]
    
    red_counter = Counter()
    blue_counter = Counter()
    
    for draw in recent_data:
        red_counter.update(draw['red_numbers'])
        blue_counter[draw['blue_number']] += 1
    
    # 计算理论频率
    red_theory = periods * 6 / 33  # 每个红球理论出现次数
    blue_theory = periods / 16     # 每个蓝球理论出现次数
    
    return {
        'red_frequency': dict(red_counter),
        'blue_frequency': dict(blue_counter),
        'red_theory': red_theory,
        'blue_theory': blue_theory,
        'periods': periods
    }

def analyze_missing(history_data: List[Dict]) -> Dict:
    """分析号码遗漏（从最新一期开始计算）"""
    red_missing = {i: 0 for i in range(1, 34)}
    blue_missing = {i: 0 for i in range(1, 17)}

    # 从最新一期开始遍历
    for draw in history_data:
        red_numbers = draw['red_numbers']
        blue_number = draw['blue_number']

        # 红球遗漏：如果号码出现，停止计数；否则继续累加
        for num in range(1, 34):
            if num in red_numbers:
                # 如果遗漏值还是0，说明这是第一次遇到该号码，不更新
                if red_missing[num] == 0:
                    pass  # 保持为0
                else:
                    # 已经开始计数了，但又遇到了，说明之前的遗漏值是正确的
                    pass
            else:
                # 号码未出现，遗漏值+1
                red_missing[num] += 1

        # 蓝球遗漏：如果号码出现，停止计数；否则继续累加
        if blue_number in blue_missing:
            # 如果遗漏值还是0，说明这是第一次遇到该号码，不更新
            if blue_missing[blue_number] == 0:
                pass  # 保持为0

        for num in range(1, 17):
            if num != blue_number:
                blue_missing[num] += 1

    # 修正逻辑：重新计算遗漏值
    red_missing = {i: 0 for i in range(1, 34)}
    blue_missing = {i: 0 for i in range(1, 17)}

    # 从最新一期开始，计算每个号码的遗漏期数
    for num in range(1, 34):
        for i, draw in enumerate(history_data):
            if num in draw['red_numbers']:
                red_missing[num] = i
                break

    for num in range(1, 17):
        for i, draw in enumerate(history_data):
            if num == draw['blue_number']:
                blue_missing[num] = i
                break

    return {
        'red_missing': red_missing,
        'blue_missing': blue_missing
    }

def analyze_patterns(red_numbers: List[int]) -> Dict:
    """分析号码模式"""
    sorted_nums = sorted(red_numbers)
    
    # 1. 奇偶比
    odd_count = sum(1 for n in red_numbers if n % 2 == 1)
    even_count = 6 - odd_count
    
    # 2. 大小比（大号：18-33，小号：1-17）
    big_count = sum(1 for n in red_numbers if n >= 18)
    small_count = 6 - big_count
    
    # 3. 区间分布（1-11, 12-22, 23-33）
    zone1 = sum(1 for n in red_numbers if 1 <= n <= 11)
    zone2 = sum(1 for n in red_numbers if 12 <= n <= 22)
    zone3 = sum(1 for n in red_numbers if 23 <= n <= 33)
    
    # 4. 连号检测
    consecutive = []
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i+1] - sorted_nums[i] == 1:
            consecutive.append((sorted_nums[i], sorted_nums[i+1]))
    
    # 5. 和值
    sum_value = sum(red_numbers)
    
    # 6. 跨度（最大号-最小号）
    span = max(red_numbers) - min(red_numbers)
    
    # 7. AC值（号码复杂度）
    ac_value = calculate_ac_value(sorted_nums)
    
    return {
        'odd_even': f"{odd_count}:{even_count}",
        'big_small': f"{big_count}:{small_count}",
        'zone_distribution': f"{zone1}-{zone2}-{zone3}",
        'consecutive': consecutive,
        'sum': sum_value,
        'span': span,
        'ac_value': ac_value
    }

def calculate_ac_value(numbers: List[int]) -> int:
    """计算AC值（号码复杂度）"""
    differences = set()
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            differences.add(abs(numbers[i] - numbers[j]))
    return len(differences) - (len(numbers) - 1)

def check_historical_appearance(history_data: List[Dict], red_numbers: List[int], blue_number: int) -> Dict:
    """检查号码是否在历史中出现过"""
    red_set = set(red_numbers)
    
    exact_match = False
    red_match_counts = []
    blue_match_count = 0
    
    for draw in history_data:
        draw_red_set = set(draw['red_numbers'])
        draw_blue = draw['blue_number']
        
        # 检查完全匹配
        if draw_red_set == red_set and draw_blue == blue_number:
            exact_match = True
            break
        
        # 统计红球匹配数
        match_count = len(red_set & draw_red_set)
        red_match_counts.append(match_count)
        
        # 统计蓝球匹配
        if draw_blue == blue_number:
            blue_match_count += 1
    
    return {
        'exact_match': exact_match,
        'max_red_match': max(red_match_counts) if red_match_counts else 0,
        'avg_red_match': np.mean(red_match_counts) if red_match_counts else 0,
        'blue_appearance': blue_match_count
    }

def evaluate_number(red_numbers: List[int], blue_number: int, history_data: List[Dict]) -> Dict:
    """综合评价号码"""
    print("=" * 80)
    print("双色球号码统计评价报告")
    print("=" * 80)
    print(f"\n待评价号码: 红球 {red_numbers} | 蓝球 {blue_number}")
    print("\n" + "-" * 80)
    
    # 1. 频率分析（最近100期）
    print("\n【1. 频率分析】（基于最近100期）")
    print("-" * 80)
    freq_analysis = analyze_frequency(history_data, periods=100)
    
    print("\n红球频率分析:")
    red_freq_scores = []
    for num in red_numbers:
        freq = freq_analysis['red_frequency'].get(num, 0)
        theory = freq_analysis['red_theory']
        deviation = ((freq - theory) / theory * 100) if theory > 0 else 0
        
        if freq >= theory * 1.2:
            temp = "热门"
        elif freq <= theory * 0.8:
            temp = "冷门"
        else:
            temp = "温号"
        
        red_freq_scores.append(freq)
        print(f"  • 号码 {num:2d}: 出现 {freq:2d} 次 (理论 {theory:.1f} 次, 偏差 {deviation:+.1f}%) - {temp}")
    
    print(f"\n蓝球频率分析:")
    blue_freq = freq_analysis['blue_frequency'].get(blue_number, 0)
    blue_theory = freq_analysis['blue_theory']
    blue_deviation = ((blue_freq - blue_theory) / blue_theory * 100) if blue_theory > 0 else 0
    
    if blue_freq >= blue_theory * 1.2:
        blue_temp = "热门"
    elif blue_freq <= blue_theory * 0.8:
        blue_temp = "冷门"
    else:
        blue_temp = "温号"
    
    print(f"  • 号码 {blue_number:2d}: 出现 {blue_freq:2d} 次 (理论 {blue_theory:.1f} 次, 偏差 {blue_deviation:+.1f}%) - {blue_temp}")
    
    # 2. 遗漏分析
    print("\n【2. 遗漏分析】（当前遗漏期数）")
    print("-" * 80)
    missing_analysis = analyze_missing(history_data)
    
    print("\n红球遗漏:")
    red_missing_scores = []
    for num in red_numbers:
        missing = missing_analysis['red_missing'][num]
        red_missing_scores.append(missing)
        
        if missing == 0:
            status = "刚出现"
        elif missing <= 5:
            status = "短期遗漏"
        elif missing <= 15:
            status = "中期遗漏"
        else:
            status = "长期遗漏"
        
        print(f"  • 号码 {num:2d}: 遗漏 {missing:3d} 期 - {status}")
    
    print(f"\n蓝球遗漏:")
    blue_missing = missing_analysis['blue_missing'][blue_number]
    
    if blue_missing == 0:
        blue_status = "刚出现"
    elif blue_missing <= 3:
        blue_status = "短期遗漏"
    elif blue_missing <= 10:
        blue_status = "中期遗漏"
    else:
        blue_status = "长期遗漏"
    
    print(f"  • 号码 {blue_number:2d}: 遗漏 {blue_missing:3d} 期 - {blue_status}")
    
    # 3. 模式分析
    print("\n【3. 模式分析】")
    print("-" * 80)
    pattern = analyze_patterns(red_numbers)
    
    print(f"\n• 奇偶比: {pattern['odd_even']}")
    odd, even = map(int, pattern['odd_even'].split(':'))
    if odd == 3 and even == 3:
        print("  ✅ 标准奇偶比（3:3），平衡性好")
    elif 2 <= odd <= 4:
        print("  ✓ 奇偶比合理（2:4 或 4:2），常见模式")
    else:
        print("  ⚠️  奇偶比极端，出现概率较低")
    
    print(f"\n• 大小比: {pattern['big_small']}")
    big, small = map(int, pattern['big_small'].split(':'))
    if big == 3 and small == 3:
        print("  ✅ 标准大小比（3:3），平衡性好")
    elif 2 <= big <= 4:
        print("  ✓ 大小比合理（2:4 或 4:2），常见模式")
    else:
        print("  ⚠️  大小比极端，出现概率较低")
    
    print(f"\n• 区间分布: {pattern['zone_distribution']}")
    print("  (区间1: 01-11, 区间2: 12-22, 区间3: 23-33)")
    zones = list(map(int, pattern['zone_distribution'].split('-')))
    if all(z >= 1 for z in zones):
        print("  ✅ 三区都有号码，分布均衡")
    elif sum(1 for z in zones if z > 0) >= 2:
        print("  ✓ 覆盖两个区间，分布合理")
    else:
        print("  ⚠️  号码集中在一个区间，分布不均")
    
    print(f"\n• 连号: {len(pattern['consecutive'])} 组")
    if pattern['consecutive']:
        for pair in pattern['consecutive']:
            print(f"  - {pair[0]}-{pair[1]}")
        if len(pattern['consecutive']) >= 2:
            print("  ⚠️  连号较多，可能降低独特性")
        else:
            print("  ✓ 有连号，符合常见模式")
    else:
        print("  ✓ 无连号，独特性较高")
    
    print(f"\n• 和值: {pattern['sum']}")
    if 90 <= pattern['sum'] <= 130:
        print("  ✅ 和值在常见范围内（90-130）")
    elif 70 <= pattern['sum'] <= 150:
        print("  ✓ 和值合理（70-150）")
    else:
        print("  ⚠️  和值偏离常见范围")
    
    print(f"\n• 跨度: {pattern['span']}")
    if 15 <= pattern['span'] <= 28:
        print("  ✅ 跨度在常见范围内（15-28）")
    elif 10 <= pattern['span'] <= 32:
        print("  ✓ 跨度合理（10-32）")
    else:
        print("  ⚠️  跨度偏离常见范围")
    
    print(f"\n• AC值: {pattern['ac_value']}")
    if pattern['ac_value'] >= 6:
        print("  ✅ AC值较高，号码复杂度好")
    elif pattern['ac_value'] >= 4:
        print("  ✓ AC值中等，复杂度合理")
    else:
        print("  ⚠️  AC值较低，号码可能过于规律")
    
    # 4. 历史对比
    print("\n【4. 历史对比】")
    print("-" * 80)
    historical = check_historical_appearance(history_data, red_numbers, blue_number)
    
    if historical['exact_match']:
        print("\n⚠️  警告: 这注号码在历史上完全出现过！")
        print("  （虽然理论上可能再次出现，但概率极低）")
    else:
        print("\n✅ 这注号码从未完全出现过")
    
    print(f"\n• 红球最大匹配数: {historical['max_red_match']} 个")
    print(f"• 红球平均匹配数: {historical['avg_red_match']:.2f} 个")
    print(f"• 蓝球历史出现: {historical['blue_appearance']} 次")
    
    # 5. 综合评分
    print("\n【5. 综合评分】")
    print("-" * 80)
    
    # 频率得分（0-100）
    avg_red_freq = np.mean(red_freq_scores)
    freq_score = min(100, (avg_red_freq / freq_analysis['red_theory']) * 50 + 50)
    
    # 遗漏得分（0-100）
    avg_red_missing = np.mean(red_missing_scores)
    missing_score = min(100, 100 - avg_red_missing * 2)
    
    # 模式得分（0-100）
    pattern_score = 0
    if 2 <= odd <= 4:
        pattern_score += 20
    if 2 <= big <= 4:
        pattern_score += 20
    if all(z >= 1 for z in zones):
        pattern_score += 20
    if 90 <= pattern['sum'] <= 130:
        pattern_score += 20
    if pattern['ac_value'] >= 4:
        pattern_score += 20
    
    # 独特性得分（0-100）
    uniqueness_score = 100 - historical['max_red_match'] * 10
    
    # 综合得分
    total_score = (freq_score * 0.25 + missing_score * 0.25 + 
                   pattern_score * 0.3 + uniqueness_score * 0.2)
    
    print(f"\n• 频率得分: {freq_score:.1f}/100")
    print(f"• 遗漏得分: {missing_score:.1f}/100")
    print(f"• 模式得分: {pattern_score:.1f}/100")
    print(f"• 独特性得分: {uniqueness_score:.1f}/100")
    print(f"\n★ 综合得分: {total_score:.1f}/100")
    
    if total_score >= 80:
        rating = "优秀 ⭐⭐⭐⭐⭐"
    elif total_score >= 70:
        rating = "良好 ⭐⭐⭐⭐"
    elif total_score >= 60:
        rating = "中等 ⭐⭐⭐"
    elif total_score >= 50:
        rating = "一般 ⭐⭐"
    else:
        rating = "较差 ⭐"
    
    print(f"★ 综合评价: {rating}")
    
    # 6. 建议
    print("\n【6. 专家建议】")
    print("-" * 80)
    
    suggestions = []
    
    if avg_red_freq < freq_analysis['red_theory'] * 0.7:
        suggestions.append("• 红球整体偏冷，可能需要较长时间才会出现")
    elif avg_red_freq > freq_analysis['red_theory'] * 1.3:
        suggestions.append("• 红球整体偏热，短期内可能继续活跃")
    
    if avg_red_missing > 20:
        suggestions.append("• 部分红球遗漏较长，可能即将回补")
    
    if len(pattern['consecutive']) >= 2:
        suggestions.append("• 连号较多，可能降低独特性，中奖时分奖风险较高")
    
    if not (90 <= pattern['sum'] <= 130):
        suggestions.append("• 和值偏离常见范围，出现概率相对较低")
    
    if pattern['ac_value'] < 4:
        suggestions.append("• AC值较低，号码可能过于规律，建议增加复杂度")
    
    if historical['max_red_match'] >= 5:
        suggestions.append("• 与历史号码相似度较高，独特性不足")
    
    if not suggestions:
        suggestions.append("• 这是一注平衡性和独特性都不错的号码")
        suggestions.append("• 从统计角度看，各项指标都在合理范围内")
    
    for suggestion in suggestions:
        print(suggestion)
    
    print("\n" + "=" * 80)
    print("⚠️  重要提醒:")
    print("• 本评价仅基于历史统计数据，不代表中奖概率")
    print("• 每期开奖都是独立随机事件，过往数据不影响未来结果")
    print("• 理性购彩，量力而行")
    print("=" * 80)

if __name__ == "__main__":
    # 待评价的号码
    red_numbers = [3, 9, 16, 17, 24, 33]
    blue_number = 15
    
    # 加载历史数据
    history_data = load_history_data('data/ssq_history.json')
    
    print(f"\n数据加载成功: 共 {len(history_data)} 期历史数据")
    print(f"最新一期: {history_data[0]['draw_num']} ({history_data[0]['draw_date']})")
    print(f"最早一期: {history_data[-1]['draw_num']} ({history_data[-1]['draw_date']})")
    
    # 评价号码
    evaluate_number(red_numbers, blue_number, history_data)

