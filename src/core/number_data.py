"""Normalize lottery ball columns for analysis and feature extraction."""
import json
import re
from numbers import Integral
from typing import List

import pandas as pd


AREAS = {
    'ssq': [('red_numbers', 'red', 6, 33), ('blue_number', 'blue', 1, 16)],
    'dlt': [('front_numbers', 'front', 5, 35), ('back_numbers', 'back', 2, 12)],
}


def _parse_area(value, count: int, maximum: int) -> List[int]:
    if isinstance(value, str):
        text = value.strip()
        value = json.loads(text) if text.startswith('[') else re.split(r'[\s,]+', text)
    elif isinstance(value, Integral):
        value = [value]
    if not isinstance(value, (list, tuple)) or len(value) != count:
        raise ValueError(f'号码区域必须包含{count}个整数')
    numbers = []
    for number in value:
        if isinstance(number, str) and re.fullmatch(r'[0-9]+', number.strip()):
            number = int(number)
        if isinstance(number, bool) or not isinstance(number, Integral) or not 1 <= number <= maximum:
            raise ValueError(f'号码必须为1-{maximum}之间的整数')
        numbers.append(int(number))
    if len(set(numbers)) != count:
        raise ValueError('同一区域的号码不能重复')
    return sorted(numbers)


def normalize_number_data(data: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
    """Accept list/string/expanded columns, preserving row order, index and caller data."""
    if lottery_type not in AREAS:
        raise ValueError(f'不支持的彩票类型: {lottery_type}')
    if not isinstance(data, pd.DataFrame) or data.empty or not data.index.is_unique:
        raise ValueError('输入必须为非空、索引唯一的DataFrame')
    result = data.copy()
    for canonical, prefix, count, maximum in AREAS[lottery_type]:
        columns = [f'{prefix}_{i + 1}' for i in range(count)]
        if canonical in result.columns:
            values = result[canonical]
        elif canonical == 'blue_number' and 'blue' in result.columns:
            values = result['blue']
        elif canonical == 'blue_number' and 'blue_numbers' in result.columns:
            values = result['blue_numbers']
        elif all(column in result.columns for column in columns):
            values = pd.Series(result[columns].values.tolist(), index=result.index)
        else:
            raise ValueError(f'缺少号码列: {canonical}或{columns}')
        parsed = values.map(lambda value: _parse_area(value, count, maximum))
        result[canonical] = parsed.map(lambda numbers: numbers[0]) if count == 1 else parsed
        for i, column in enumerate(columns):
            result[column] = parsed.map(lambda numbers: numbers[i])
    return result
