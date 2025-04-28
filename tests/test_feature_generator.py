import pytest
import pandas as pd
import numpy as np
from src.core.features.generators import FeatureGenerator

def test_basic_features_ssq():
    # 创建测试数据
    data = pd.DataFrame({
        'red_1': [1, 10, 20],
        'red_2': [5, 15, 25],
        'red_3': [8, 18, 28],
        'red_4': [12, 22, 30],
        'red_5': [15, 25, 32],
        'red_6': [20, 30, 33],
        'blue': [5, 10, 15]
    })
    
    # 初始化生成器
    generator = FeatureGenerator('ssq')
    
    # 生成特征
    features = generator._generate_basic_features(data)
    
    # 验证特征
    assert 'red_sum' in features.columns
    assert 'red_mean' in features.columns
    assert 'red_odd_count' in features.columns
    assert 'blue_is_odd' in features.columns
    
    # 验证特征值
    assert features.loc[0, 'red_sum'] == 61
    assert features.loc[0, 'red_odd_count'] == 3
    assert features.loc[0, 'blue_is_odd'] == 1

def test_basic_features_dlt():
    # 创建测试数据
    data = pd.DataFrame({
        'front_1': [1, 10, 20],
        'front_2': [5, 15, 25],
        'front_3': [8, 18, 28],
        'front_4': [12, 22, 30],
        'front_5': [15, 25, 32],
        'back_1': [2, 8, 11],
        'back_2': [5, 10, 12]
    })
    
    # 初始化生成器
    generator = FeatureGenerator('dlt')
    
    # 生成特征
    features = generator._generate_basic_features(data)
    
    # 验证特征
    assert 'red_sum' in features.columns
    assert 'back_sum' in features.columns
    assert 'total_sum' in features.columns
    
    # 验证特征值
    assert features.loc[0, 'red_sum'] == 41
    assert features.loc[0, 'back_sum'] == 7
    assert features.loc[0, 'total_sum'] == 48

def test_statistical_features_ssq():
    # 创建测试数据
    np.random.seed(42)
    n_samples = 50
    data = pd.DataFrame({
        'red_1': np.random.randint(1, 34, n_samples),
        'red_2': np.random.randint(1, 34, n_samples),
        'red_3': np.random.randint(1, 34, n_samples),
        'red_4': np.random.randint(1, 34, n_samples),
        'red_5': np.random.randint(1, 34, n_samples),
        'red_6': np.random.randint(1, 34, n_samples),
        'blue': np.random.randint(1, 17, n_samples)
    })
    
    generator = FeatureGenerator('ssq')
    features = generator._generate_statistical_features(data)
    
    # 验证特征存在性
    assert 'red_freq_5' in features.columns
    assert 'red_ma_10' in features.columns
    assert 'red_var_ratio_20' in features.columns
    assert 'blue_freq_5' in features.columns
    
    # 验证特征值范围
    assert features['red_freq_5'].min() >= 0
    assert features['red_freq_5'].max() <= 1
    assert not features['red_ma_10'].isnull().all()
    assert not features['blue_freq_5'].isnull().all()

def test_statistical_features_dlt():
    # 创建测试数据
    np.random.seed(42)
    n_samples = 50
    data = pd.DataFrame({
        'front_1': np.random.randint(1, 36, n_samples),
        'front_2': np.random.randint(1, 36, n_samples),
        'front_3': np.random.randint(1, 36, n_samples),
        'front_4': np.random.randint(1, 36, n_samples),
        'front_5': np.random.randint(1, 36, n_samples),
        'back_1': np.random.randint(1, 13, n_samples),
        'back_2': np.random.randint(1, 13, n_samples)
    })
    
    generator = FeatureGenerator('dlt')
    features = generator._generate_statistical_features(data)
    
    # 验证特征存在性
    assert 'red_freq_5' in features.columns
    assert 'red_ma_10' in features.columns
    assert 'back_freq_5' in features.columns
    assert 'back_var_ratio_20' in features.columns
    
    # 验证特征值范围
    assert features['red_freq_5'].min() >= 0
    assert features['red_freq_5'].max() <= 1
    assert not features['red_ma_10'].isnull().all()
    assert not features['back_freq_5'].isnull().all()

def test_statistical_features_error_handling():
    # 创建无效数据
    data = pd.DataFrame({'invalid_column': [1, 2, 3]})
    
    generator = FeatureGenerator('ssq')
    with pytest.raises(Exception):
        generator._generate_statistical_features(data)

