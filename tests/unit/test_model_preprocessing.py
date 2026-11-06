import numpy as np
import pandas as pd
import pytest
from src.core.preprocessing.data_preprocessor import DataPreprocessor


@pytest.fixture
def processor(tmp_path):
    return DataPreprocessor(config_dir=str(tmp_path))


def test_numeric_and_categorical_preprocessing_preserves_alignment(processor):
    data = pd.DataFrame({'value': [1.0, np.nan, 5.0, 5.0], 'category': ['B', None, 'A', 'A']}, index=[10, 20, 30, 40])
    original = data.copy(deep=True)
    result = processor.preprocess_data(data, categorical_columns=['category'], numerical_columns=['value'])
    assert result.index.tolist() == [10, 20, 30, 40]
    assert result.columns.tolist() == ['value', 'category']
    assert result['value'].tolist() == [1.0, 5.0, 5.0, 5.0]
    assert pd.api.types.is_integer_dtype(result['category'])
    assert np.isfinite(result.to_numpy(dtype=float)).all()
    pd.testing.assert_frame_equal(data, original)
    assert processor.last_report['sections']['basic_info']['row_count'] == 4


def test_all_missing_selected_columns_are_not_dropped(processor):
    data = pd.DataFrame({'value': [np.nan, np.nan], 'category': [None, None]})
    result = processor.preprocess_data(data, categorical_columns=['category'], numerical_columns=['value'], generate_report=False)
    assert result.shape == (2, 2)
    assert result['value'].tolist() == [0.0, 0.0]
    assert result['category'].tolist() == [0, 0]


def test_nullable_integer_column_can_receive_fractional_median(processor):
    data = pd.DataFrame({'value': pd.Series([1, None, 4], dtype='Int64')})
    result = processor.preprocess_data(data, [], ['value'])
    assert result['value'].tolist() == [1.0, 2.5, 4.0]


def test_named_config_applies_transform_and_validation(tmp_path):
    processor = DataPreprocessor(config_dir=str(tmp_path))
    config = {'validation_rules': {'value': {'type': 'integer', 'range': {'min': 1, 'max': 5}}},
              'transformers': {'value': {'type': 'integer'}}, 'cleaning': {}}
    processor.config_manager.save_config('numeric', config)
    loaded = DataPreprocessor('numeric', config_dir=str(tmp_path))
    assert loaded.preprocess_data(pd.DataFrame({'value': ['2', '4']}), [], ['value'])['value'].tolist() == [2, 4]
    with pytest.raises(ValueError):
        loaded.preprocess_data(pd.DataFrame({'value': ['9']}), [], ['value'])


def test_nullable_integer_named_config_accepts_optional_missing_values(processor):
    processor._apply_config({
        'validation_rules': {'value': {'type': 'integer', 'required': False,
                                      'range': {'min': 1, 'max': 5}}},
        'transformers': {'value': {'type': 'integer'}}, 'cleaning': {}})
    data = pd.DataFrame({'value': pd.Series([1, None, 4], dtype='Int64')})
    result = processor.preprocess_data(data, [], ['value'])
    assert result['value'].tolist() == [1.0, 2.5, 4.0]
    with pytest.raises(ValueError):
        processor.preprocess_data(pd.DataFrame({'value': [1.5, 4]}), [], ['value'])


@pytest.mark.parametrize('category, numeric', [(['missing'], ['value']), (['value'], ['value']), ([], ['value', 'value'])])
def test_invalid_column_selection_is_rejected(processor, category, numeric):
    with pytest.raises(ValueError):
        processor.preprocess_data(pd.DataFrame({'value': [1, 2]}), category, numeric)


@pytest.mark.parametrize('value', ['bad', float('inf')])
def test_invalid_numeric_values_are_rejected(processor, value):
    with pytest.raises(ValueError):
        processor.preprocess_data(pd.DataFrame({'value': [1, value]}), [], ['value'])


def test_config_round_trip(tmp_path):
    processor = DataPreprocessor(config_dir=str(tmp_path))
    processor.save_config('default')
    loaded = DataPreprocessor('default', config_dir=str(tmp_path))
    assert loaded._get_current_config() == processor._get_current_config()


def test_empty_data_is_rejected(processor):
    with pytest.raises(ValueError):
        processor.preprocess_data(pd.DataFrame(), [], [])
