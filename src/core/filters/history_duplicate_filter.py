"""
历史重复过滤器

用于过滤与历史开奖号码重复过多的候选号码
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import pandas as pd

from ..models import SSQNumber, DLTNumber


@dataclass
class FilterResult:
    """过滤结果"""
    is_valid: bool              # 是否通过过滤
    overlap_score: float        # 重复度评分（越低越好）
    max_overlap: int            # 最大重复数量
    overlap_period: Optional[str]  # 重复最多的期号
    reason: Optional[str]       # 拒绝原因（如果拒绝）


class HistoryDuplicateFilter:
    """历史重复过滤器
    
    用于检测候选号码与历史开奖号码的重复程度，
    避免推荐与历史过于相似的号码组合。
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        'ssq': {
            'max_red_overlap': 4,       # 红球最多重复4个（共6个）
            'exact_match_reject': True, # 完全匹配直接拒绝
            'recent_strict_periods': 10, # 最近10期使用更严格的检查
            'recent_max_overlap': 3,    # 最近10期红球最多重复3个
            'check_periods': 100,       # 检查最近100期
            'enable_blue_check': False, # 蓝球重复不单独检查（因为只有1个）
        },
        'dlt': {
            'max_front_overlap': 3,     # 前区最多重复3个（共5个）
            'max_back_overlap': 2,      # 后区最多重复2个（共2个，即不检查）
            'exact_match_reject': True,
            'recent_strict_periods': 10,
            'recent_max_overlap': 2,    # 最近10期前区最多重复2个
            'check_periods': 100,
        }
    }
    
    def __init__(self, lottery_type: str, config: Optional[Dict] = None):
        """
        初始化过滤器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
            config: 自定义配置（可选）
        """
        self.lottery_type = lottery_type.lower()
        if self.lottery_type not in ('ssq', 'dlt'):
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
        
        # 合并配置
        self.config = self.DEFAULT_CONFIG[self.lottery_type].copy()
        if config:
            self.config.update(config)
    
    def update_config(self, **kwargs):
        """更新配置"""
        self.config.update(kwargs)
    
    def filter(self, candidate: Union[SSQNumber, DLTNumber], 
               history_data: Union[pd.DataFrame, List[Dict]],
               check_periods: Optional[int] = None) -> FilterResult:
        """
        过滤候选号码
        
        Args:
            candidate: 候选号码
            history_data: 历史开奖数据（DataFrame或字典列表）
            check_periods: 检查期数（覆盖默认配置）
            
        Returns:
            FilterResult: 过滤结果
        """
        periods = check_periods or self.config['check_periods']
        
        # 转换历史数据为统一格式
        records = self._convert_history_data(history_data, periods)
        
        if not records:
            return FilterResult(
                is_valid=True,
                overlap_score=0.0,
                max_overlap=0,
                overlap_period=None,
                reason=None
            )
        
        max_overlap = 0
        overlap_period = None
        total_overlap_score = 0.0
        
        for i, record in enumerate(records):
            overlap = self._calculate_overlap(candidate, record)
            
            # 1. 完全匹配检查
            if self.config['exact_match_reject'] and self._is_exact_match(candidate, record):
                return FilterResult(
                    is_valid=False,
                    overlap_score=100.0,
                    max_overlap=overlap,
                    overlap_period=record.get('period', f'第{i+1}期'),
                    reason=f"与{record.get('period', f'第{i+1}期')}完全相同"
                )
            
            # 2. 更新最大重复
            if overlap > max_overlap:
                max_overlap = overlap
                overlap_period = record.get('period', f'第{i+1}期')
            
            # 3. 计算加权重复分数（近期权重更高）
            weight = 1.0 / (i + 1)
            total_overlap_score += overlap * weight
            
            # 4. 近期严格检查
            if i < self.config['recent_strict_periods']:
                if overlap > self.config['recent_max_overlap']:
                    return FilterResult(
                        is_valid=False,
                        overlap_score=total_overlap_score,
                        max_overlap=overlap,
                        overlap_period=record.get('period', f'第{i+1}期'),
                        reason=f"与近期{record.get('period', f'第{i+1}期')}重复{overlap}个号码"
                    )
        
        # 5. 全局最大重复检查
        max_allowed = self._get_max_allowed_overlap()
        if max_overlap > max_allowed:
            return FilterResult(
                is_valid=False,
                overlap_score=total_overlap_score,
                max_overlap=max_overlap,
                overlap_period=overlap_period,
                reason=f"与{overlap_period}重复{max_overlap}个，超过阈值{max_allowed}"
            )
        
        return FilterResult(
            is_valid=True,
            overlap_score=total_overlap_score,
            max_overlap=max_overlap,
            overlap_period=overlap_period,
            reason=None
        )

    def filter_batch(self, candidates: List[Union[SSQNumber, DLTNumber]],
                     history_data: Union[pd.DataFrame, List[Dict]],
                     check_periods: Optional[int] = None) -> List[tuple]:
        """
        批量过滤候选号码

        Args:
            candidates: 候选号码列表
            history_data: 历史开奖数据
            check_periods: 检查期数

        Returns:
            List[tuple]: (候选号码, 过滤结果) 的列表，按重复度排序
        """
        results = []
        for candidate in candidates:
            result = self.filter(candidate, history_data, check_periods)
            results.append((candidate, result))

        # 按重复度评分排序（越低越好）
        results.sort(key=lambda x: x[1].overlap_score)
        return results

    def filter_and_select(self, candidates: List[Union[SSQNumber, DLTNumber]],
                          history_data: Union[pd.DataFrame, List[Dict]],
                          count: int,
                          check_periods: Optional[int] = None) -> List[Union[SSQNumber, DLTNumber]]:
        """
        过滤并选择最佳候选号码

        Args:
            candidates: 候选号码列表
            history_data: 历史开奖数据
            count: 需要选择的数量
            check_periods: 检查期数

        Returns:
            List: 通过过滤的最佳号码列表
        """
        results = self.filter_batch(candidates, history_data, check_periods)

        # 选择通过过滤的号码
        valid_numbers = [num for num, result in results if result.is_valid]

        return valid_numbers[:count]

    def _get_max_allowed_overlap(self) -> int:
        """获取允许的最大重复数"""
        if self.lottery_type == 'ssq':
            return self.config.get('max_red_overlap', 4)
        else:
            return self.config.get('max_front_overlap', 3)

    def _convert_history_data(self, history_data: Union[pd.DataFrame, List[Dict]],
                              periods: int) -> List[Dict]:
        """将历史数据转换为统一格式"""
        if isinstance(history_data, pd.DataFrame):
            # DataFrame 格式
            records = []
            for i, row in history_data.head(periods).iterrows():
                record = {'period': row.get('period', row.get('draw_number', str(i)))}

                if self.lottery_type == 'ssq':
                    # 处理红球
                    if 'red_numbers' in row:
                        red = row['red_numbers']
                        if isinstance(red, str):
                            record['red_numbers'] = [int(x) for x in red.split(',')]
                        else:
                            record['red_numbers'] = list(red)
                    else:
                        # 尝试从单独列获取
                        red_cols = [col for col in row.index if col.startswith('red_')]
                        if red_cols:
                            record['red_numbers'] = [int(row[col]) for col in sorted(red_cols)]

                    # 处理蓝球
                    if 'blue_number' in row:
                        record['blue_number'] = int(row['blue_number'])
                    elif 'blue' in row:
                        record['blue_number'] = int(row['blue'])
                else:
                    # 处理前区
                    if 'front_numbers' in row:
                        front = row['front_numbers']
                        if isinstance(front, str):
                            record['front_numbers'] = [int(x) for x in front.split(',')]
                        else:
                            record['front_numbers'] = list(front)
                    else:
                        front_cols = [col for col in row.index if col.startswith('front_')]
                        if front_cols:
                            record['front_numbers'] = [int(row[col]) for col in sorted(front_cols)]

                    # 处理后区
                    if 'back_numbers' in row:
                        back = row['back_numbers']
                        if isinstance(back, str):
                            record['back_numbers'] = [int(x) for x in back.split(',')]
                        else:
                            record['back_numbers'] = list(back)
                    else:
                        back_cols = [col for col in row.index if col.startswith('back_')]
                        if back_cols:
                            record['back_numbers'] = [int(row[col]) for col in sorted(back_cols)]

                records.append(record)
            return records
        else:
            # 列表格式，直接截取
            return history_data[:periods]

    def _calculate_overlap(self, candidate: Union[SSQNumber, DLTNumber],
                          record: Dict) -> int:
        """计算主区号码重复数量"""
        if self.lottery_type == 'ssq':
            candidate_red = set(candidate.red)
            history_red = set(record.get('red_numbers', []))
            return len(candidate_red & history_red)
        else:
            candidate_front = set(candidate.front)
            history_front = set(record.get('front_numbers', []))
            return len(candidate_front & history_front)

    def _is_exact_match(self, candidate: Union[SSQNumber, DLTNumber],
                        record: Dict) -> bool:
        """检查是否完全匹配"""
        if self.lottery_type == 'ssq':
            history_red = record.get('red_numbers', [])
            history_blue = record.get('blue_number')
            return (sorted(candidate.red) == sorted(history_red)
                    and candidate.blue == history_blue)
        else:
            history_front = record.get('front_numbers', [])
            history_back = record.get('back_numbers', [])
            return (sorted(candidate.front) == sorted(history_front)
                    and sorted(candidate.back) == sorted(history_back))

    def get_overlap_stats(self, candidate: Union[SSQNumber, DLTNumber],
                          history_data: Union[pd.DataFrame, List[Dict]],
                          check_periods: Optional[int] = None) -> Dict[str, Any]:
        """
        获取详细的重复统计信息

        Args:
            candidate: 候选号码
            history_data: 历史数据
            check_periods: 检查期数

        Returns:
            Dict: 详细统计信息
        """
        periods = check_periods or self.config['check_periods']
        records = self._convert_history_data(history_data, periods)

        overlap_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        overlap_details = []

        for i, record in enumerate(records):
            overlap = self._calculate_overlap(candidate, record)
            if overlap in overlap_distribution:
                overlap_distribution[overlap] += 1

            if overlap >= 3:  # 只记录重复3个及以上的
                overlap_details.append({
                    'period': record.get('period', f'第{i+1}期'),
                    'overlap_count': overlap,
                    'position': i + 1
                })

        return {
            'distribution': overlap_distribution,
            'high_overlap_periods': overlap_details,
            'total_checked': len(records),
            'avg_overlap': sum(k * v for k, v in overlap_distribution.items()) / max(len(records), 1)
        }

