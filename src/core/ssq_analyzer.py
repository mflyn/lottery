#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
双色球数据分析模块
"""

from typing import List, Dict, Optional, Any
from collections import Counter
import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from enum import Enum
import logging
import itertools
import random
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    VotingClassifier
)
from sklearn.neural_network import MLPClassifier
from scipy import stats
from .features.data_exploration import DataExplorationAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/ssq_analyzer.log'
)
logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """错误代码枚举"""
    SUCCESS = 0
    NETWORK_ERROR = 1001
    DATA_FORMAT_ERROR = 1002
    VALIDATION_ERROR = 1003
    CACHE_ERROR = 1004
    ANALYSIS_ERROR = 1005
    UNEXPECTED_ERROR = 9999

class SSQError:
    """统一错误信息格式"""
    def __init__(self, code: ErrorCode, message: str, details: Any = None):
        self.code = code
        self.message = message
        self.details = details
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        return {
            'code': self.code.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }

class SSQResult:
    """统一返回结果格式"""
    def __init__(self, success: bool, data: Any = None, error: SSQError = None):
        self.success = success
        self.data = data
        self.error = error
        
    def to_dict(self) -> Dict:
        result = {'success': self.success}
        if self.data is not None:
            result['data'] = self.data
        if self.error is not None:
            result['error'] = self.error.to_dict()
        return result

class SSQAnalysisError(Exception):
    """双色球分析错误基类"""
    pass

class DataFetchError(SSQAnalysisError):
    """数据获取错误"""
    pass

class DataParseError(SSQAnalysisError):
    """数据解析错误"""
    pass

class CacheError(SSQAnalysisError):
    """缓存操作错误"""
    pass

class ValidationError(SSQAnalysisError):
    """数据验证错误"""
    pass

class SSQDataFetcher:
    """双色球数据获取类"""
    
    def __init__(self):
        self.base_url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        self.cache_file = "data/ssq_history.json"
        self.cache_expire_hours = 24
        
    def fetch_history(self, count: int = 50) -> List[Dict]:
        """获取历史开奖数据
        
        Args:
            count: 获取的期数
            
        Returns:
            历史开奖数据列表
            
        Raises:
            DataFetchError: 网络请求失败
            DataParseError: 数据解析失败
            CacheError: 缓存操作失败
        """
        try:
            # 参数验证
            if not isinstance(count, int) or count <= 0:
                raise ValidationError("count参数必须为正整数")
                
            # 先尝试从缓存读取
            try:
                cached_data = self._read_cache()
                if cached_data:
                    return cached_data[:count]
            except CacheError as e:
                print(f"读取缓存失败: {e}")
            
            # 从网络获取数据
            params = {
                'name': 'ssq',
                'pageNo': 1,
                'pageSize': count,
                'systemType': 0
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                raise DataFetchError(f"网络请求失败: {e}")
            except json.JSONDecodeError as e:
                raise DataParseError(f"JSON解析失败: {e}")
                
            # 验证响应数据
            if 'result' not in data:
                raise DataParseError("响应数据格式错误")
                
            result = data['result']
            
            # 写入缓存
            try:
                self._write_cache(result)
            except CacheError as e:
                print(f"写入缓存失败: {e}")
            
            return result
            
        except SSQAnalysisError:
            raise
        except Exception as e:
            raise DataFetchError(f"获取数据时发生未知错误: {e}")
            
    def _read_cache(self) -> Optional[List[Dict]]:
        """读取缓存数据
        
        Raises:
            CacheError: 缓存操作失败
        """
        try:
            if not os.path.exists(self.cache_file):
                return None
                
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                
            # 验证缓存数据格式
            if not isinstance(cache, dict) or 'timestamp' not in cache or 'data' not in cache:
                raise CacheError("缓存数据格式错误")
                
            # 检查缓存是否过期
            try:
                cache_time = datetime.fromisoformat(cache['timestamp'])
                if datetime.now() - cache_time > timedelta(hours=self.cache_expire_hours):
                    return None
            except ValueError as e:
                raise CacheError(f"缓存时间戳格式错误: {e}")
                
            return cache['data']
            
        except json.JSONDecodeError as e:
            raise CacheError(f"缓存文件JSON解析失败: {e}")
        except Exception as e:
            raise CacheError(f"读取缓存时发生错误: {e}")
            
    def _write_cache(self, data: List[Dict]):
        """写入缓存数据
        
        Args:
            data: 要缓存的数据
            
        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 确保缓存目录存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
                
        except Exception as e:
            raise CacheError(f"写入缓存时发生错误: {e}")

