"""Current DataFrame feature API, exercised without processor mocks."""
import numpy as np
import pandas as pd
import pytest
from src.core.features.feature_engineering import FeatureEngineering


@pytest.fixture
def history():
    return pd.DataFrame({
        'draw_date': pd.date_range('2024-01-01', periods=10),
        'red_numbers': [[1, 2, 3, 10, 20, 30]] * 10,
        'blue_number': [3] * 10,
    }, index=range(10, 20))


@pytest.fixture
def engineer(tmp_path):
    return FeatureEngineering('ssq', data_path=str(tmp_path))


@pytest.mark.parametrize('blue_column', ['blue_number', 'blue', 'blue_1', 'blue_numbers'])
def test_blue_aliases_and_list_input(engineer, history, blue_column):
    data = history.rename(columns={'blue_number': blue_column})
    if blue_column == 'blue_numbers':
        data[blue_column] = [[3]] * len(data)
    features = engineer.generate_features(data)
    assert features.index.equals(history.index)
    assert features['red_sum'].tolist() == [66] * 10
    assert features['red_consecutive_count'].tolist() == [2] * 10
    assert features['blue_is_prime'].all()
    assert features['blue_is_odd'].all()
    assert np.isfinite(features.to_numpy(dtype=float)).all()


def test_derived_columns_do_not_change_ball_statistics(engineer, history):
    clean = engineer.generate_features(history)
    changed = history.assign(red_sum=999, red_mean=500, red_odd_count=20)
    pd.testing.assert_frame_equal(engineer.generate_features(changed), clean)


def test_short_windows_are_finite_and_do_not_use_future_draws(engineer, history):
    history.at[11, 'red_numbers'] = [4, 5, 6, 11, 21, 31]
    before = engineer.generate_features(history.iloc[:2])
    after = engineer.generate_features(history)
    pd.testing.assert_frame_equal(before, after.loc[before.index])
    assert before['number_frequency_ma7'].tolist() == [1.0, 2.5]
    assert before['gap_days'].tolist() == [0.0, 1.0]
    assert np.isfinite(before.to_numpy(dtype=float)).all()


def test_features_preserve_input_and_index(engineer, history):
    original = history.copy(deep=True)
    features = engineer.generate_features(history)
    pd.testing.assert_frame_equal(history, original)
    assert features.index.tolist() == list(range(10, 20))


@pytest.mark.parametrize('bad_data', [None, pd.DataFrame(), pd.DataFrame({'unrelated': [1]}), 100])
def test_invalid_feature_input_is_rejected(engineer, bad_data):
    with pytest.raises(ValueError):
        engineer.generate_features(bad_data)


def test_no_lottery_processor_is_rejected(tmp_path, history):
    with pytest.raises(ValueError):
        FeatureEngineering(data_path=str(tmp_path)).generate_features(history)


@pytest.mark.parametrize('method', ['mutual_info', 'f_regression', 'correlation'])
def test_real_feature_selection_preserves_index(engineer, method):
    data = pd.DataFrame({'signal': np.arange(20), 'noise': np.tile([0, 1], 10)}, index=range(20, 40))
    target = pd.Series(np.arange(20), index=data.index)
    selected = engineer.select_features(data, target, method=method, n_features=1)
    assert selected.columns.tolist() == ['signal']
    assert selected.index.equals(data.index)
    assert engineer.feature_scores['signal'] > 0


def test_importance_handles_constant_features(engineer):
    data = pd.DataFrame({'constant': [1] * 10, 'signal': range(10)})
    with np.errstate(invalid='raise', divide='raise'):
        scores = engineer.analyze_feature_importance(data, pd.Series(range(10)))
    assert all(np.isfinite(score) for score in scores.values())
    assert scores['signal'] > scores['constant']


def test_history_features_use_configured_data_directory(tmp_path, monkeypatch):
    import json
    from src.core.config_manager import get_config_manager
    monkeypatch.setattr(get_config_manager(), 'get_data_path', lambda: str(tmp_path))
    rows = [{'draw_num': f'202400{i+1}', 'draw_date': f'2024-01-0{i+1}',
             'red_numbers': [1, 2, 3, 10, 20, 30], 'blue_number': 3,
             'sales': 0, 'prize_pool': 0} for i in range(3)]
    (tmp_path / 'ssq_history.json').write_text(json.dumps({'data': rows}))
    engineer = FeatureEngineering('ssq')
    features = engineer.generate_features_from_history(periods=2)
    assert engineer.data_manager.data_path == tmp_path
    assert features['red_sum'].tolist() == [66, 66]


def test_series_targets_are_aligned_by_label(engineer):
    data = pd.DataFrame({'signal': [1, 2, 3, 4, 5, 6], 'noise': [6, 1, 5, 2, 4, 3]}, index=list('abcdef'))
    target = pd.Series([1, 2, 3, 4, 5, 6], index=list('abcdef'))
    ordered = engineer.analyze_feature_importance(data, target)
    shuffled = target.loc[list('faebdc')]
    assert engineer.select_features(data, shuffled, 'correlation', 1).columns.tolist() == ['signal']
    assert engineer.analyze_feature_importance(data, shuffled) == pytest.approx(ordered)


@pytest.mark.parametrize('method', ['correlation', 'mutual_info', 'f_regression'])
def test_mismatched_target_labels_are_rejected(engineer, method):
    data = pd.DataFrame({'signal': range(6)}, index=list('abcdef'))
    with pytest.raises(ValueError):
        engineer.select_features(data, pd.Series(range(6), index=list('abcdeg')), method, 1)
