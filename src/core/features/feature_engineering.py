"""
特征工程模块

该模块提供了特征工程相关的功能，包括特征提取、特征选择和特征重要性分析。
主要用于彩票数据的特征工程，支持双色球和大乐透两种彩票类型。

主要类:
    - FeatureEngineering: 特征工程主控制器
    - FeatureProcessor: 特征处理器基类
    - DataExplorationAnalyzer: 数据探索分析器
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import os
from sklearn.feature_selection import SelectKBest, mutual_info_regression, f_regression
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from pathlib import Path
import logging

from .ssq_feature_processor import SSQFeatureProcessor
from .dlt_feature_processor import DLTFeatureProcessor
from .feature_validator import FeatureValidator
from ..data_manager import LotteryDataManager
from ..number_data import normalize_number_data

class FeatureEngineering:
    """
    特征工程主控制器
    
    该类负责协调特征提取、特征选择和特征重要性分析等功能。
    支持双色球和大乐透两种彩票类型的特征工程。
    
    属性:
        lottery_type (str): 彩票类型，'ssq'表示双色球，'dlt'表示大乐透
        processor (FeatureProcessor): 特征处理器，根据彩票类型初始化
        data_manager (LotteryDataManager): 数据管理器，用于获取历史数据
        feature_scores (Dict[str, float]): 特征重要性分数
    """
    
    def __init__(self, lottery_type: Optional[str] = None, data_path: Optional[str] = None):
        """
        初始化特征工程控制器
        
        Args:
            lottery_type: 彩票类型 ('ssq' 或 'dlt')，如不指定则不加载特定处理器
            data_path: 数据文件路径，用于初始化数据管理器
        """
        self.logger = logging.getLogger(__name__)
        if lottery_type is not None and lottery_type not in ('ssq', 'dlt'):
            raise ValueError(f"不支持的彩票类型: {lottery_type}")
        self.lottery_type = lottery_type
        self.processor = (SSQFeatureProcessor() if lottery_type == 'ssq' 
                         else DLTFeatureProcessor() if lottery_type == 'dlt'
                         else None)
        
        # 未指定时由数据管理器使用项目配置，避免误读 src/data。
        self.data_manager = LotteryDataManager(data_path=data_path)
        self.feature_validator = FeatureValidator()
        self.feature_scores = {}
        self.raw_data = None
        
        # 缓存相关
        self._feature_cache = {}
        self._data_cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = pd.Timedelta(hours=24)  # 缓存有效期24小时
        
        self.scaler = StandardScaler()
        
        # 特征存储相关
        self.base_dir = str(self.data_manager.data_path / 'features')
        os.makedirs(self.base_dir, exist_ok=True)
        
    def clear_cache(self, cache_type: str = 'all'):
        """清除缓存
        
        Args:
            cache_type: 缓存类型，可选值:
                       - 'all': 所有缓存
                       - 'data': 数据缓存
                       - 'feature': 特征缓存
        """
        if cache_type in ['all', 'data']:
            self._data_cache.clear()
            # 清除与数据相关的时间戳
            keys_to_remove = [k for k in self._cache_timestamp if k.startswith('data_')]
            for k in keys_to_remove:
                del self._cache_timestamp[k]
                
        if cache_type in ['all', 'feature']:
            self._feature_cache.clear()
            # 清除与特征相关的时间戳
            keys_to_remove = [k for k in self._cache_timestamp if k.startswith('feature_')]
            for k in keys_to_remove:
                del self._cache_timestamp[k]
        
    def refresh_cache(self, force: bool = False):
        """刷新缓存数据
        
        检查缓存是否过期，并清除过期的缓存。
        
        Args:
            force: 是否强制刷新所有缓存
        """
        current_time = pd.Timestamp.now()
        
        # 检查数据缓存
        data_keys_to_remove = []
        for key, timestamp in self._cache_timestamp.items():
            if key.startswith('data_') and (force or (current_time - timestamp) > self._cache_ttl):
                data_keys_to_remove.append(key)
                cache_key = key[5:]  # 移除'data_'前缀
                if cache_key in self._data_cache:
                    del self._data_cache[cache_key]
        
        # 检查特征缓存
        feature_keys_to_remove = []
        for key, timestamp in self._cache_timestamp.items():
            if key.startswith('feature_') and (force or (current_time - timestamp) > self._cache_ttl):
                feature_keys_to_remove.append(key)
                cache_key = key[8:]  # 移除'feature_'前缀
                if cache_key in self._feature_cache:
                    del self._feature_cache[cache_key]
        
        # 清除过期的时间戳
        for key in data_keys_to_remove + feature_keys_to_remove:
            if key in self._cache_timestamp:
                del self._cache_timestamp[key]
    
    def _get_cached_data(self, lottery_type: str, periods: int) -> pd.DataFrame:
        """
        获取缓存的历史数据
        
        该方法使用缓存机制获取历史数据，避免重复查询数据库。
        
        Args:
            lottery_type: 彩票类型
            periods: 期数
            
        Returns:
            历史数据DataFrame
        """
        cache_key = f"{lottery_type}_{periods}"
        timestamp_key = f"data_{cache_key}"
        
        # 检查缓存是否存在且未过期
        current_time = pd.Timestamp.now()
        if (cache_key in self._data_cache and 
            timestamp_key in self._cache_timestamp and 
            (current_time - self._cache_timestamp[timestamp_key]) <= self._cache_ttl):
            return self._data_cache[cache_key]
        
        # 缓存不存在或已过期，重新获取数据
        data = self.data_manager.get_history_data(lottery_type, periods)
        
        # 更新缓存
        self._data_cache[cache_key] = data
        self._cache_timestamp[timestamp_key] = current_time
        
        return data
    
    def _cache_features(self, key: str, features: pd.DataFrame):
        """缓存特征数据
        
        Args:
            key: 缓存键
            features: 特征数据
        """
        self._feature_cache[key] = features
        self._cache_timestamp[f"feature_{key}"] = pd.Timestamp.now()
    
    def _get_cached_features(self, key: str) -> Optional[pd.DataFrame]:
        """获取缓存的特征数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的特征数据，如果不存在则返回None
        """
        timestamp_key = f"feature_{key}"
        
        # 检查缓存是否存在且未过期
        current_time = pd.Timestamp.now()
        if (key in self._feature_cache and 
            timestamp_key in self._cache_timestamp and 
            (current_time - self._cache_timestamp[timestamp_key]) <= self._cache_ttl):
            return self._feature_cache[key]
        
        return None

    def generate_features(self, data: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
        """从号码DataFrame生成数值特征，保留行索引并报告真实执行结果。"""
        try:
            if progress_callback:
                progress_callback(0, "开始生成特征")
            if self.processor is None:
                raise ValueError("特征处理器未初始化，请在创建 FeatureEngineering 时指定 lottery_type")
            prepared = normalize_number_data(data, self.lottery_type)
            features = self._generate_basic_features(prepared)
            if hasattr(self.processor, 'extract_advanced_features'):
                advanced = self.processor.extract_advanced_features(prepared)
                features = pd.concat([features, advanced], axis=1)
            if not np.isfinite(features.to_numpy(dtype=float)).all():
                raise ValueError("生成的特征包含无效值")
            self.raw_data = prepared.copy()
            if progress_callback:
                progress_callback(100, "特征生成完成")
            return features
        except Exception as exc:
            if progress_callback:
                progress_callback(-1, f"错误: {exc}")
            raise ValueError(f"特征生成失败: {exc}") from exc

    def generate_features_from_history(self, periods: int = 100, progress_callback=None) -> pd.DataFrame:
        """按期数读取历史后调用DataFrame特征接口。"""
        if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
            raise ValueError("期数必须为正整数")
        history = self.data_manager.get_history_data(self.lottery_type, periods=periods)
        return self.generate_features(history, progress_callback=progress_callback)

    def _generate_basic_features(self, data: pd.DataFrame, periods: int = 7) -> pd.DataFrame:
        """生成球区统计及只依赖当前与过去记录的滚动特征。"""
        df = normalize_number_data(data, self.lottery_type)
        original_index = df.index
        date_column = next((column for column in ['draw_date', 'date'] if column in df.columns), None)
        if date_column:
            df[date_column] = pd.to_datetime(df[date_column], errors='raise')
            if df[date_column].isna().any():
                raise ValueError("开奖日期不能为空")
            df = df.sort_values(date_column, kind='stable')
        prefix, count = ('red', 6) if self.lottery_type == 'ssq' else ('front', 5)
        columns = [f'{prefix}_{i + 1}' for i in range(count)]
        number = df[columns[0]]
        features = pd.DataFrame(index=df.index)
        rolling = number.rolling(window=periods, min_periods=1)
        features['number_frequency_ma7'] = rolling.mean()
        features['number_frequency_mean'] = number.expanding().mean()
        features['number_frequency_std7'] = rolling.std().fillna(0)
        features['gap_days'] = df[date_column].diff().dt.total_seconds().div(86400).fillna(0) if date_column else 0
        features['sum_value_ma7'] = rolling.sum()
        balls = df[columns]
        features[f'{prefix}_sum'] = balls.sum(axis=1)
        features[f'{prefix}_mean'] = balls.mean(axis=1)
        features[f'{prefix}_std'] = balls.std(axis=1)
        features[f'{prefix}_odd_count'] = balls.mod(2).sum(axis=1)
        features[f'{prefix}_even_count'] = count - features[f'{prefix}_odd_count']
        if self.lottery_type == 'ssq':
            primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
            features['red_prime_count'] = balls.isin(primes).sum(axis=1)
            features['red_consecutive_count'] = balls.diff(axis=1).eq(1).sum(axis=1)
            features['blue_is_prime'] = df['blue_number'].isin(primes)
            features['blue_is_odd'] = df['blue_number'].mod(2).eq(1)
        return features.reindex(original_index)

    def process_with_progress(self, func, callback=None):
        """使用进度回调执行函数
        
        Args:
            func: 要执行的函数
            callback: 进度回调函数
            
        Returns:
            函数执行结果
        """
        try:
            if callback:
                callback(0, "开始处理")
            result = func()
            if callback:
                callback(100, "处理完成")
            return result
        except Exception as e:
            if callback:
                callback(-1, f"错误: {str(e)}")
            raise
            
    def _generate_statistical_features(self, basic_features: pd.DataFrame) -> pd.DataFrame:
        """生成统计特征
    
        Args:
            basic_features: 基础特征数据
        
        Returns:
            pd.DataFrame: 统计特征
        """
        try:
            df = basic_features.copy()
            
            # 保持原有列不变
            return df
        
        except Exception as e:
            self.logger.error(f"生成统计特征时出错: {str(e)}")
            return None

    def _generate_combined_features(self, basic_features: pd.DataFrame, 
                                  statistical_features: pd.DataFrame) -> pd.DataFrame:
        """生成组合特征"""
        # 实现组合特征生成逻辑
        pass

    def _normalize_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """对特征进行归一化处理
    
        Args:
            features: 待归一化的特征DataFrame
        
        Returns:
            pd.DataFrame: 归一化后的特征DataFrame
        """
        try:
            if features is None or features.empty:
                raise ValueError("输入特征数据不能为空")
            
            df = features.copy()
            
            # 对每一列进行归一化处理
            for column in df.columns:
                # 跳过日期类型的列
                if df[column].dtype == 'datetime64[ns]':
                    continue
                
                # 获取列的最大最小值
                min_val = df[column].min()
                max_val = df[column].max()
                
                # 处理最大值等于最小值的情况
                if max_val == min_val:
                    df[column] = 0.5  # 所有值相同时设为0.5
                else:
                    # 使用Min-Max归一化
                    df[column] = (df[column] - min_val) / (max_val - min_val)
            
            # 检查是否有无效值
            if df.isnull().any().any():
                df = df.fillna(method='bfill').fillna(method='ffill')
            
            # 确保所有值都在[0,1]范围内
            df = df.clip(0, 1)
            
            return df
        
        except Exception as e:
            self.logger.error(f"特征归一化处理时出错: {str(e)}")
            raise ValueError(f"特征归一化失败: {str(e)}")

    def select_features(self, features: pd.DataFrame, target: pd.Series,
                        method: str = 'mutual_info', n_features: int = 10) -> pd.DataFrame:
        """选择真实数值特征，保留输入索引并记录实际评分。"""
        if not isinstance(features, pd.DataFrame) or features.empty:
            raise ValueError("特征不能为空")
        if isinstance(n_features, bool) or not isinstance(n_features, int) or not 1 <= n_features <= features.shape[1]:
            raise ValueError("选择特征数必须在1和特征列数之间")
        y = self._aligned_target(features, target)
        if method == 'correlation':
            scores = self._correlation_scores(features, y)
            selected = scores.nlargest(n_features).index
        elif method in ('mutual_info', 'f_regression'):
            score_func = (lambda X, y: mutual_info_regression(X, y, random_state=42,
                          n_neighbors=min(3, len(X) - 1))) if method == 'mutual_info' else f_regression
            selector = SelectKBest(score_func=score_func, k=n_features)
            selector.fit(features, y)
            scores = pd.Series(np.nan_to_num(selector.scores_), index=features.columns)
            selected = features.columns[selector.get_support()]
        else:
            raise ValueError(f"不支持的特征选择方法: {method}")
        self.feature_scores = {column: float(scores[column]) for column in selected}
        return features.loc[:, selected].copy()

    def analyze_feature_importance(self, features: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """以互信息及相关性分析特征，常数列的相关性按零处理。"""
        if len(features) < 2:
            raise ValueError("特征重要性分析至少需要两条记录")
        y = self._aligned_target(features, target)
        mi_scores = mutual_info_regression(features, y, random_state=42,
                                           n_neighbors=min(3, len(features) - 1))
        correlations = self._correlation_scores(features, y)
        scores = {column: float((mi_scores[i] + correlations[column]) / 2)
                  for i, column in enumerate(features.columns)}
        self.feature_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
        return self.feature_scores

    def get_feature_importance_report(self) -> Dict[str, float]:
        return dict(self.feature_scores)

    @staticmethod
    def _aligned_target(features: pd.DataFrame, target) -> pd.Series:
        if not features.index.is_unique:
            raise ValueError("特征索引必须唯一")
        if isinstance(target, pd.Series):
            if (not target.index.is_unique or len(target) != len(features)
                    or not features.index.isin(target.index).all()):
                raise ValueError("目标与特征必须具有相同且唯一的索引")
            result = target.reindex(features.index)
        else:
            values = np.asarray(target)
            if values.ndim != 1 or len(values) != len(features):
                raise ValueError("目标必须为与特征等长的一维数组")
            result = pd.Series(values, index=features.index)
        if not np.isfinite(result.to_numpy(dtype=float)).all():
            raise ValueError("目标必须为有限数值")
        return result

    @staticmethod
    def _correlation_scores(features: pd.DataFrame, target: pd.Series) -> pd.Series:
        scores = pd.Series(0.0, index=features.columns)
        varying = features.columns[features.nunique() > 1]
        if target.nunique() > 1 and len(varying):
            scores.loc[varying] = features[varying].corrwith(target).abs().fillna(0)
        return scores

    def visualize_features(self, features: pd.DataFrame, target: pd.Series = None) -> Figure:
        """特征可视化
        
        Args:
            features: 特征DataFrame
            target: 可选的目标变量
            
        Returns:
            matplotlib Figure对象
        """
        n_features = len(features.columns)
        fig_rows = (n_features + 2) // 3
        
        fig, axes = plt.subplots(fig_rows, 3, figsize=(15, 5*fig_rows))
        axes = axes.ravel()
        
        for i, feature in enumerate(features.columns):
            if target is not None:
                # 散点图
                sns.scatterplot(data=features, x=feature, y=target, ax=axes[i])
            else:
                # 分布图
                sns.histplot(data=features, x=feature, ax=axes[i])
                
        plt.tight_layout()
        return fig

    def save_features(self, features: pd.DataFrame, filename: str):
        """保存特征到文件
        
        Args:
            features: 特征DataFrame
            filename: 文件名
        """
        save_path = Path(self.base_dir) / f"{filename}.pkl"
        features.to_pickle(save_path)

    def load_features(self, filename: str) -> pd.DataFrame:
        """从文件加载特征
        
        Args:
            filename: 文件名
            
        Returns:
            特征DataFrame
        """
        load_path = Path(self.base_dir) / f"{filename}.pkl"
        return pd.read_pickle(load_path)

    def _track_progress(self, current: int, total: int, description: str):
        """跟踪处理进度
        
        Args:
            current: 当前进度
            total: 总数
            description: 进度描述
        """ 
        if hasattr(self, 'progress_callback') and self.progress_callback:
            progress = (current / total) * 100
            self.progress_callback(progress, description)


    def visualize_feature_importance(self, 
                                   top_n: int = 20, 
                                   save_path: Optional[str] = None,
                                   show_plot: bool = True) -> Optional[Figure]:
        """可视化特征重要性
        
        该方法将特征重要性以条形图的形式可视化，展示最重要的top_n个特征。
        
        Args:
            top_n: 展示的特征数量
            save_path: 保存图像的路径，如果为None则不保存
            show_plot: 是否显示图像
            
        Returns:
            matplotlib.figure.Figure: 如果show_plot为False，则返回图像对象
            
        Raises:
            ValueError: 如果特征重要性未计算
        """
        if not self.feature_scores:
            raise ValueError("请先运行特征重要性分析")
        
        # 将特征重要性转换为DataFrame
        report = pd.DataFrame({
            'feature': list(self.feature_scores.keys()),
            'importance': list(self.feature_scores.values())
        }).sort_values('importance', ascending=False)
        
        # 限制展示的特征数量
        if len(report) > top_n:
            report = report.head(top_n)
        
        # 创建图像
        fig = plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='importance', y='feature', data=report, palette='viridis')
        
        # 添加标题和标签
        plt.title(f'特征重要性 Top {len(report)}', fontsize=16)
        plt.xlabel('重要性', fontsize=14)
        plt.ylabel('特征', fontsize=14)
        
        # 添加数值标签
        for i, v in enumerate(report['importance']):
            ax.text(v + 0.01, i, f'{v:.4f}', va='center')
        
        plt.tight_layout()
        
        # 保存图像
        if save_path:
            if not save_path.endswith('.png') and not save_path.endswith('.jpg'):
                save_path += '.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # 显示或返回图像
        if show_plot:
            plt.show()
            return None
        else:
            plt.close()
            return fig
    
    def visualize_feature_distribution(self, 
                                     features_df: pd.DataFrame,
                                     columns: Optional[List[str]] = None,
                                     n_cols: int = 3,
                                     save_path: Optional[str] = None,
                                     show_plot: bool = True) -> Optional[Figure]:
        """可视化特征分布
        
        该方法将特征的分布以直方图的形式可视化，可以选择特定的列进行可视化。
        
        Args:
            features_df: 特征DataFrame
            columns: 要可视化的列，如果为None则可视化所有列
            n_cols: 每行显示的图像数量
            save_path: 保存图像的路径，如果为None则不保存
            show_plot: 是否显示图像
            
        Returns:
            matplotlib.figure.Figure: 如果show_plot为False，则返回图像对象
            
        Raises:
            ValueError: 如果特征数据为空
        """
        if features_df.empty:
            raise ValueError("特征数据为空")
        
        # 选择要可视化的列
        if columns is None:
            columns = features_df.columns
        else:
            # 确保所有列都存在
            for col in columns:
                if col not in features_df.columns:
                    raise ValueError(f"列 '{col}' 不存在于特征数据中")
        
        # 计算行数
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        # 创建图像
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        axes = axes.flatten() if n_rows * n_cols > 1 else [axes]
        
        # 绘制每个特征的分布
        for i, col in enumerate(columns):
            if i < len(axes):
                # 绘制直方图和核密度估计
                sns.histplot(features_df[col].dropna(), kde=True, ax=axes[i])
                axes[i].set_title(f'{col} 分布', fontsize=12)
                axes[i].set_xlabel(col, fontsize=10)
                axes[i].set_ylabel('频率', fontsize=10)
        
        # 隐藏多余的子图
        for i in range(len(columns), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # 保存图像
        if save_path:
            if not save_path.endswith('.png') and not save_path.endswith('.jpg'):
                save_path += '.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # 显示或返回图像
        if show_plot:
            plt.show()
            return None
        else:
            fig = plt.gcf()
            plt.close()
            return fig
    
    def visualize_feature_correlation(self, 
                                    features_df: pd.DataFrame,
                                    method: str = 'pearson',
                                    threshold: float = 0.8,
                                    save_path: Optional[str] = None,
                                    show_plot: bool = True) -> Optional[Figure]:
        """可视化特征相关性
        
        该方法将特征之间的相关性以热力图的形式可视化，可以选择相关性计算方法。
        
        Args:
            features_df: 特征DataFrame
            method: 相关性计算方法，可选值: 'pearson', 'kendall', 'spearman'
            threshold: 高相关性阈值，用于标记高相关性特征
            save_path: 保存图像的路径，如果为None则不保存
            show_plot: 是否显示图像
            
        Returns:
            matplotlib.figure.Figure: 如果show_plot为False，则返回图像对象
            
        Raises:
            ValueError: 如果特征数据为空
        """
        if features_df.empty:
            raise ValueError("特征数据为空")
        
        # 计算相关性矩阵
        corr_matrix = features_df.corr(method=method)
        
        # 创建图像
        plt.figure(figsize=(12, 10))
        
        # 绘制热力图
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        
        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                   square=True, linewidths=.5, annot=False, fmt='.2f')
        
        # 添加标题
        plt.title(f'特征相关性热力图 ({method})', fontsize=16)
        
        plt.tight_layout()
        
        # 保存图像
        if save_path:
            if not save_path.endswith('.png') and not save_path.endswith('.jpg'):
                save_path += '.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # 显示或返回图像
        if show_plot:
            plt.show()
            return None
        else:
            fig = plt.gcf()
            plt.close()
            return fig
    
    def visualize_feature_pairplot(self,
                                 features_df: pd.DataFrame,
                                 columns: Optional[List[str]] = None,
                                 target: Optional[pd.Series] = None,
                                 save_path: Optional[str] = None,
                                 show_plot: bool = True) -> Optional[Figure]:
        """可视化特征对关系
        
        该方法将特征之间的关系以散点图矩阵的形式可视化，可以选择特定的列进行可视化。
        
        Args:
            features_df: 特征DataFrame
            columns: 要可视化的列，如果为None则选择前5个数值列
            target: 目标变量，用于着色散点图
            save_path: 保存图像的路径，如果为None则不保存
            show_plot: 是否显示图像
        
        Returns:
            matplotlib.figure.Figure: 如果show_plot为False，则返回图像对象
        
        Raises:
            ValueError: 如果特征数据为空
        """
        if features_df.empty:
            raise ValueError("特征数据为空")
        
        # 选择要可视化的列
        if columns is None:
            # 选择前5个数值列
            numeric_cols = features_df.select_dtypes(include=['number']).columns
            columns = list(numeric_cols[:min(5, len(numeric_cols))])
        else:
            # 确保所有列都存在
            for col in columns:
                if col not in features_df.columns:
                    raise ValueError(f"列 '{col}' 不存在于特征数据中")
        
        # 准备数据
        plot_data = features_df[columns].copy()
        
        # 如果有目标变量，添加到数据中
        if target is not None:
            if len(target) != len(features_df):
                raise ValueError("目标变量长度与特征数据长度不匹配")
            plot_data['target'] = target
            hue = 'target'
        else:
            hue = None
        
        # 创建散点图矩阵
        g = sns.pairplot(plot_data, hue=hue, diag_kind='kde', 
                         plot_kws={'alpha': 0.6}, height=3)
        
        # 添加标题
        g.figure.suptitle('特征对关系图', fontsize=16, y=1.02)
        
        # 保存图像
        if save_path:
            if not save_path.endswith('.png') and not save_path.endswith('.jpg'):
                save_path += '.png'
            g.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # 显示或返回图像
        if show_plot:
            plt.show()
            return None
        else:
            fig = g.figure  # 使用 figure 而不是 fig
            plt.close()
            return fig

    def _generate_advanced_features(self, basic_features: pd.DataFrame) -> pd.DataFrame:
        """生成高级特征"""
        try:
            advanced_features = basic_features.copy()
            # Add your advanced feature generation logic here
            return advanced_features
        except Exception as e:
            raise ValueError(f"生成高级特征失败: {str(e)}")
