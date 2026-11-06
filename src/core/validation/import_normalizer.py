"""Convert file imports to the canonical history schema without repairing bad data."""

import json
import math
import re
from datetime import date
from numbers import Integral, Real
from typing import Dict, List

import pandas as pd


def _integer(value) -> int:
    if isinstance(value, bool):
        raise ValueError('号码不能为布尔值')
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, str) and re.fullmatch(r'[0-9]+', value.strip()):
        return int(value.strip())
    raise ValueError(f'号码必须为整数: {value!r}')


def _number_list(value) -> List[int]:
    if isinstance(value, str):
        text = value.strip()
        value = json.loads(text) if text.startswith('[') else re.split(r'[\s,]+', text)
    if not isinstance(value, (list, tuple)):
        raise ValueError('号码区域必须为列表或数字字符串')
    numbers = [_integer(number) for number in value]
    if len(numbers) != len(set(numbers)):
        raise ValueError('同一号码区域不能包含重复号码')
    return sorted(numbers)


def _check_finite_values(value):
    if isinstance(value, Real) and not math.isfinite(value):
        raise ValueError('导入数据不能包含 NaN 或 Infinity')
    if isinstance(value, dict):
        for item in value.values():
            _check_finite_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_finite_values(item)


def _date_string(value) -> str:
    # Numeric values are ambiguous (Unix nanoseconds, YYYYMMDD, or Excel serials).
    if not isinstance(value, (str, date)):
        raise ValueError('日期必须为日期文本或日期对象，不能为裸数字')
    parsed = pd.Timestamp(value)
    if pd.isna(parsed):
        raise ValueError('日期不能为空')
    return parsed.strftime('%Y-%m-%d')


def normalize_import_data(records: List[Dict], lottery_type: str) -> pd.DataFrame:
    """Normalize JSON/CSV/Excel records; reject malformed rows as a complete batch."""
    if not isinstance(records, list) or not records or not all(isinstance(row, dict) for row in records):
        raise ValueError('导入数据必须为非空的记录列表')
    if lottery_type not in ('ssq', 'dlt'):
        raise ValueError(f'不支持的彩票类型: {lottery_type}')
    _check_finite_values(records)

    data = pd.DataFrame(records)
    for legacy, canonical in [('date', 'draw_date'), ('issue', 'draw_num')]:
        if canonical not in data.columns and legacy in data.columns:
            data = data.rename(columns={legacy: canonical})

    area_columns = ['red_numbers', 'blue_number'] if lottery_type == 'ssq' else ['front_numbers', 'back_numbers']
    if 'numbers' in data.columns and any(column not in data.columns for column in area_columns):
        # A legacy combined string has seven numbers; uniqueness applies within each area.
        def split_combined(value):
            if isinstance(value, str):
                text = value.strip()
                value = json.loads(text) if text.startswith('[') else re.split(r'[\s,]+', text)
            if not isinstance(value, (list, tuple)) or len(value) != 7:
                raise ValueError('合并号码必须包含7个整数')
            return [_integer(number) for number in value]

        combined = data['numbers'].map(split_combined)
        split_at = 6 if lottery_type == 'ssq' else 5
        if area_columns[0] not in data.columns:
            data[area_columns[0]] = combined.map(lambda numbers: numbers[:split_at])
        if area_columns[1] not in data.columns:
            data[area_columns[1]] = combined.map(
                lambda numbers: numbers[-1] if lottery_type == 'ssq' else numbers[split_at:])

    required = ['draw_num', 'draw_date'] + area_columns
    if any(column not in data.columns for column in required):
        raise ValueError(f'缺少必需字段: {required}')
    if data[required].isnull().any().any():
        raise ValueError('必需字段不能有空值')

    data['draw_num'] = data['draw_num'].map(lambda issue: str(issue).strip())
    data['draw_date'] = data['draw_date'].map(_date_string)
    data[area_columns[0]] = data[area_columns[0]].map(_number_list)
    data[area_columns[1]] = data[area_columns[1]].map(_integer if lottery_type == 'ssq' else _number_list)
    for column in ['sales', 'prize_pool']:
        if column not in data.columns:
            data[column] = 0
        data[column] = pd.to_numeric(data[column], errors='raise').fillna(0)
        if not data[column].map(lambda value: math.isfinite(value) and value >= 0).all():
            raise ValueError(f'{column}必须为有限的非负数值')
    data = data.drop(columns=['date', 'issue', 'numbers'], errors='ignore')
    # DataFrame fills absent optional fields with NaN; emit JSON null for those gaps.
    return data.astype(object).where(data.notna(), None)