def test_temporal_features_ssq():
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', periods=50, freq='3D')
    np.random.seed(42)
    data = pd.DataFrame({
        'date': dates,
        'red_1': np.random.randint(1, 34, 50),
        'red_2': np.random.randint(1, 34, 50),
        'red_3': np.random.randint(1, 34, 50),
        'red_4': np.random.randint(1, 34, 50),
        'red_5': np.random.randint(1, 34, 50),
        'red_6': np.random.randint(1, 34, 50),
        'blue': np.random.randint(1, 17, 50)
    })
    
    generator = FeatureGenerator('ssq')
    features = generator._generate_temporal_features(data)
    
    # 验证日期特征
    assert 'weekday' in features.columns
    assert 'month' in features.columns
    assert 'season' in features.columns
    assert features['weekday'].min() >= 0
    assert features['weekday'].max() <= 6
    
    # 验证周期性特征
    assert 'days_since_last' in features.columns
    assert 'avg_interval_5' in features.columns
    assert 'draw_order_in_month' in features.columns
    assert features['days_since_last'].iloc[1:].equals(pd.Series([3] * 49))
    
    # 验证时序特征
    assert 'red_sum_lag_1' in features.columns
    assert 'blue_lag_1' in features.columns
    assert 'red_trend_5' in features.columns
    assert not features['red_sum_lag_1'].isnull().all()

def test_temporal_features_dlt():
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', periods=50, freq='3D')
    np.random.seed(42)
    data = pd.DataFrame({
        'date': dates,
        'front_1': np.random.randint(1, 36, 50),
        'front_2': np.random.randint(1, 36, 50),
        'front_3': np.random.randint(1, 36, 50),
        'front_4': np.random.randint(1, 36, 50),
        'front_5': np.random.randint(1, 36, 50),
        'back_1': np.random.randint(1, 13, 50),
        'back_2': np.random.randint(1, 13, 50)
    })
    
    generator = FeatureGenerator('dlt')
    features = generator._generate_temporal_features(data)
    
    # 验证日期特征
    assert 'weekday' in features.columns
    assert 'month' in features.columns
    assert 'season' in features.columns
    
    # 验证周期性特征
    assert 'days_since_last' in features.columns
    assert 'avg_interval_5' in features.columns
    
    # 验证时序特征
    assert 'red_sum_lag_1' in features.columns
    assert 'back_sum_lag_1' in features.columns
    assert 'red_trend_5' in features.columns
    assert not features['red_sum_lag_1'].isnull().all()

def test_temporal_features_error_handling():
    # 测试缺少date列的情况
    data = pd.DataFrame({'invalid_column': [1, 2, 3]})
    
    generator = FeatureGenerator('ssq')
    with pytest.raises(ValueError, match="数据必须包含'date'列"):
        generator._generate_temporal_features(data)
    
    # 测试无效日期的情况
    data = pd.DataFrame({
        'date': ['invalid_date', '2023-01-01', '2023-01-02'],
        'red_1': [1, 2, 3]
    })
    
    with pytest.raises(Exception):
        generator._generate_temporal_features(data)

def test_pattern_features_ssq():
    # 创建测试数据
    data = pd.DataFrame({
        'red_1': [1, 10, 20],
        'red_2': [2, 15, 25],
        'red_3': [3, 18, 28],
        'red_4': [12, 22, 30],
        'red_5': [15, 25, 32],
        'red_6': [20, 30, 33],
        'blue': [5, 10, 15]
    })
    
    generator = FeatureGenerator('ssq')
    features = generator._generate_pattern_features(data)
    
    # 验证基础分布特征
    assert 'red_odd_ratio' in features.columns
    assert 'red_high_ratio' in features.columns
    assert 'red_prime_ratio' in features.columns
    assert 'red_zone_1_count' in features.columns
    
    # 验证连号特征
    assert 'consecutive_count' in features.columns
    assert 'max_consecutive_length' in features.columns
    assert features.loc[0, 'consecutive_count'] == 2  # 1,2,3连号
    
    # 验证重复模式特征
    assert 'red_repeat_1' in features.columns
    assert 'blue_repeat_1' in features.columns
    
    # 验证组合模式特征
    assert 'red_ac_value' in features.columns
    assert 'red_sum' in features.columns
    assert 'red_span' in features.columns
    assert features.loc[0, 'red_span'] == 19  # 20 - 1 = 19

