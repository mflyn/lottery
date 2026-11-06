import pandas as pd
import pytest
from src.core.analyzers import FrequencyAnalyzer
from src.core.exceptions import AnalysisError


@pytest.mark.parametrize('representation', ['lists', 'strings', 'expanded'])
@pytest.mark.parametrize('lottery_type', ['ssq', 'dlt'])
def test_frequency_accepts_supported_number_representations(representation, lottery_type):
    if lottery_type == 'ssq':
        data = pd.DataFrame({'red_numbers': [[1, 2, 3, 10, 20, 30]], 'blue_number': [3]}, index=[7])
        main, secondary = 'red_ball', 'blue_ball'
    else:
        data = pd.DataFrame({'front_numbers': [[1, 2, 3, 10, 20]], 'back_numbers': [[3, 8]]}, index=[7])
        main, secondary = 'front_area', 'back_area'
    if representation == 'strings':
        for column in data.columns:
            if column.endswith('numbers'):
                data[column] = data[column].map(lambda values: ','.join(map(str, values)))
    elif representation == 'expanded':
        data = pd.DataFrame({
            **{('red_' if lottery_type == 'ssq' else 'front_') + str(i + 1): [number]
               for i, number in enumerate([1, 2, 3, 10, 20, 30] if lottery_type == 'ssq' else [1, 2, 3, 10, 20])},
            **({'blue_1': [3]} if lottery_type == 'ssq' else {'back_1': [3], 'back_2': [8]})
        }, index=[7])
    original = data.copy(deep=True)
    result = FrequencyAnalyzer(lottery_type).analyze(data)['data']
    assert result[main]['frequency'][1] == 1
    assert result[secondary]['frequency'][3] == 1
    pd.testing.assert_frame_equal(data, original)


def test_frequency_rejects_malformed_history():
    data = pd.DataFrame({'front_numbers': [[1, 2, 3, 4, 99]], 'back_numbers': [[1, 2]]})
    with pytest.raises(AnalysisError):
        FrequencyAnalyzer('dlt').analyze(data)