class SSQAnalyzer:
    """双色球数据分析类"""
    
    def __init__(self, data_fetcher: Optional[SSQDataFetcher] = None, debug_mode: bool = False):
        """初始化分析器
        
        Args:
            data_fetcher: 数据获取器实例
            debug_mode: 是否启用调试模式
        """
        self.data_fetcher = data_fetcher or SSQDataFetcher()
        self.debug_mode = debug_mode
        self.plot_style = {
            'figure.figsize': (12, 8),
            'font.sans-serif': ['SimHei'],  # 支持中文显示
            'axes.unicode_minus': False
        }
        self.models = {
            'random_forest': RandomForestClassifier(),
            'gradient_boost': GradientBoostingClassifier(),
            'neural_network': MLPClassifier(),
            'ensemble': VotingClassifier([
                ('rf', RandomForestClassifier()),
                ('gb', GradientBoostingClassifier()),
                ('nn', MLPClassifier())
            ])
        }
        self.data_explorer = DataExplorationAnalyzer()
        
    def set_debug(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled
        if enabled:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            
    def analyze_all(self, periods: int = 100) -> SSQResult:
        """执行全面分析
        
        Args:
            periods: 分析的期数
            
        Returns:
            包含所有分析结果的SSQResult对象
        """
        try:
            # 获取历史数据
            fetched_data = self.data_fetcher.fetch_history(periods)
            
            # 执行各项分析
            results = {
                'frequency': self.analyze_frequency(fetched_data),
                'hot_cold': self.analyze_hot_cold_numbers(fetched_data),
                'missing': self.analyze_missing_numbers(fetched_data),
                'trends': self.analyze_trends(fetched_data),
                'combinations': self.analyze_combinations(fetched_data),
                'exploration': self.explore_data(fetched_data),  # 新增数据探索结果
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'periods_analyzed': periods
                }
            }
            
            return SSQResult(success=True, data=results)
            
        except Exception as e:
            error = SSQError(
                code=ErrorCode.ANALYSIS_ERROR,
                message="分析过程发生错误",
                details=str(e)
            )
            return SSQResult(success=False, error=error)
            
    def analyze_frequency(self, data: List[Dict]) -> Dict:
        """分析号码出现频率
        
        Args:
            data: 历史开奖数据
            
        Returns:
            频率分析结果
        """
        red_counts = Counter()
        blue_counts = Counter()
        total_draws = len(data)
        
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            blue_number = int(draw['blue'])
            
            red_counts.update(red_numbers)
            blue_counts.update([blue_number])
            
        # 计算频率
        red_freq = {num: count/total_draws for num, count in red_counts.items()}
        blue_freq = {num: count/total_draws for num, count in blue_counts.items()}
        
        return {
            'red_frequency': red_freq,
            'blue_frequency': blue_freq,
            'total_draws': total_draws
        }
        
    def analyze_hot_cold_numbers(self, data: List[Dict], recent_draws: int = 30) -> Dict:
        """分析热门和冷门号码
        
        Args:
            data: 历史开奖数据
            recent_draws: 最近几期作为参考
            
        Returns:
            热冷号分析结果
        """
        recent_data = data[:recent_draws]
        red_counts = Counter()
        blue_counts = Counter()
        
        for draw in recent_data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            blue_number = int(draw['blue'])
            red_counts.update(red_numbers)
            blue_counts.update([blue_number])
            
        # 定义热冷标准
        def get_temperature(count: int) -> str:
            if count >= recent_draws * 0.2:  # 出现率超过20%为热号
                return 'hot'
            elif count <= recent_draws * 0.05:  # 出现率低于5%为冷号
                return 'cold'
            return 'normal'
            
        red_temperature = {num: get_temperature(count) for num, count in red_counts.items()}
        blue_temperature = {num: get_temperature(count) for num, count in blue_counts.items()}
        
        return {
            'red_temperature': red_temperature,
            'blue_temperature': blue_temperature,
            'reference_draws': recent_draws
        }
        
    def analyze_missing_numbers(self, data: List[Dict]) -> Dict:
        """分析号码遗漏值
        
        Args:
            data: 历史开奖数据
            
        Returns:
            遗漏值分析结果
        """
        red_missing = {i: 0 for i in range(1, 34)}
        blue_missing = {i: 0 for i in range(1, 17)}
        
        # 计算当前遗漏值
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            blue_number = int(draw['blue'])
            
            # 更新红球遗漏值
            for num in red_missing:
                if num in red_numbers:
                    red_missing[num] = 0
                else:
                    red_missing[num] += 1
                    
            # 更新蓝球遗漏值
            for num in blue_missing:
                if num == blue_number:
                    blue_missing[num] = 0
                else:
                    blue_missing[num] += 1
                    
        return {
            'red_missing': red_missing,
            'blue_missing': blue_missing
        }

    def analyze_trends(self, data: List[Dict], window_size: int = 10) -> Dict:
        """分析号码走势
        
        Args:
            data: 历史开奖数据
            window_size: 移动平均窗口大小
            
        Returns:
            走势分析结果
        """
        try:
            df = pd.DataFrame(data)
            
            # 转换号码列
            df['red_numbers'] = df['red'].apply(lambda x: [int(n) for n in x.split(',')])
            df['blue_number'] = df['blue'].astype(int)
            
            # 计算移动平均
            red_means = []
            blue_means = []
            
            for i in range(len(df) - window_size + 1):
                window = df.iloc[i:i+window_size]
                red_mean = sum(sum(nums) for nums in window['red_numbers']) / (window_size * 6)
                blue_mean = window['blue_number'].mean()
                red_means.append(red_mean)
                blue_means.append(blue_mean)
                
            return {
                'trends': {
                    'red_moving_avg': red_means,
                    'blue_moving_avg': blue_means,
                    'window_size': window_size
                }
            }
            
        except Exception as e:
            if self.debug_mode:
                logger.exception("走势分析失败")
            raise SSQAnalysisError("走势分析失败") from e

    def analyze_combinations(self, data: List[Dict], top_n: int = 10) -> Dict:
        """分析号码组合特征
        
        Args:
            data: 历史开奖数据
            top_n: 返回前N个最常见组合
            
        Returns:
            组合分析结果
        """
        try:
            combinations_data = {
                'sum_distribution': self._analyze_sum_distribution(data),
                'odd_even_ratio': self._analyze_odd_even_ratio(data),
                'span_analysis': self._analyze_number_span(data),
                'consecutive_numbers': self._analyze_consecutive_numbers(data),
                'common_pairs': self._find_common_pairs(data, top_n),
                'zone_distribution': self._analyze_zone_distribution(data)
            }
            
            return combinations_data
            
        except Exception as e:
            if self.debug_mode:
                logger.exception("组合分析失败")
            raise SSQAnalysisError("组合分析失败") from e

    def _analyze_sum_distribution(self, data: List[Dict]) -> Dict:
        """分析号码和值分布"""
        red_sums = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            red_sums.append(sum(red_numbers))
            
        return {
            'min_sum': min(red_sums),
            'max_sum': max(red_sums),
            'avg_sum': sum(red_sums) / len(red_sums),
            'most_common_sums': Counter(red_sums).most_common(5)
        }

    def _analyze_odd_even_ratio(self, data: List[Dict]) -> Dict:
        """分析奇偶比例"""
        ratios = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            odd_count = sum(1 for x in red_numbers if x % 2 == 1)
            even_count = len(red_numbers) - odd_count
            ratios.append(f"{odd_count}:{even_count}")
            
        return {
            'ratio_distribution': Counter(ratios).most_common(),
            'most_common_ratio': Counter(ratios).most_common(1)[0]
        }

    def _analyze_number_span(self, data: List[Dict]) -> Dict:
        """分析号码跨度"""
        spans = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            span = max(red_numbers) - min(red_numbers)
            spans.append(span)
            
        return {
            'min_span': min(spans),
            'max_span': max(spans),
            'avg_span': sum(spans) / len(spans),
            'common_spans': Counter(spans).most_common(5)
        }

    def _analyze_consecutive_numbers(self, data: List[Dict]) -> Dict:
        """分析连号情况"""
        consecutive_stats = []
        
        for draw in data:
            red_numbers = sorted([int(x) for x in draw['red'].split(',')])
            consecutive_count = 0
            max_consecutive = 0
            
            for i in range(len(red_numbers) - 1):
                if red_numbers[i + 1] - red_numbers[i] == 1:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
                    
            consecutive_stats.append(max_consecutive)
            
        return {
            'consecutive_distribution': Counter(consecutive_stats).most_common(),
            'max_consecutive_found': max(consecutive_stats)
        }

    def _find_common_pairs(self, data: List[Dict], top_n: int) -> Dict:
        """查找常见号码对"""
        red_pairs = Counter()
        blue_repeats = Counter()
        
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            blue_number = int(draw['blue'])
            
            # 统计红球号码对
            for pair in itertools.combinations(sorted(red_numbers), 2):
                red_pairs[pair] += 1
                
            # 统计蓝球重复
            blue_repeats[blue_number] += 1
            
        return {
            'common_red_pairs': red_pairs.most_common(top_n),
            'common_blue_numbers': blue_repeats.most_common(top_n)
        }

    def _analyze_zone_distribution(self, data: List[Dict]) -> Dict:
        """分析号码区间分布"""
        zones = {
            'low': (1, 11),
            'mid': (12, 22),
            'high': (23, 33)
        }
        
        zone_stats = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            zone_count = {'low': 0, 'mid': 0, 'high': 0}
            
            for num in red_numbers:
                for zone, (start, end) in zones.items():
                    if start <= num <= end:
                        zone_count[zone] += 1
                        break
                        
            zone_stats.append(tuple(zone_count.values()))
            
        return {
            'zone_distribution': Counter(zone_stats).most_common(),
            'zones_defined': zones
        }

    def generate_smart_numbers(self, count: int = 5) -> List[Dict]:
        """基于分析结果智能生成号码
        
        Args:
            count: 生成号码组数
            
        Returns:
            生成的号码列表
        """
        try:
            # 获取最近100期数据进行分析
            
            # 进行全面分析
            analysis = self.analyze_all(100).data
            
            generated_numbers = []
            for _ in range(count):
                # 根据分析结果生成符合规律的号码
                red_numbers = self._generate_red_numbers(analysis)
                blue_number = self._generate_blue_number(analysis)
                
                generated_numbers.append({
                    'red': sorted(red_numbers),
                    'blue': blue_number
                })
                
            return generated_numbers
            
        except Exception as e:
            if self.debug_mode:
                logger.exception("智能生成号码失败")
            raise SSQAnalysisError("智能生成号码失败") from e

    def _generate_red_numbers(self, analysis: Dict) -> List[int]:
        """根据分析结果生成红球号码"""
        # 获取热门号码
        hot_numbers = [num for num, temp in analysis['hot_cold']['red_temperature'].items() 
                      if temp == 'hot']
        # 获取最长遗漏号码
        missing_numbers = sorted(analysis['missing']['red_missing'].items(), 
                               key=lambda x: x[1], reverse=True)[:3]
        
        # 综合考虑各种因素生成号码
        selected = []
        # 从热门号码中选择2-3个
        selected.extend(random.sample(hot_numbers, random.randint(2, 3)))
        # 从遗漏号码中选择1-2个
        selected.extend(num for num, _ in random.sample(missing_numbers, random.randint(1, 2)))
        # 剩余号码随机选择
        remaining = list(set(range(1, 34)) - set(selected))
        selected.extend(random.sample(remaining, 6 - len(selected)))
        
        return selected

    def _generate_blue_number(self, analysis: Dict) -> int:
        """根据分析结果生成蓝球号码"""
        # 获取热门蓝球
        hot_blue = [num for num, temp in analysis['hot_cold']['blue_temperature'].items() 
                   if temp == 'hot']
        # 获取最长遗漏的蓝球
        missing_blue = sorted(analysis['missing']['blue_missing'].items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        
        # 70%概率选择热门号码，30%概率选择遗漏号码
        if random.random() < 0.7 and hot_blue:
            return random.choice(hot_blue)
        else:
            return random.choice([num for num, _ in missing_blue])

    def export_analysis_report(self, data: Dict, format: str = 'json') -> str:
        """导出分析报告
        
        Args:
            data: 分析数据
            format: 导出格式 ('json' 或 'text')
            
        Returns:
            格式化的报告内容
        """
        if format == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == 'text':
            report = []
            report.append("双色球数据分析报告")
            report.append("=" * 30)
            
            # 添加频率分析结果
            if 'frequency' in data:
                report.append("\n号码出现频率:")
                report.append("-" * 20)
                report.append("红球频率:")
                for num, freq in sorted(data['frequency']['red_frequency'].items()):
                    report.append(f"  {num:02d}: {freq:.3f}")
                report.append("\n蓝球频率:")
                for num, freq in sorted(data['frequency']['blue_frequency'].items()):
                    report.append(f"  {num:02d}: {freq:.3f}")
                    
            # 添加其他分析结果...
            
            return "\n".join(report)
        else:
            raise ValueError("不支持的导出格式")

    def create_visualization(self, data: Dict, save_dir: str = "reports/figures") -> Dict[str, str]:
        """创建数据可视化图表
        
        Args:
            data: 分析数据
            save_dir: 图表保存目录
            
        Returns:
            Dict[str, str]: 图表文件路径字典
        """
        try:
            # 确保保存目录存在
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 设置绘图样式
            plt.style.use('seaborn')
            plt.rcParams.update(self.plot_style)
            
            figure_paths = {}
            
            # 1. 红球频率分布图
            figure_paths['red_frequency'] = self._plot_number_frequency(
                data['frequency']['red_frequency'],
                '红球出现频率分布',
                save_path / 'red_frequency.png'
            )
            
            # 2. 蓝球频率分布图
            figure_paths['blue_frequency'] = self._plot_number_frequency(
                data['frequency']['blue_frequency'],
                '蓝球出现频率分布',
                save_path / 'blue_frequency.png'
            )
            
            # 3. 热门号码走势图
            figure_paths['hot_numbers'] = self._plot_hot_numbers_trend(
                data['trends']['red_trends'],
                save_path / 'hot_numbers_trend.png'
            )
            
            # 4. 奇偶比例饼图
            figure_paths['odd_even_ratio'] = self._plot_odd_even_ratio(
                data['combinations']['odd_even_ratio'],
                save_path / 'odd_even_ratio.png'
            )
            
            # 5. 区间分布热力图
            figure_paths['zone_heatmap'] = self._plot_zone_distribution(
                data['combinations']['zone_distribution'],
                save_path / 'zone_heatmap.png'
            )
            
            return figure_paths
            
        except Exception as e:
            if self.debug_mode:
                logger.exception("创建可视化图表失败")
            raise SSQAnalysisError("创建可视化图表失败") from e

    def _plot_number_frequency(self, frequency_data: Dict, title: str, save_path: Path) -> str:
        """绘制号码频率分布图"""
        plt.figure()
        
        numbers = list(frequency_data.keys())
        frequencies = list(frequency_data.values())
        
        plt.bar(numbers, frequencies, color='royalblue')
        plt.title(title)
        plt.xlabel('号码')
        plt.ylabel('出现频率')
        plt.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, v in enumerate(frequencies):
            plt.text(numbers[i], v, f'{v:.3f}', ha='center', va='bottom')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(save_path)

    def _plot_hot_numbers_trend(self, trend_data: Dict, save_path: Path) -> str:
        """绘制热门号码走势图"""
        plt.figure()
        
        # 选择最近10期的数据
        periods = list(trend_data.keys())[-10:]
        hot_numbers = []
        for period in periods:
            hot_numbers.append([num for num, count in trend_data[period].items() if count > 0])
        
        # 创建热力图数据
        heatmap_data = np.zeros((33, len(periods)))
        for i, period_numbers in enumerate(hot_numbers):
            for num in period_numbers:
                heatmap_data[num-1][i] = 1
        
        sns.heatmap(heatmap_data, cmap='YlOrRd', cbar_kws={'label': '出现次数'})
        plt.title('最近10期热门号码走势')
        plt.xlabel('期号')
        plt.ylabel('号码')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(save_path)

    def _plot_odd_even_ratio(self, ratio_data: Dict, save_path: Path) -> str:
        """绘制奇偶比例饼图"""
        plt.figure()
        
        ratios = ratio_data['ratio_distribution']
        labels = [f'{ratio[0]} ({ratio[1]}次)' for ratio in ratios]
        sizes = [ratio[1] for ratio in ratios]
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('红球奇偶比例分布')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(save_path)

    def _plot_zone_distribution(self, zone_data: Dict, save_path: Path) -> str:
        """绘制区间分布热力图"""
        plt.figure()
        
        distribution = zone_data['zone_distribution']
        matrix = np.zeros((3, 3))  # 3个区间
        
        for pattern, count in distribution:
            low, mid, high = pattern
            matrix[0][low] = count
            matrix[1][mid] = count
            matrix[2][high] = count
        
        sns.heatmap(matrix, annot=True, fmt='g', cmap='YlOrRd',
                   xticklabels=['低区', '中区', '高区'],
                   yticklabels=['0球', '1球', '2球'])
        plt.title('号码区间分布热力图')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(save_path)

    def analyze_winning_patterns(self, data: List[Dict]) -> Dict:
        """分析中奖号码模式
        
        Args:
            data: 历史开奖数据
            
        Returns:
            中奖号码模式分析结果
        """
        try:
            patterns = {
                'sum_range': self._analyze_winning_sum_range(data),
                'consecutive_patterns': self._analyze_consecutive_patterns(data),
                'repeat_patterns': self._analyze_repeat_patterns(data),
                'prime_composite_ratio': self._analyze_prime_composite_ratio(data)
            }
            
            return patterns
            
        except Exception as e:
            if self.debug_mode:
                logger.exception("中奖模式分析失败")
            raise SSQAnalysisError("中奖模式分析失败") from e

    def _analyze_winning_sum_range(self, data: List[Dict]) -> Dict:
        """分析中奖号码和值范围"""
        sums = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            sums.append(sum(red_numbers))
            
        return {
            'min_sum': min(sums),
            'max_sum': max(sums),
            'avg_sum': sum(sums) / len(sums),
            'most_common_range': f"{np.percentile(sums, 25):.0f}-{np.percentile(sums, 75):.0f}"
        }

    def _analyze_consecutive_patterns(self, data: List[Dict]) -> Dict:
        """分析连号模式"""
        patterns = []
        for draw in data:
            red_numbers = sorted([int(x) for x in draw['red'].split(',')])
            pattern = []
            consecutive_count = 1
            
            for i in range(1, len(red_numbers)):
                if red_numbers[i] - red_numbers[i-1] == 1:
                    consecutive_count += 1
                else:
                    if consecutive_count > 1:
                        pattern.append(consecutive_count)
                    consecutive_count = 1
                    
            if consecutive_count > 1:
                pattern.append(consecutive_count)
                
            patterns.append(tuple(sorted(pattern)) if pattern else (0,))
            
        return {
            'pattern_distribution': Counter(patterns).most_common(),
            'most_common_pattern': Counter(patterns).most_common(1)[0]
        }

    def _analyze_repeat_patterns(self, data: List[Dict]) -> Dict:
        """分析重复号码模式"""
        repeat_patterns = []
        for i in range(len(data)-1):
            current = set([int(x) for x in data[i]['red'].split(',')])
            next_draw = set([int(x) for x in data[i+1]['red'].split(',')])
            repeat_count = len(current & next_draw)
            repeat_patterns.append(repeat_count)
            
        return {
            'repeat_distribution': Counter(repeat_patterns).most_common(),
            'avg_repeat_count': sum(repeat_patterns) / len(repeat_patterns)
        }

    def _analyze_prime_composite_ratio(self, data: List[Dict]) -> Dict:
        """分析质数和合数比例"""
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True
            
        ratios = []
        for draw in data:
            red_numbers = [int(x) for x in draw['red'].split(',')]
            prime_count = sum(1 for x in red_numbers if is_prime(x))
            composite_count = len(red_numbers) - prime_count
            ratios.append(f"{prime_count}:{composite_count}")
            
        return {
            'ratio_distribution': Counter(ratios).most_common(),
            'most_common_ratio': Counter(ratios).most_common(1)[0]
        }

    def extract_advanced_features(self, data: List[Dict]) -> Dict:
        """实现更复杂的特征工程
    
        Args:
            data: 历史开奖数据列表
        
        Returns:
            Dict: 包含多个维度特征的字典
        """
        features = {
            'number_patterns': self._analyze_number_patterns(data),
            'temporal_features': self._extract_temporal_features(data),
            'statistical_moments': self._calculate_statistical_moments(data),
            'frequency_domain': self._analyze_frequency_domain(data)
        }
        return features

    def _analyze_number_patterns(self, data: List[Dict]) -> Dict:
        """分析号码模式特征
    
        包括：连号、重号、间隔、奇偶、大小等模式
        """
        patterns = {
            'consecutive': [],  # 连号
            'repeats': [],     # 重号
            'gaps': [],        # 间隔
            'odd_even': [],    # 奇偶
            'high_low': []     # 大小
        }
        
        for draw in data:
            red_numbers = sorted([int(x) for x in draw['red'].split(',')])
            
            # 分析连号
            consecutive_count = 0
            for i in range(1, len(red_numbers)):
                if red_numbers[i] - red_numbers[i-1] == 1:
                    consecutive_count += 1
            patterns['consecutive'].append(consecutive_count)
            
            # 分析重号（与上一期比较）
            if len(patterns['repeats']) > 0:
                prev_numbers = set([int(x) for x in data[data.index(draw)-1]['red'].split(',')])
                current_numbers = set(red_numbers)
                repeat_count = len(current_numbers & prev_numbers)
                patterns['repeats'].append(repeat_count)
            else:
                patterns['repeats'].append(0)
                
            # 分析间隔
            gaps = [red_numbers[i] - red_numbers[i-1] for i in range(1, len(red_numbers))]
            patterns['gaps'].append(sum(gaps) / len(gaps))
            
            # 分析奇偶
            odd_count = sum(1 for x in red_numbers if x % 2 == 1)
            patterns['odd_even'].append(odd_count)
            
            # 分析大小（以17为分界）
            high_count = sum(1 for x in red_numbers if x > 17)
            patterns['high_low'].append(high_count)
        
        return patterns

    def _extract_temporal_features(self, data: List[Dict]) -> Dict:
        """提取时间相关特征
    
        包括：周期性、季节性、趋势等
        """
        temporal = {
            'weekday': [],     # 开奖日期的星期几
            'month': [],       # 开奖月份
            'season': [],      # 季节
            'year_week': []    # 一年中的第几周
        }
        
        for draw in data:
            draw_date = datetime.strptime(draw['date'], '%Y-%m-%d')
            
            temporal['weekday'].append(draw_date.weekday())
            temporal['month'].append(draw_date.month)
            temporal['season'].append((draw_date.month - 1) // 3 + 1)
            temporal['year_week'].append(draw_date.isocalendar()[1])
        
        return temporal

    def _calculate_statistical_moments(self, data: List[Dict]) -> Dict:
        """计算统计矩特征
    
        包括：均值、方差、偏度、峰度等
        """
        moments = {
            'mean': [],        # 均值
            'variance': [],    # 方差
            'skewness': [],    # 偏度
            'kurtosis': []     # 峰度
        }
        
        for draw in data:
            numbers = [int(x) for x in draw['red'].split(',')]
            
            # 计算统计矩
            mean = np.mean(numbers)
            variance = np.var(numbers)
            skewness = stats.skew(numbers)
            kurtosis = stats.kurtosis(numbers)
            
            moments['mean'].append(mean)
            moments['variance'].append(variance)
            moments['skewness'].append(skewness)
            moments['kurtosis'].append(kurtosis)
        
        return moments

    def _analyze_frequency_domain(self, data: List[Dict]) -> Dict:
        """分析频域特征
    
        使用傅里叶变换分析号码的周期性特征
        """
        frequency = {
            'red_fft': [],     # 红球频谱
            'blue_fft': [],    # 蓝球频谱
            'dominant_freq': [] # 主导频率
        }
        
        # 准备数据
        red_numbers = np.array([[int(x) for x in draw['red'].split(',')] for draw in data])
        blue_numbers = np.array([int(draw['blue']) for draw in data])
        
        # 对每个位置的红球进行FFT分析
        for pos in range(6):
            fft_result = np.fft.fft(red_numbers[:, pos])
            frequency['red_fft'].append(np.abs(fft_result))
            
        # 对蓝球进行FFT分析
        blue_fft = np.fft.fft(blue_numbers)
        frequency['blue_fft'] = np.abs(blue_fft)
        
        # 找出主导频率
        for fft_result in frequency['red_fft']:
            dominant = np.argmax(np.abs(fft_result[1:])) + 1  # 跳过直流分量
            frequency['dominant_freq'].append(dominant)
        
        return frequency

    def optimize_prediction_model(self):
        """优化预测模型性能"""
        # 添加模型性能优化逻辑
        self.hyperparameter_tuning()
        self.feature_selection()
        self.cross_validation()
        self.model_evaluation()

    def explore_data(self, data: pd.DataFrame,
                    date_range: tuple = None,
                    number_range: tuple = None) -> Dict[str, Any]:
        """执行数据探索分析"""
        return self.data_explorer.analyze_distribution(
            data,
            date_range=date_range,
            number_range=number_range
        )
