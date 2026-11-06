"""Expanded-column inputs and real feature calculations."""
import numpy as np
import pandas as pd
import pytest
from src.core.features.feature_engineering import FeatureEngineering


@pytest.fixture
def engineer(tmp_path):
    return FeatureEngineering('ssq', data_path=str(tmp_path))


@pytest.fixture
def expanded():
    return pd.DataFrame({**{f'red_{i+1}': [n] * 5 for i, n in enumerate([1, 5, 10, 15, 20, 25])},
                         'blue': [1, 2, 3, 4, 5]})


def test_expanded_columns_match_list_input(engineer, expanded):
    canonical = pd.DataFrame({'red_numbers': [[1, 5, 10, 15, 20, 25]] * 5, 'blue_number': [1, 2, 3, 4, 5]})
    pd.testing.assert_frame_equal(engineer.generate_features(expanded), engineer.generate_features(canonical))


def test_basic_statistics_are_computed_from_exact_ball_columns(engineer, expanded):
    result = engineer.generate_features(expanded)
    assert result['red_sum'].tolist() == [76] * 5
    assert result['red_mean'].iloc[0] == pytest.approx(76 / 6)
    assert result['red_odd_count'].tolist() == [4] * 5
    assert result['red_even_count'].tolist() == [2] * 5
    assert result['red_consecutive_count'].tolist() == [0] * 5


def test_full_consecutive_run_counts_five_pairs(engineer, expanded):
    for i in range(6):
        expanded[f'red_{i+1}'] = i+1
    assert engineer.generate_features(expanded)['red_consecutive_count'].tolist() == [5] * 5


def test_missing_ball_column_is_rejected(engineer, expanded):
    with pytest.raises(ValueError):
        engineer.generate_features(expanded.drop(columns='red_6'))


def test_duplicate_ball_is_rejected(engineer, expanded):
    expanded['red_6'] = expanded['red_1']
    with pytest.raises(ValueError):
        engineer.generate_features(expanded)


def test_partial_windows_produce_finite_values(engineer, expanded):
    assert np.isfinite(engineer.generate_features(expanded.head(1)).to_numpy(dtype=float)).all()


def test_unknown_selection_method_is_rejected(engineer):
    with pytest.raises(ValueError):
        engineer.select_features(pd.DataFrame({'a': range(10)}), pd.Series(range(10)), 'unknown', 1)


def test_excessive_feature_count_is_rejected(engineer):
    with pytest.raises(ValueError):
        engineer.select_features(pd.DataFrame({'a': range(10)}), pd.Series(range(10)), n_features=2)
