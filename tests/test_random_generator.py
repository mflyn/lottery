"""Generators return validated number objects through generate(count)."""
import pytest
from src.core.generators.random_generator import RandomGenerator
from src.core.number_generator import LotteryNumberGenerator
from src.core.models import DLTNumber, SSQNumber


@pytest.mark.parametrize('lottery_type, number_class', [('ssq', SSQNumber), ('dlt', DLTNumber)])
@pytest.mark.parametrize('count', [0, 1, 5])
def test_generate_typed_valid_numbers(lottery_type, number_class, count):
    numbers = RandomGenerator(lottery_type).generate(count)
    assert len(numbers) == count
    for number in numbers:
        assert isinstance(number, number_class)
        assert number.validate()
        main = number.red if lottery_type == 'ssq' else number.front
        assert main == sorted(set(main))


@pytest.mark.parametrize('generator_class', [RandomGenerator, LotteryNumberGenerator])
@pytest.mark.parametrize('lottery_type', ['invalid', '', None])
def test_invalid_lottery_type(generator_class, lottery_type):
    with pytest.raises(ValueError):
        generator_class(lottery_type)


@pytest.mark.parametrize('count', [-1, 1.5, True, '2'])
def test_invalid_generation_count(count):
    with pytest.raises(ValueError):
        RandomGenerator('ssq').generate(count)