def test_pattern_features_dlt():
    # 创建测试数据
    data = pd.DataFrame({
        'front_1': [1, 10, 20],
        'front_2': [2, 15, 25],
        'front_3': [3, 18, 28],
        'front_4': [12, 22, 30],
        'front_5': [15, 25, 32],
        'back_1': [2, 8, 11],
        'back_2': [5, 10, 12]
    })
    
    generator = FeatureGenerator('dlt')
    features = generator._generate_pattern_features(data)
    
    # 验证基础分布特征
    assert 'red_odd_ratio' in features.columns
    assert 'blue_odd_ratio' in features.columns
    
    # 验证连号特征
    assert 'consecutive_count' in features.columns
    assert features.loc[0, 'consecutive_count'] == 2  # 1,2,3连号
    
    # 验证重复模式特征
    assert 'red_repeat_1' in features.columns
    assert 'back_repeat_1' in features.columns
    
    # 验证组合模式特征
    assert 'red_ac_value' in features.columns
    assert 'back_ac_value' in features.columns
    assert 'total_sum' in features.columns

def test_pattern_features_edge_cases():
    # 测试空数据
    data = pd.DataFrame(columns=['red_1', 'red_2', 'red_3', 'red_4', 'red_5', 'red_6', 'blue'])
    generator = FeatureGenerator('ssq')
    features = generator._generate_pattern_features(data)
    assert len(features) == 0
    
    # 测试单行数据
    data = pd.DataFrame({
        'red_1': [1],
        'red_2': [2],
        'red_3': [3],
        'red_4': [4],
        'red_5': [5],
        'red_6': [6],
        'blue': [7]
    })
    features = generator._generate_pattern_features(data)
    assert len(features) == 1
    assert features.loc[0, 'consecutive_count'] == 5  # 1,2,3,4,5,6全是连号

def test_pattern_features_invalid_data():
    # 测试无效数据
    data = pd.DataFrame({'invalid_column': [1, 2, 3]})
    generator = FeatureGenerator('ssq')
    with pytest.raises(Exception):
        generator._generate_pattern_features(data)

def test_combination_features_ssq():
    # 创建测试数据
    np.random.seed(42)
    n_samples = 50
    data = pd.DataFrame({
        'red_1': np.random.randint(1, 34, n_samples),
        'red_2': np.random.randint(1, 34, n_samples),
        'red_3': np.random.randint(1, 34, n_samples),
        'red_4': np.random.randint(1, 34, n_samples),
        'red_5': np.random.randint(1, 34, n_samples),
        'red_6': np.random.randint(1, 34, n_samples),
        'blue': np.random.randint(1, 17, n_samples)
    })
    
    generator = FeatureGenerator('ssq')
    features = generator._generate_combination_features(data)
    
    # 验证基本特征存在性
    assert 'red_sum' in features.columns
    assert 'red_span' in features.columns
    assert 'interval_1_count' in features.columns
    assert 'odd_even_ratio' in features.columns
    assert 'prime_ratio' in features.columns
    assert 'combination_repeat_1' in features.columns
    
    # 验证特征值范围
    assert features['red_sum'].min() >= 6  # 最少6个号码
    assert features['red_sum'].max() <= 33 * 6  # 最大可能和值
    assert all(features['odd_even_ratio'] >= 0)
    assert all(features['prime_ratio'] >= 0) and all(features['prime_ratio'] <= 1)
    
def test_combination_features_dlt():
    # 创建测试数据
    np.random.seed(42)
    n_samples = 50
    data = pd.DataFrame({
        'front_1': np.random.randint(1, 36, n_samples),
        'front_2': np.random.randint(1, 36, n_samples),
        'front_3': np.random.randint(1, 36, n_samples),
        'front_4': np.random.randint(1, 36, n_samples),
        'front_5': np.random.randint(1, 36, n_samples),
        'back_1': np.random.randint(1, 13, n_samples),
        'back_2': np.random.randint(1, 13, n_samples)
    })
    
    generator = FeatureGenerator('dlt')
    features = generator._generate_combination_features(data)
    
    # 验证特征存在性
    assert 'red_sum' in features.columns
    assert 'blue_sum' in features.columns
    assert 'total_sum' in features.columns
    assert 'interval_balance' in features.columns
    assert 'big_small_pattern' in features.columns
    
    # 验证特征值范围
    assert features['blue_sum'].min() >= 2  # 最少2个号码
    assert features['blue_sum'].max() <= 12 * 2  # 最大可能和值
    assert all(features['interval_balance'] >= 0)
