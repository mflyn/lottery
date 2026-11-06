import pandas as pd
import pytest
from src.core.features.feature_engineering import FeatureEngineering


def test_progress_callback_reports_real_feature_work(tmp_path):
    engineer = FeatureEngineering('ssq', data_path=str(tmp_path))
    history = pd.DataFrame({'red_numbers': [[1, 2, 3, 10, 20, 30]] * 3, 'blue_number': [3, 4, 5]})
    events = []
    result = engineer.generate_features(history, progress_callback=lambda *event: events.append(event))
    assert result['red_sum'].tolist() == [66, 66, 66]
    assert [event[0] for event in events] == [0, 100]


def test_feature_error_reports_failure_instead_of_completion(tmp_path):
    engineer = FeatureEngineering('ssq', data_path=str(tmp_path))
    events = []
    with pytest.raises(ValueError):
        engineer.generate_features(pd.DataFrame(), progress_callback=lambda *event: events.append(event))
    assert events[-1][0] == -1
    assert 100 not in [event[0] for event in events]
