from typing import Dict, List, Any
import pandas as pd
from collections import Counter

def _ensure_int_list(value) -> List[int]:
    """将各种格式的号码值转换为整数列表"""
    if value is None:
        return []
    if hasattr(value, 'tolist') and not isinstance(value, (str, bytes)):
        return _ensure_int_list(value.tolist())
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            try:
                if pd.isna(item):
                    continue
            except TypeError:
                pass
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith('[') and text.endswith(']'):
            text = text[1:-1]
        text = text.replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',')
        parts = [p.strip() for p in text.replace(' ', ',').split(',') if p.strip()]
        result = []
        for part in parts:
            try:
                result.append(int(float(part)))
            except ValueError:
                continue
        return result
    try:
        if pd.isna(value):
            return []
    except TypeError:
        pass
    try:
        return [int(value)]
    except (TypeError, ValueError):
        return []

class PatternAnalyzer:
    """号码模式分析器"""
    
    def __init__(self, lottery_type: str):
        """
        Args:
            lottery_type: 彩票类型 ('dlt' 或 'ssq')
        """
        self.lottery_type = lottery_type
        self._zone_configs = {
            'ssq': {
                'red': (1, 33, 11),   # 1-11, 12-22, 23-33
                'blue': (1, 16, 5)    # 1-5, 6-10, 11-15, 16
            },
            'dlt': {
                'front': (1, 35, 12), # 1-12, 13-24, 25-35
                'back': (1, 12, 4)    # 1-4, 5-8, 9-12
            }
        }
        
    def analyze(self, history_data: pd.DataFrame) -> Dict:
        """分析历史数据中的模式
        
        Args:
            history_data: 历史开奖数据
            
        Returns:
            Dict: 模式分析结果
        """
        if self.lottery_type == 'dlt':
            return self._analyze_dlt(history_data)
        else:
            return self._analyze_ssq(history_data)
            
    def _analyze_dlt(self, history_data: pd.DataFrame) -> Dict:
        """分析大乐透数据模式"""
        patterns = {
            'front': self._analyze_number_patterns(history_data.get('front_numbers'), area='front'),
            'back': self._analyze_number_patterns(history_data.get('back_numbers'), area='back')
        }
        return patterns
        
    def _analyze_ssq(self, history_data: pd.DataFrame) -> Dict:
        """分析双色球数据模式"""
        blue_series = None
        if 'blue_numbers' in history_data.columns:
            blue_series = history_data['blue_numbers']
        elif 'blue_number' in history_data.columns:
            blue_series = history_data['blue_number'].apply(lambda x: [x] if pd.notna(x) else [])

        patterns = {
            'red': self._analyze_number_patterns(history_data.get('red_numbers'), area='red'),
            'blue': self._analyze_number_patterns(blue_series, area='blue')
        }
        return patterns
        
    def _analyze_number_patterns(self, numbers: pd.Series, area: str = '') -> Dict[str, Any]:
        """分析号码序列的模式
        
        Args:
            numbers: 号码序列
            
        Returns:
            Dict: 模式分析结果
        """
        if numbers is None:
            return {
                'odd_even_ratio': {},
                'span': {},
                'consecutive': {},
                'sum_range': {}
            }

        # 规范化为列表序列
        normalized: List[List[int]] = []
        for value in numbers:
            nums = _ensure_int_list(value)
            if nums:
                normalized.append(sorted(nums))

        if not normalized:
            return {
                'odd_even_ratio': {},
                'span': {},
                'consecutive': {},
                'sum_range': {}
            }

        # 基础模式分析
        patterns = {
            'odd_even_ratio': self._analyze_odd_even_ratio(normalized),
            'span': self._analyze_span(normalized),
            'consecutive': self._analyze_consecutive(normalized),
            'sum_range': self._analyze_sum_range(normalized),
            'zone_distribution': self._analyze_zone_distribution(normalized, area)
        }
        return patterns
        
    def _analyze_odd_even_ratio(self, numbers: List[List[int]]) -> Dict[str, Any]:
        """分析奇偶比例"""
        ratios = []
        for nums in numbers:
            if not nums:
                continue
            odd = sum(1 for n in nums if n % 2 == 1)
            even = len(nums) - odd
            ratios.append(f"{odd}:{even}")

        if not ratios:
            return {}

        counter = Counter(ratios)
        most_common = counter.most_common(1)[0]
        return {
            'ratio_distribution': counter.most_common(),
            'most_common_ratio': most_common,
            'total_draws': len(ratios)
        }
        
    def _analyze_span(self, numbers: List[List[int]]) -> Dict[str, Any]:
        """分析号码跨度"""
        spans = []
        for nums in numbers:
            if not nums:
                continue
            spans.append(max(nums) - min(nums))

        if not spans:
            return {}

        return {
            'min': min(spans),
            'max': max(spans),
            'avg': sum(spans) / len(spans),
            'distribution': Counter(spans).most_common()
        }
        
    def _analyze_consecutive(self, numbers: List[List[int]]) -> Dict[str, Any]:
        """分析连号情况"""
        consecutive_counts = []
        max_runs = []

        for nums in numbers:
            if len(nums) < 2:
                consecutive_counts.append(0)
                max_runs.append(1 if nums else 0)
                continue
            run = 1
            max_run = 1
            consecutive_pairs = 0
            for i in range(1, len(nums)):
                if nums[i] - nums[i - 1] == 1:
                    consecutive_pairs += 1
                    run += 1
                    if run > max_run:
                        max_run = run
                else:
                    run = 1
            consecutive_counts.append(consecutive_pairs)
            max_runs.append(max_run)

        total = len(consecutive_counts)
        has_consecutive = sum(1 for c in consecutive_counts if c > 0)
        return {
            'ratio_with_consecutive': has_consecutive / total if total else 0,
            'avg_pairs': sum(consecutive_counts) / total if total else 0,
            'max_run': max(max_runs) if max_runs else 0,
            'pair_count_distribution': Counter(consecutive_counts).most_common()
        }
        
    def _analyze_sum_range(self, numbers: List[List[int]]) -> Dict[str, Any]:
        """分析和值范围"""
        sums = []
        for nums in numbers:
            if nums:
                sums.append(sum(nums))

        if not sums:
            return {}

        return {
            'min': min(sums),
            'max': max(sums),
            'avg': sum(sums) / len(sums),
            'distribution': Counter(sums).most_common()
        }

    def _analyze_zone_distribution(self, numbers: List[List[int]], area: str) -> Dict[str, Any]:
        """分析区间分布"""
        zone_ranges = self._get_zone_ranges(area)
        if not zone_ranges:
            return {}

        counts = Counter()
        for nums in numbers:
            for n in nums:
                for start, end in zone_ranges:
                    if start <= n <= end:
                        counts[(start, end)] += 1
                        break

        result = []
        for start, end in zone_ranges:
            result.append({'range': f"{start}-{end}", 'count': counts.get((start, end), 0)})
        return {
            'ranges': result,
            'total_numbers': sum(item['count'] for item in result)
        }

    def _get_zone_ranges(self, area: str) -> List[tuple]:
        """获取区间范围配置"""
        config = self._zone_configs.get(self.lottery_type, {}).get(area)
        if not config:
            return []
        start, end, step = config
        ranges = []
        current = start
        while current <= end:
            next_end = min(current + step - 1, end)
            ranges.append((current, next_end))
            current = next_end + 1
        return ranges
