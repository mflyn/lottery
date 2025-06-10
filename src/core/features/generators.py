from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class FeatureGenerator:
    """特征生成器类"""
    
    def __init__(self, lottery_type: str):
        """初始化特征生成器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')
        """
        if lottery_type not in ['ssq', 'dlt']:
            raise ValueError("彩票类型必须是 'ssq' 或 'dlt'")
            
        self.lottery_type = lottery_type
        self.logger = logging.getLogger(__name__)
        
        # 定义支持的特征类型
        self.feature_types = {
            'basic': self._generate_basic_features,
            'statistical': self._generate_statistical_features,
            'temporal': self._generate_temporal_features,
            'pattern': self._generate_pattern_features,
            'combination': self._generate_combination_features
        }
        
        # 设置彩票相关参数
        if lottery_type == 'ssq':
            self.red_columns = [f'red_{i}' for i in range(1, 7)]
            self.blue_columns = ['blue']
            self.red_range = (1, 33)
            self.blue_range = (1, 16)
        else:  # dlt
            self.red_columns = [f'front_{i}' for i in range(1, 6)]
            self.blue_columns = [f'back_{i}' for i in range(1, 3)]
            self.red_range = (1, 35)
            self.blue_range = (1, 12)
    
    def generate(self, 
                data: pd.DataFrame,
                feature_types: Optional[List[str]] = None) -> pd.DataFrame:
        """生成特征主方法
        
        Args:
            data: 原始数据DataFrame
            feature_types: 要生成的特征类型列表，如果为None则生成所有类型
            
        Returns:
            包含所有生成特征的DataFrame
        """
        if data.empty:
            raise ValueError("输入数据为空")
            
        if feature_types is None:
            feature_types = list(self.feature_types.keys())
            
        # 验证特征类型
        invalid_types = set(feature_types) - set(self.feature_types.keys())
        if invalid_types:
            raise ValueError(f"不支持的特征类型: {invalid_types}")
            
        # 初始化结果DataFrame
        features = pd.DataFrame(index=data.index)
        
        # 生成每种类型的特征
        for feature_type in feature_types:
            try:
                new_features = self.feature_types[feature_type](data)
                features = pd.concat([features, new_features], axis=1)
            except Exception as e:
                self.logger.error(f"生成{feature_type}特征时出错: {str(e)}")
                raise
                
        return features
    
    def _generate_basic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成基础特征
        
        生成的特征包括:
        1. 红球特征:
           - 和值
           - 平均值
           - 标准差
           - 跨度(最大值-最小值)
           - 奇数个数
           - 偶数个数
           - 大数个数(大于一半)
           - 小数个数(小于等于一半)
           
        2. 蓝球特征:
           - 奇偶性
           - 大小性
           - 除3余数
           
        Args:
            data: 原始数据DataFrame
            
        Returns:
            基础特征DataFrame
        """
        features = pd.DataFrame(index=data.index)
        
        # 1. 红球特征
        red_numbers = data[self.red_columns].values
        red_mid = (self.red_range[1] - self.red_range[0]) // 2 + self.red_range[0]
        
        # 计算红球基本统计特征
        features['red_sum'] = red_numbers.sum(axis=1)
        features['red_mean'] = red_numbers.mean(axis=1)
        features['red_std'] = red_numbers.std(axis=1)
        features['red_span'] = red_numbers.max(axis=1) - red_numbers.min(axis=1)
        
        # 计算红球奇偶特征
        features['red_odd_count'] = (red_numbers % 2 == 1).sum(axis=1)
        features['red_even_count'] = (red_numbers % 2 == 0).sum(axis=1)
        
        # 计算红球大小特征
        features['red_big_count'] = (red_numbers > red_mid).sum(axis=1)
        features['red_small_count'] = (red_numbers <= red_mid).sum(axis=1)
        
        # 计算红球区间分布
        if self.lottery_type == 'ssq':
            intervals = [(1,11), (12,22), (23,33)]
        else:  # dlt
            intervals = [(1,12), (13,24), (25,35)]
            
        for i, (start, end) in enumerate(intervals, 1):
            features[f'red_zone_{i}_count'] = ((red_numbers >= start) & 
                                             (red_numbers <= end)).sum(axis=1)
        
        # 2. 蓝球特征
        blue_numbers = data[self.blue_columns].values
        blue_mid = (self.blue_range[1] - self.blue_range[0]) // 2 + self.blue_range[0]
        
        if self.lottery_type == 'ssq':
            # 双色球蓝球特征
            features['blue_is_odd'] = blue_numbers[:, 0] % 2 == 1
            features['blue_is_big'] = blue_numbers[:, 0] > blue_mid
            features['blue_mod3'] = blue_numbers[:, 0] % 3
        else:
            # 大乐透蓝球特征
            features['back_sum'] = blue_numbers.sum(axis=1)
            features['back_span'] = blue_numbers.max(axis=1) - blue_numbers.min(axis=1)
            features['back_odd_count'] = (blue_numbers % 2 == 1).sum(axis=1)
            features['back_big_count'] = (blue_numbers > blue_mid).sum(axis=1)
        
        # 3. 总体特征
        if self.lottery_type == 'ssq':
            features['total_sum'] = features['red_sum'] + blue_numbers[:, 0]
        else:
            features['total_sum'] = features['red_sum'] + features['back_sum']
            
        # 转换特征类型
        for col in features.columns:
            if features[col].dtype == bool:
                features[col] = features[col].astype(int)
                
        return features
    
    def _generate_statistical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成统计特征
        
        生成的特征包括:
        1. 频率特征:
           - 近期出现频率
           - 历史出现频率
           - 遗漏值统计
           
        2. 趋势特征:
           - 移动平均
           - 移动标准差
           - 移动极差
           
        3. 波动特征:
           - 方差比
           - 变异系数
           - 波动率
           
        Args:
            data: 原始数据DataFrame
            
        Returns:
            统计特征DataFrame
        """
        features = pd.DataFrame(index=data.index)
        
        try:
            # 1. 频率特征
            freq_features = self._calculate_frequency_features(data)
            for key, series in freq_features.items():
                features[key] = series
            
            # 2. 趋势特征
            trend_features = self._calculate_trend_features(data)
            for key, series in trend_features.items():
                features[key] = series
            
            # 3. 波动特征
            volatility_features = self._calculate_volatility_features(data)
            for key, series in volatility_features.items():
                features[key] = series
            
            return features
            
        except Exception as e:
            self.logger.error(f"生成统计特征时发生错误: {str(e)}")
            raise
    
    def _generate_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成时间相关特征
    
        生成的特征包括:
        1. 日期特征:
           - 星期几
           - 月份
           - 季节
           - 年份
       
        2. 周期性特征:
           - 距离上期天数
           - 开奖间隔统计
           - 月内第几次开奖
       
        3. 时序特征:
           - 滞后特征
           - 差分特征
           - 趋势特征
       
        Args:
            data: 原始数据DataFrame，必须包含'date'列
        
        Returns:
            时间特征DataFrame
        """
        if 'date' not in data.columns:
            raise ValueError("数据必须包含'date'列")
        
        features = pd.DataFrame(index=data.index)
        
        try:
            # 1. 日期特征
            date_features = self._calculate_date_features(data)
            for key, series in date_features.items():
                features[key] = series
            
            # 2. 周期性特征
            periodic_features = self._calculate_periodic_features(data)
            for key, series in periodic_features.items():
                features[key] = series
            
            # 3. 时序特征
            sequence_features = self._calculate_sequence_features(data)
            for key, series in sequence_features.items():
                features[key] = series
            
            return features
            
        except Exception as e:
            self.logger.error(f"生成时间特征时发生错误: {str(e)}")
            raise

    def _generate_pattern_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成号码模式特征
    
        生成的特征包括:
        1. 基础分布模式:
           - 奇偶比例
           - 大小比例
           - 质数比例
           - 区间分布
       
        2. 连号模式:
           - 连号数量
           - 连号位置
           - 最大连号长度
       
        3. 重复模式:
           - 与历史号码的重复情况
           - 号码间隔统计
           - 热温冷号分布
       
        4. 组合模式:
           - AC值
           - 和值特征
           - 跨度特征
       
        Args:
            data: 原始数据DataFrame
        
        Returns:
            模式特征DataFrame
        """
        try:
            features = pd.DataFrame(index=data.index)
            
            # 1. 基础分布模式
            distribution_features = self._calculate_distribution_patterns(data)
            for key, series in distribution_features.items():
                features[key] = series
            
            # 2. 连号模式
            consecutive_features = self._calculate_consecutive_patterns(data)
            for key, series in consecutive_features.items():
                features[key] = series
            
            # 3. 重复模式
            repeat_features = self._calculate_repeat_patterns(data)
            for key, series in repeat_features.items():
                features[key] = series
            
            # 4. 组合模式
            combination_features = self._calculate_combination_patterns(data)
            for key, series in combination_features.items():
                features[key] = series
            
            return features
            
        except Exception as e:
            self.logger.error(f"生成模式特征时发生错误: {str(e)}")
            raise

    def _generate_combination_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成组合特征
    
        生成的特征包括:
        1. 号码组合特征:
           - 号码和值特征
           - 号码跨度特征
           - 号码密度特征
           
        2. 区间组合特征:
           - 区间分布特征
           - 区间组合模式
           - 区间平衡性
           
        3. 数字特性组合:
           - 奇偶组合特征
           - 质合组合特征
           - 大小组合特征
           
        4. 历史组合特征:
           - 历史热门组合
           - 组合重复性
           - 组合间隔统计
           
        Args:
            data: 原始数据DataFrame
        
        Returns:
            组合特征DataFrame
        """
        try:
            features = pd.DataFrame(index=data.index)
            
            # 1. 号码组合特征
            if self.lottery_type == 'ssq':
                red_numbers = data[self.red_columns].values
                blue_numbers = data[self.blue_columns].values.flatten()
            else:  # dlt
                red_numbers = data[self.red_columns].values
                blue_numbers = data[self.blue_columns].values
            
            # 计算和值特征
            features['red_sum'] = np.sum(red_numbers, axis=1)
            features['red_sum_diff'] = features['red_sum'].diff()
            features['red_sum_ratio'] = features['red_sum'] / (red_numbers.shape[1] * self.red_range[1])
            
            if self.lottery_type == 'dlt':
                features['blue_sum'] = np.sum(blue_numbers, axis=1)
                features['total_sum'] = features['red_sum'] + features['blue_sum']
                
            # 计算跨度特征
            features['red_span'] = np.max(red_numbers, axis=1) - np.min(red_numbers, axis=1)
            features['red_density'] = features['red_span'] / red_numbers.shape[1]
            
            # 2. 区间组合特征
            red_intervals = self._calculate_interval_features(red_numbers)
            for key, series in red_intervals.items():
                features[key] = series
            
            # 3. 数字特性组合
            number_features = self._calculate_number_properties(red_numbers)
            for key, series in number_features.items():
                features[key] = series
            
            # 4. 历史组合特征
            history_features = self._calculate_historical_combinations(red_numbers)
            for key, series in history_features.items():
                features[key] = series
            
            return features
        
        except Exception as e:
            self.logger.error(f"生成组合特征时发生错误: {str(e)}")
            raise

    def _calculate_frequency_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算频率相关特征"""
        features = {}
        
        # 设置不同的统计窗口
        windows = [5, 10, 20, 30]
        
        # 红球频率特征
        red_numbers = data[self.red_columns].values
        red_df = pd.DataFrame(red_numbers, index=data.index)
        
        for window in windows:
            # 计算近期出现频率 - 修复计算逻辑
            def calc_unique_ratio(x):
                if len(x) == 0:
                    return 0.0
                unique_count = len(np.unique(x.dropna()))
                return unique_count / len(x)
            
            recent_freq = red_df.rolling(window, min_periods=1).apply(
                calc_unique_ratio, raw=False
            ).mean(axis=1)
            features[f'red_freq_{window}'] = recent_freq
            
            # 计算遗漏值统计 - 修复计算逻辑
            def calc_missing_ratio(x):
                if len(x) == 0:
                    return 0.0
                unique_count = len(np.unique(x.dropna()))
                total_possible = self.red_range[1] - self.red_range[0] + 1
                return (total_possible - unique_count) / total_possible
            
            missing_ratio = red_df.rolling(window, min_periods=1).apply(
                calc_missing_ratio, raw=False
            ).mean(axis=1)
            features[f'red_missing_{window}'] = missing_ratio
        
        # 蓝球频率特征
        blue_numbers = data[self.blue_columns].values
        
        for window in windows:
            if self.lottery_type == 'ssq':
                # 双色球蓝球频率
                blue_series = pd.Series(blue_numbers.flatten(), index=data.index)
                
                def calc_blue_freq(x):
                    if len(x) == 0:
                        return 0.0
                    unique_count = len(np.unique(x.dropna()))
                    return unique_count / len(x)
                
                recent_freq = blue_series.rolling(window, min_periods=1).apply(calc_blue_freq)
                features[f'blue_freq_{window}'] = recent_freq
            else:
                # 大乐透蓝球频率
                blue_df = pd.DataFrame(blue_numbers, index=data.index)
                recent_freq = blue_df.rolling(window, min_periods=1).apply(
                    calc_unique_ratio, raw=False
                ).mean(axis=1)
                features[f'back_freq_{window}'] = recent_freq
        
        # 确保所有特征都有相同的索引
        for key, series in features.items():
            if len(series) != len(data):
                # 如果长度不匹配，重新索引
                features[key] = series.reindex(data.index, fill_value=0.0)
        
        return features

    def _calculate_trend_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算趋势相关特征"""
        features = {}
        windows = [5, 10, 20]
        
        # 红球趋势特征
        red_sums = data[self.red_columns].sum(axis=1)
        for window in windows:
            # 移动平均
            features[f'red_ma_{window}'] = red_sums.rolling(window, min_periods=1).mean()
            # 移动标准差
            features[f'red_std_{window}'] = red_sums.rolling(window, min_periods=1).std().fillna(0)
            # 移动极差
            features[f'red_range_{window}'] = (red_sums.rolling(window, min_periods=1).max() - 
                                             red_sums.rolling(window, min_periods=1).min()).fillna(0)
        
        # 蓝球趋势特征
        if self.lottery_type == 'ssq':
            blue_numbers = data[self.blue_columns].values.flatten()
            blue_series = pd.Series(blue_numbers, index=data.index)
            for window in windows:
                features[f'blue_ma_{window}'] = blue_series.rolling(window, min_periods=1).mean()
                features[f'blue_std_{window}'] = blue_series.rolling(window, min_periods=1).std().fillna(0)
        else:
            back_sums = data[self.blue_columns].sum(axis=1)
            for window in windows:
                features[f'back_ma_{window}'] = back_sums.rolling(window, min_periods=1).mean()
                features[f'back_std_{window}'] = back_sums.rolling(window, min_periods=1).std().fillna(0)
        
        return features

    def _calculate_volatility_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算波动相关特征"""
        features = {}
        windows = [5, 10, 20]
        
        # 红球波动特征
        red_sums = data[self.red_columns].sum(axis=1)
        for window in windows:
            # 方差比 - 添加安全检查
            rolling_var = red_sums.rolling(window, min_periods=1).var()
            rolling_mean = red_sums.rolling(window, min_periods=1).mean()
            var_ratio = rolling_var / (rolling_mean ** 2 + 1e-8)  # 避免除零
            features[f'red_var_ratio_{window}'] = var_ratio.fillna(0)
            
            # 变异系数 - 添加安全检查
            rolling_std = red_sums.rolling(window, min_periods=1).std()
            cv = rolling_std / (rolling_mean + 1e-8)  # 避免除零
            features[f'red_cv_{window}'] = cv.fillna(0)
            
            # 波动率 - 添加安全检查
            rolling_max = red_sums.rolling(window, min_periods=1).max()
            rolling_min = red_sums.rolling(window, min_periods=1).min()
            volatility = (rolling_max - rolling_min) / (rolling_mean + 1e-8)
            features[f'red_volatility_{window}'] = volatility.fillna(0)
        
        # 蓝球波动特征
        if self.lottery_type == 'ssq':
            blue_numbers = data[self.blue_columns].values.flatten()
            blue_series = pd.Series(blue_numbers, index=data.index)
            for window in windows:
                rolling_var = blue_series.rolling(window, min_periods=1).var()
                rolling_mean = blue_series.rolling(window, min_periods=1).mean()
                features[f'blue_var_ratio_{window}'] = (rolling_var / (rolling_mean ** 2 + 1e-8)).fillna(0)
                
                rolling_std = blue_series.rolling(window, min_periods=1).std()
                features[f'blue_cv_{window}'] = (rolling_std / (rolling_mean + 1e-8)).fillna(0)
        else:
            back_sums = data[self.blue_columns].sum(axis=1)
            for window in windows:
                rolling_var = back_sums.rolling(window, min_periods=1).var()
                rolling_mean = back_sums.rolling(window, min_periods=1).mean()
                features[f'back_var_ratio_{window}'] = (rolling_var / (rolling_mean ** 2 + 1e-8)).fillna(0)
                
                rolling_std = back_sums.rolling(window, min_periods=1).std()
                features[f'back_cv_{window}'] = (rolling_std / (rolling_mean + 1e-8)).fillna(0)
        
        return features

    def _calculate_date_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算日期相关特征"""
        features = {}
        
        # 确保date列为datetime类型
        dates = pd.to_datetime(data['date'])
        
        # 基础日期特征
        features['weekday'] = dates.dt.dayofweek  # 0-6，0表示周一
        features['weekend'] = dates.dt.dayofweek.isin([5, 6]).astype(int)  # 是否周末
        features['month'] = dates.dt.month  # 1-12
        features['quarter'] = dates.dt.quarter  # 1-4
        features['year'] = dates.dt.year
        features['day_of_month'] = dates.dt.day  # 1-31
        features['week_of_year'] = dates.dt.isocalendar().week
        
        # 季节特征（根据月份划分）
        features['season'] = pd.cut(dates.dt.month, 
                                  bins=[0, 3, 6, 9, 12], 
                                  labels=['春', '夏', '秋', '冬'],
                                  include_lowest=True)
        
        # 是否月初/月中/月末
        features['is_month_start'] = dates.dt.is_month_start.astype(int)
        features['is_month_end'] = dates.dt.is_month_end.astype(int)
        features['is_month_middle'] = (~(dates.dt.is_month_start | dates.dt.is_month_end)).astype(int)
        
        return features

    def _calculate_periodic_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算周期性特征"""
        features = {}
        dates = pd.to_datetime(data['date'])
        
        # 计算开奖间隔
        date_diff = dates.diff().dt.days
        features['days_since_last'] = date_diff
        
        # 开奖间隔统计
        windows = [5, 10, 20]
        for window in windows:
            features[f'avg_interval_{window}'] = date_diff.rolling(window).mean()
            features[f'std_interval_{window}'] = date_diff.rolling(window).std()
            features[f'max_interval_{window}'] = date_diff.rolling(window).max()
        
        # 月内开奖次序
        features['draw_order_in_month'] = dates.groupby(
            [dates.dt.year, dates.dt.month]
        ).cumcount() + 1
        
        # 距离上次相同星期几开奖的期数
        weekday = dates.dt.dayofweek
        features['periods_since_same_weekday'] = weekday.groupby(weekday).cumcount()
        
        return features

    def _calculate_sequence_features(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算时序特征"""
        features = {}
        
        # 获取红球和蓝球数据
        if self.lottery_type == 'ssq':
            red_data = data[self.red_columns]
            blue_data = data[self.blue_columns]
        else:  # dlt
            red_data = data[self.red_columns]
            blue_data = data[self.blue_columns]
        
        # 计算红球滞后特征
        red_sums = red_data.sum(axis=1)
        for lag in [1, 2, 3, 5]:
            features[f'red_sum_lag_{lag}'] = red_sums.shift(lag)
            # 差分特征
            if lag == 1:
                features['red_sum_diff'] = red_sums.diff()
                features['red_sum_diff_pct'] = red_sums.pct_change()
        
        # 计算蓝球滞后特征
        if self.lottery_type == 'ssq':
            blue_numbers = blue_data.values.flatten()
            blue_series = pd.Series(blue_numbers, index=data.index)
            for lag in [1, 2, 3]:
                features[f'blue_lag_{lag}'] = blue_series.shift(lag)
                if lag == 1:
                    features['blue_diff'] = blue_series.diff()
        else:
            back_sums = blue_data.sum(axis=1)
            for lag in [1, 2, 3]:
                features[f'back_sum_lag_{lag}'] = back_sums.shift(lag)
                if lag == 1:
                    features['back_sum_diff'] = back_sums.diff()
        
        # 趋势特征
        windows = [5, 10, 20]
        for window in windows:
            # 红球趋势
            features[f'red_trend_{window}'] = (
                red_sums.rolling(window, min_periods=1).mean().pct_change().fillna(0)
            )
            
            # 蓝球趋势
            if self.lottery_type == 'ssq':
                features[f'blue_trend_{window}'] = (
                    blue_series.rolling(window, min_periods=1).mean().pct_change().fillna(0)
                )
            else:
                features[f'back_trend_{window}'] = (
                    back_sums.rolling(window, min_periods=1).mean().pct_change().fillna(0)
                )
        
        return features

    def _calculate_distribution_patterns(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算基础分布模式特征"""
        features = {}
        
        if self.lottery_type == 'ssq':
            red_data = data[self.red_columns]
            blue_data = data[self.blue_columns]
        else:  # dlt
            red_data = data[self.red_columns]
            blue_data = data[self.blue_columns]
        
        # 红球分布特征
        for prefix, numbers in [('red', red_data), ('blue', blue_data)]:
            # 奇偶比例
            features[f'{prefix}_odd_ratio'] = (numbers % 2 == 1).sum(axis=1) / numbers.shape[1]
            
            # 大小比例（以号码范围中位数为界）
            mid = 16 if prefix == 'red' else 8
            features[f'{prefix}_high_ratio'] = (numbers > mid).sum(axis=1) / numbers.shape[1]
            
            # 质数比例
            primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
            features[f'{prefix}_prime_ratio'] = numbers.isin(primes).sum(axis=1) / numbers.shape[1]
            
            # 区间分布
            if prefix == 'red':
                for i in range(3):
                    start = i * 11 + 1
                    end = (i + 1) * 11 if i < 2 else 33
                    features[f'red_zone_{i+1}_count'] = (
                        (numbers >= start) & (numbers <= end)
                    ).sum(axis=1)
        
        return features

    def _calculate_consecutive_patterns(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算连号模式特征"""
        features = {}
        
        def get_consecutive_info(row):
            numbers = sorted(row)
            consecutive_count = 0
            max_consecutive = 0
            current_consecutive = 1
            consecutive_positions = []
            
            for i in range(1, len(numbers)):
                if numbers[i] == numbers[i-1] + 1:
                    current_consecutive += 1
                    if current_consecutive == 2:
                        consecutive_count += 1
                        consecutive_positions.append(i-1)
                else:
                    max_consecutive = max(max_consecutive, current_consecutive)
                    current_consecutive = 1
            
            max_consecutive = max(max_consecutive, current_consecutive)
            return consecutive_count, max_consecutive, consecutive_positions
        
        # 红球连号特征
        if self.lottery_type == 'ssq':
            red_numbers = data[self.red_columns].values
        else:
            red_numbers = data[self.red_columns].values
        
        # 处理空数据情况
        if len(red_numbers) == 0:
            features['consecutive_count'] = pd.Series([], dtype=int)
            features['max_consecutive_length'] = pd.Series([], dtype=int)
            features['has_consecutive'] = pd.Series([], dtype=int)
            for i in range(5):
                features[f'consecutive_pos_{i+1}'] = pd.Series([], dtype=int)
            return features
        
        consecutive_info = [get_consecutive_info(row) for row in red_numbers]
        
        # 分别提取各个特征
        features['consecutive_count'] = pd.Series([info[0] for info in consecutive_info], index=data.index)
        features['max_consecutive_length'] = pd.Series([info[1] for info in consecutive_info], index=data.index)
        features['has_consecutive'] = pd.Series([(info[0] > 0) for info in consecutive_info], index=data.index, dtype=int)
        
        # 连号位置特征
        for i in range(5):  # 最多5个连号位置
            features[f'consecutive_pos_{i+1}'] = pd.Series([
                1 if i < len(info[2]) else 0 for info in consecutive_info
            ], index=data.index, dtype=int)
        
        return features

    def _calculate_repeat_patterns(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算重复模式特征"""
        features = {}
        
        # 计算与前N期的重复情况
        def calculate_repeats(numbers, prev_numbers):
            return len(set(numbers) & set(prev_numbers))
        
        for look_back in [1, 2, 3, 5]:
            # 红球重复
            if self.lottery_type == 'ssq':
                red_numbers = data[self.red_columns].values
            else:
                red_numbers = data[self.red_columns].values
            
            repeat_values = [
                calculate_repeats(red_numbers[i], red_numbers[i-look_back])
                if i >= look_back else 0
                for i in range(len(data))
            ]
            features[f'red_repeat_{look_back}'] = pd.Series(repeat_values, index=data.index)
            
            # 蓝球重复（双色球）或后区重复（大乐透）
            if self.lottery_type == 'ssq':
                blue_numbers = data[self.blue_columns].values.flatten()
                blue_repeat = (blue_numbers == np.roll(blue_numbers, look_back)).astype(int)
                features[f'blue_repeat_{look_back}'] = pd.Series(blue_repeat, index=data.index)
            else:
                back_numbers = data[self.blue_columns].values
                back_repeat_values = [
                    calculate_repeats(back_numbers[i], back_numbers[i-look_back])
                    if i >= look_back else 0
                    for i in range(len(data))
                ]
                features[f'back_repeat_{look_back}'] = pd.Series(back_repeat_values, index=data.index)
        
        # 计算热温冷号分布
        def calculate_number_temperature(numbers, history_numbers, hot_threshold=3, cold_threshold=8):
            freq = pd.Series(history_numbers.flatten()).value_counts()
            hot_nums = set(freq[freq >= hot_threshold].index)
            cold_nums = set(freq[freq <= cold_threshold].index)
            warm_nums = set(range(1, max(numbers.max(), history_numbers.max()) + 1)) - hot_nums - cold_nums
            
            return (
                len(set(numbers) & hot_nums),
                len(set(numbers) & warm_nums),
                len(set(numbers) & cold_nums)
            )
        
        # 计算最近30期的热温冷分布
        window = 30
        red_hot_counts = []
        red_warm_counts = []
        red_cold_counts = []
        
        for i in range(len(data)):
            start_idx = max(0, i - window)
            if i == 0 or start_idx == i:  # 第一期或没有历史数据
                red_hot_counts.append(0)
                red_warm_counts.append(0)
                red_cold_counts.append(0)
            else:
                red_history = data.iloc[start_idx:i][self.red_columns].values
                current_red = data.iloc[i][self.red_columns].values
                if len(red_history) > 0:
                    hot, warm, cold = calculate_number_temperature(current_red, red_history)
                    red_hot_counts.append(hot)
                    red_warm_counts.append(warm)
                    red_cold_counts.append(cold)
                else:
                    red_hot_counts.append(0)
                    red_warm_counts.append(0)
                    red_cold_counts.append(0)
        
        features['red_hot_count'] = pd.Series(red_hot_counts, index=data.index)
        features['red_warm_count'] = pd.Series(red_warm_counts, index=data.index)
        features['red_cold_count'] = pd.Series(red_cold_counts, index=data.index)
        
        return features

    def _calculate_combination_patterns(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算组合模式特征"""
        features = {}
        
        if self.lottery_type == 'ssq':
            red_data = data[self.red_columns].values
            blue_data = data[self.blue_columns].values.flatten()
        else:
            red_data = data[self.red_columns].values
            blue_data = data[self.blue_columns].values
        
        # 计算AC值（邻号差值的平均值）
        def calculate_ac_value(numbers):
            sorted_nums = np.sort(numbers)
            diffs = np.diff(sorted_nums)
            return np.mean(diffs)
        
        features['red_ac_value'] = pd.Series([calculate_ac_value(row) for row in red_data], index=data.index)
        if self.lottery_type == 'dlt':
            features['back_ac_value'] = pd.Series([calculate_ac_value(row) for row in blue_data], index=data.index)
        
        # 和值特征
        red_sum = np.sum(red_data, axis=1)
        features['red_sum'] = pd.Series(red_sum, index=data.index)
        features['red_sum_mod_10'] = pd.Series(red_sum % 10, index=data.index)
        features['red_sum_ones'] = pd.Series(red_sum % 10, index=data.index)
        features['red_sum_tens'] = pd.Series((red_sum // 10) % 10, index=data.index)
        
        if self.lottery_type == 'dlt':
            back_sum = np.sum(blue_data, axis=1)
            features['back_sum'] = pd.Series(back_sum, index=data.index)
            features['total_sum'] = pd.Series(red_sum + back_sum, index=data.index)
        else:
            features['total_sum'] = pd.Series(red_sum + blue_data, index=data.index)
        
        # 跨度特征
        red_span = np.max(red_data, axis=1) - np.min(red_data, axis=1)
        features['red_span'] = pd.Series(red_span, index=data.index)
        if self.lottery_type == 'dlt':
            back_span = np.max(blue_data, axis=1) - np.min(blue_data, axis=1)
            features['back_span'] = pd.Series(back_span, index=data.index)
        
        # 号码间隔特征
        sorted_red = np.sort(red_data, axis=1)
        features['red_avg_gap'] = pd.Series(np.mean(np.diff(sorted_red, axis=1), axis=1), index=data.index)
        features['red_max_gap'] = pd.Series(np.max(np.diff(sorted_red, axis=1), axis=1), index=data.index)
        features['red_min_gap'] = pd.Series(np.min(np.diff(sorted_red, axis=1), axis=1), index=data.index)
        
        return features

    def _calculate_interval_features(self, numbers: np.ndarray) -> Dict[str, pd.Series]:
        """计算区间分布特征"""
        features = {}
        
        # 定义区间
        if self.lottery_type == 'ssq':
            intervals = [(1,11), (12,22), (23,33)]
        else:  # dlt
            intervals = [(1,12), (13,24), (25,35)]
        
        # 计算每个区间的号码数量
        for i, (start, end) in enumerate(intervals):
            interval_count = np.sum((numbers >= start) & (numbers <= end), axis=1)
            features[f'interval_{i+1}_count'] = pd.Series(interval_count, index=range(len(numbers)))
        
        # 计算区间组合模式
        interval_patterns = []
        for row in numbers:
            pattern = []
            for start, end in intervals:
                count = np.sum((row >= start) & (row <= end))
                pattern.append(str(count))
            interval_patterns.append('_'.join(pattern))
        
        features['interval_pattern'] = pd.Series(interval_patterns, index=range(len(numbers)))
        
        # 计算区间平衡性
        interval_counts = [features[f'interval_{i+1}_count'] for i in range(len(intervals))]
        mean_counts = np.mean(interval_counts, axis=0)
        std_counts = np.std(interval_counts, axis=0)
        features['interval_balance'] = pd.Series(mean_counts / (std_counts + 1e-6), index=range(len(numbers)))
        
        return features

    def _calculate_number_properties(self, numbers: np.ndarray) -> Dict[str, pd.Series]:
        """计算数字特性组合"""
        features = {}
        
        # 奇偶特征
        odd_counts = np.sum(numbers % 2 == 1, axis=1)
        even_counts = numbers.shape[1] - odd_counts
        features['odd_even_ratio'] = pd.Series(odd_counts / (even_counts + 1e-8), index=range(len(numbers)))  # 避免除零
        features['odd_even_pattern'] = pd.Series([f"{int(odd)}_{int(even)}" for odd, even in zip(odd_counts, even_counts)], index=range(len(numbers)))
        
        # 质数特征
        primes = {2,3,5,7,11,13,17,19,23,29,31}
        prime_counts = np.sum(np.isin(numbers, list(primes)), axis=1)
        features['prime_count'] = pd.Series(prime_counts, index=range(len(numbers)))
        features['prime_ratio'] = pd.Series(prime_counts / numbers.shape[1], index=range(len(numbers)))
        
        # 大小特征
        mid_point = self.red_range[1] // 2
        big_counts = np.sum(numbers > mid_point, axis=1)
        small_counts = numbers.shape[1] - big_counts
        features['big_small_ratio'] = pd.Series(big_counts / (small_counts + 1e-8), index=range(len(numbers)))  # 避免除零
        features['big_small_pattern'] = pd.Series([f"{int(big)}_{int(small)}" for big, small in zip(big_counts, small_counts)], index=range(len(numbers)))
        
        return features

    def _calculate_historical_combinations(self, numbers: np.ndarray) -> Dict[str, pd.Series]:
        """计算历史组合特征"""
        features = {}
        
        # 计算组合重复
        for look_back in [1, 3, 5]:
            repeat_counts = []
            for i in range(len(numbers)):
                if i < look_back:
                    repeat_counts.append(0)
                    continue
                
                current_set = set(numbers[i])
                historical_sets = [set(numbers[j]) for j in range(i-look_back, i)]
                max_repeats = max(len(current_set & hist_set) for hist_set in historical_sets)
                repeat_counts.append(max_repeats)
                
            features[f'combination_repeat_{look_back}'] = pd.Series(repeat_counts, index=range(len(numbers)))
        
        # 计算热门组合
        combination_str = ['_'.join(map(str, row)) for row in numbers]
        combination_counts = pd.Series(combination_str).value_counts()
        features['combination_frequency'] = pd.Series([combination_counts.get(comb, 0) for comb in combination_str], index=range(len(numbers)))
        
        return features
