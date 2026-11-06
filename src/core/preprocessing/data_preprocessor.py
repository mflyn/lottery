"""Preprocess model tables and lottery records without changing caller data."""
import copy
import json
from numbers import Integral, Real
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder

from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .data_transformer import DataTransformer
from .quality_reporter import DataQualityReporter
from .config_manager import PreprocessingConfigManager
from .preprocessing_logger import PreprocessingLogger
from ..number_data import normalize_number_data


class DataPreprocessor:
    """Selected model columns are imputed/encoded; their row alignment is preserved."""

    def __init__(self, config_name: Optional[str] = None, config_dir: str = 'configs/preprocessing'):
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.reporter = DataQualityReporter()
        self.config_manager = PreprocessingConfigManager(config_dir)
        self.logger = PreprocessingLogger()
        self.last_report = None
        if config_name:
            self.load_config(config_name)
        else:
            self._setup_default_config()

    def _setup_default_config(self):
        self._apply_config(self.config_manager.create_default_config())

    def _apply_config(self, config: Dict):
        if not isinstance(config, dict):
            raise ValueError('预处理配置必须为字典')
        for section in ['validation_rules', 'transformers', 'cleaning']:
            if not isinstance(config.get(section, {}), dict):
                raise ValueError(f'{section}必须为字典')
        validator = DataValidator()
        transformer = DataTransformer()
        for column, rule in config.get('validation_rules', {}).items():
            validator.add_rule(column, 'format', {
                'validator': lambda value, rule=copy.deepcopy(rule): self._validate_value(value, rule)})
        for column, spec in config.get('transformers', {}).items():
            kind = spec.get('type')
            if kind == 'datetime':
                transformer.add_transformer(column, DataTransformer.to_datetime, format=spec.get('format'))
            elif kind in ('integer', 'float', 'numeric'):
                transformer.add_transformer(column, DataTransformer.to_numeric, errors='raise')
            elif kind == 'list':
                transformer.add_transformer(column, self._list_series, sort=spec.get('sort', False))
            else:
                raise ValueError(f'不支持的转换类型: {kind}')
        self._config = copy.deepcopy(config)
        self.validator = validator
        self.transformer = transformer

    @staticmethod
    def _validate_value(value, rule):
        if value is None or (not isinstance(value, (list, tuple)) and pd.isna(value)):
            if rule.get('required', True):
                raise ValueError('必需值不能为空')
            return
        kind = rule.get('type')
        if kind == 'datetime':
            if isinstance(value, (Integral, Real)) or pd.isna(pd.to_datetime(value)):
                raise ValueError('无效日期')
        elif kind == 'list':
            if not isinstance(value, (list, tuple)) or ('length' in rule and len(value) != rule['length']):
                raise ValueError('列表格式或长度不正确')
        elif kind in ('integer', 'float', 'numeric'):
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                raise ValueError('无效数值类型')
            # Pandas apply can expose nullable Int64 scalars as integral floats.
            if kind == 'integer' and int(value) != value:
                raise ValueError('数值必须为整数')
        if 'range' in rule:
            values = value if isinstance(value, (list, tuple)) else [value]
            if not all(rule['range']['min'] <= number <= rule['range']['max'] for number in values):
                raise ValueError('数值超出范围')

    @staticmethod
    def _list_series(series, sort=False):
        def convert(value):
            values = json.loads(value) if isinstance(value, str) else value
            if not isinstance(values, (list, tuple)):
                raise ValueError('列表格式错误')
            return sorted(values) if sort else list(values)
        return series.map(convert)

    def _get_current_config(self) -> Dict:
        return copy.deepcopy(self._config)

    def load_config(self, config_name: str):
        self._apply_config(self.config_manager.load_config(config_name))

    def save_config(self, config_name: str):
        self.config_manager.save_config(config_name, self._get_current_config())

    @staticmethod
    def _model_columns(data, categorical_columns, numerical_columns):
        categorical = list(categorical_columns or [])
        numeric = list(numerical_columns or [])
        selected = categorical + numeric
        if len(selected) != len(set(selected)) or any(column not in data.columns for column in selected):
            raise ValueError('所选列必须存在，且不能重复或同时用于分类和数值处理')
        result = data.copy(deep=True)
        for column in numeric:
            values = pd.to_numeric(result[column], errors='raise').astype(float)
            if np.isinf(values.to_numpy(dtype=float, na_value=np.nan)).any():
                raise ValueError('数值列不能包含Infinity')
            median = values.median() if values.notna().any() else 0.0
            result[column] = values.fillna(median)
        for column in categorical:
            values = result[column]
            nonempty = values.dropna()
            fill = str(nonempty.mode().iloc[0]) if not nonempty.empty else ''
            strings = values.map(lambda value: str(value) if pd.notna(value) else fill)
            encoder = OrdinalEncoder(dtype=np.int64)
            result[column] = encoder.fit_transform(strings.to_frame()).ravel()
        return result

    def _report(self, data):
        # Reports use hashable representations of list-valued lottery columns.
        snapshot = data.copy()
        for column in snapshot.select_dtypes(include=['object']).columns:
            snapshot[column] = snapshot[column].map(
                lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (list, dict)) else value)
        return self.reporter.generate_report(snapshot)

    def preprocess_data(self, data: pd.DataFrame, categorical_columns: List[str] = None,
                        numerical_columns: List[str] = None, generate_report: bool = True) -> pd.DataFrame:
        """Return a DataFrame; invalid inputs raise ValueError instead of changing return type."""
        try:
            if not isinstance(data, pd.DataFrame) or data.empty or not data.columns.is_unique:
                raise ValueError('输入必须为非空且列名唯一的DataFrame')
            self.last_report = None
            prepared = self.transformer.transform(data)
            validation = self.validator.validate(prepared)
            if not validation['valid']:
                raise ValueError('; '.join(validation['errors']))
            if categorical_columns is not None or numerical_columns is not None:
                result = self._model_columns(prepared, categorical_columns, numerical_columns)
            elif any(column in prepared for column in ['red_numbers', 'front_numbers']):
                kind = 'ssq' if 'red_numbers' in prepared else 'dlt'
                result = normalize_number_data(prepared, kind)
                date_column = 'draw_date' if 'draw_date' in result else 'date'
                if date_column in result:
                    result[date_column] = pd.to_datetime(result[date_column], errors='raise')
                if self._config.get('cleaning', {}).get('remove_duplicates', True):
                    columns = [column for column in result if column.startswith(('red_', 'front_', 'back_', 'blue_'))
                               and column.rsplit('_', 1)[-1].isdigit()]
                    if date_column in result:
                        columns.append(date_column)
                    result = result.drop_duplicates(subset=columns)
            else:
                numeric = prepared.select_dtypes(include='number').columns.tolist()
                categorical = [column for column in prepared if column not in numeric]
                result = self._model_columns(prepared, categorical, numeric)
            if generate_report:
                self.last_report = self._report(result)
                self.logger.update_statistics({'final_quality': self.last_report['sections']['basic_info']})
            self.logger.log_operation('preprocess', {'rows_before': len(data), 'rows_after': len(result)})
            return result
        except Exception as exc:
            self.logger.log_error('预处理失败', {'error': str(exc)})
            raise

    def get_preprocessing_summary(self, original_data: pd.DataFrame, processed_data: pd.DataFrame) -> Dict:
        removed = len(original_data) - len(processed_data)
        return {
            'original_shape': original_data.shape,
            'processed_shape': processed_data.shape,
            'cleaning_report': {
                '移除的行数': removed,
                '移除行比例': removed / len(original_data) if len(original_data) else 0,
                '处理前缺失值总数': int(original_data.isnull().sum().sum()),
                '处理后缺失值总数': int(processed_data.isnull().sum().sum()),
            },
            'quality_report': self._report(processed_data),
        }
