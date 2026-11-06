import pandas as pd
import pytest
from src.core.validation import DataCleaner, DataValidator


@pytest.mark.parametrize('lottery_type, issue, valid', [
    ('ssq', '2026125', True), ('ssq', '20260001', False),
    ('ssq', '26125', False), ('dlt', '26125', True),
    ('dlt', '07001', True), ('dlt', '2026125', False),
])
def test_issue_format(lottery_type, issue, valid):
    row = {'draw_num': issue, 'draw_date': '2026-11-01'}
    if lottery_type == 'ssq':
        row.update(red_numbers=[1, 5, 12, 18, 25, 33], blue_number=8)
    else:
        row.update(front_numbers=[5, 12, 18, 25, 35], back_numbers=[3, 8])
    report = DataValidator(lottery_type).validate(pd.DataFrame([row]))
    assert report['valid'] is valid, report['errors']


def test_ssq_cleaning_preserves_seven_digit_issue():
    data = pd.DataFrame([{'draw_num': '2026125', 'draw_date': '2026-11-01',
                          'red_numbers': [1, 5, 12, 18, 25, 33], 'blue_number': 8}])
    cleaned, report = DataCleaner('ssq').clean_data(data)
    assert cleaned['draw_num'].tolist() == ['2026125']
    assert report['validation_result']['valid']


def test_dlt_sequence_uses_two_digit_year():
    data = pd.DataFrame([
        {'draw_num': '24099', 'draw_date': '2024-08-01',
         'front_numbers': [5, 12, 18, 25, 35], 'back_numbers': [3, 8]},
        {'draw_num': '24101', 'draw_date': '2024-08-05',
         'front_numbers': [6, 13, 19, 26, 34], 'back_numbers': [4, 9]},
    ])
    report = DataValidator('dlt').validate(data)
    assert any(warning['rule'] == 'issue_sequence' for warning in report['warnings'])
