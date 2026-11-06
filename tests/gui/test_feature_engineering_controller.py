"""Controller/core integration without a real Tk window."""
import numpy as np
import pandas as pd
import pytest
from src.gui.controllers.feature_engineering_controller import FeatureEngineeringController


@pytest.fixture
def controller(monkeypatch):
    controller = FeatureEngineeringController()
    assert controller.initialize('ssq')
    history = pd.DataFrame({'red_numbers': [[1, 2, 3, 10, 20, 30]] * 10, 'blue_number': [3] * 10})
    monkeypatch.setattr(controller.feature_engineering.data_manager, 'get_history_data',
                        lambda lottery_type, periods: history.head(periods).copy())
    return controller


def test_generate_features_loads_requested_history(controller):
    received = []
    controller.register_callback('on_feature_generated', received.append)
    result = controller.generate_features(periods=3)
    assert result is not None
    assert result['red_sum'].tolist() == [66, 66, 66]
    pd.testing.assert_frame_equal(received[0]['raw_features'], result)


def test_core_error_reaches_controller_callback(controller):
    errors = []
    controller.register_callback('on_error', errors.append)
    assert controller.generate_features(periods=0) is None
    assert len(errors) == 1


def test_feature_selection_and_report_use_real_scores(controller):
    data = pd.DataFrame({'signal': np.arange(20), 'noise': np.tile([0, 1], 10)}, index=range(20, 40))
    target = pd.Series(np.arange(20), index=data.index)
    received = []
    controller.register_callback('on_feature_selected', received.append)
    result = controller.select_features(data, target, method='correlation', k=1)
    assert result.columns.tolist() == ['signal']
    assert result.index.equals(data.index)
    pd.testing.assert_frame_equal(received[0], result)
    assert controller.get_feature_importance_report()['signal'] > 0


def test_unknown_lottery_initialization_reports_error():
    controller = FeatureEngineeringController()
    errors = []
    controller.register_callback('on_error', errors.append)
    assert not controller.initialize('unknown')
    assert len(errors) == 1


def test_generated_payload_is_consumed_by_existing_view_without_tk(controller):
    from types import SimpleNamespace
    from src.gui.frames.feature_engineering_frame import FeatureEngineeringFrame
    class TextSink:
        def __init__(self):
            self.content = ''
        def delete(self, *args):
            self.content = ''
        def insert(self, position, text):
            self.content += text
    view = SimpleNamespace(result_text=TextSink(), features_df=None)
    errors = []
    controller.register_callback('on_error', errors.append)
    controller.register_callback('on_feature_generated',
        lambda payload: FeatureEngineeringFrame._on_feature_generated(view, payload))
    result = controller.generate_features(periods=3)
    assert result is not None
    assert not errors
    assert len(view.features_df) == 3
    assert view.raw_data['red_numbers'].tolist() == [[1, 2, 3, 10, 20, 30]] * 3
    assert view.raw_data['blue'].tolist() == [3, 3, 3]
    assert view.features_df.to_numpy(dtype=float).min() >= 0
    assert view.features_df.to_numpy(dtype=float).max() <= 1
    assert '特征预览' in view.result_text.content
