"""Official rules: 2019/19019 and 2026/26014; additional bets only cover floating prizes."""
import pandas as pd
import pytest
from src.core.dlt_calculator import DLTCalculator

DRAW = [1, 2, 3, 4, 5, 1, 2]
NEW_FIXED = [(5, 0, 3, 5000, 6666), (4, 2, 3, 5000, 6666),
             (4, 1, 4, 300, 380), (4, 0, 5, 150, 200), (3, 2, 5, 150, 200),
             (3, 1, 6, 15, 18), (2, 2, 6, 15, 18),
             (3, 0, 7, 5, 7), (2, 1, 7, 5, 7), (1, 2, 7, 5, 7), (0, 2, 7, 5, 7)]
OLD_FIXED = [(5, 0, 3, 10000), (4, 2, 4, 3000), (4, 1, 5, 300),
             (3, 2, 6, 200), (4, 0, 7, 100), (3, 1, 8, 15),
             (2, 2, 8, 15), (3, 0, 9, 5), (2, 1, 9, 5), (1, 2, 9, 5), (0, 2, 9, 5)]


def bet(front, back):
    return list(range(1, front + 1)) + list(range(6, 11 - front)) + list(range(1, back + 1)) + list(range(3, 5 - back))


@pytest.mark.parametrize('front,back,level,low,high', NEW_FIXED)
@pytest.mark.parametrize('pool,high_pool', [(0, False), (799999999.99, False), (800000000, True)])
@pytest.mark.parametrize('additional', [False, True])
def test_new_fixed_prizes(front, back, level, low, high, pool, high_pool, additional):
    assert DLTCalculator().check_prize(bet(front, back), DRAW, additional, pool) == (level, high if high_pool else low)


@pytest.mark.parametrize('front,back,level,amount', OLD_FIXED)
@pytest.mark.parametrize('additional', [False, True])
def test_legacy_prizes_before_26014(front, back, level, amount, additional):
    assert DLTCalculator().check_prize(bet(front, back), DRAW, additional, 900000000, draw_issue='26013') == (level, amount)


@pytest.mark.parametrize('issue,level,amount', [('26013', 9, 5), ('26014', 7, 7), ('2026014', 7, 7)])
def test_rule_transition(issue, level, amount):
    assert DLTCalculator().check_prize(bet(0, 2), DRAW, prize_pool=800000000, draw_issue=issue) == (level, amount)


@pytest.mark.parametrize('back,level', [(2, 1), (1, 2)])
def test_floating_prizes_require_official_amount(back, level):
    calculator = DLTCalculator()
    assert calculator.check_prize(bet(5, back), DRAW) == (level, None)
    assert calculator.check_prize(bet(5, back), DRAW, floating_prizes={level: 1234567}) == (level, 1234567)
    assert calculator.check_prize(bet(5, back), DRAW, True, floating_prizes={level: 1234567}) == (level, 2222220)


def test_unknown_pool_does_not_guess_new_fixed_amount():
    assert DLTCalculator().check_prize(bet(5, 0), DRAW, prize_pool=None) == (3, None)


@pytest.mark.parametrize('method,args', [
    ('check_complex_prize', ([1, 2, 3, 4, 5, 6], [1, 2], DRAW)),
    ('check_dantuo_prize', ([1, 2, 3, 4], [5, 6], [1], [2, 3], DRAW)),
])
def test_grouped_bets_use_matching_rule_version(method, args):
    calculator = DLTCalculator()
    current = getattr(calculator, method)(*args, draw_issue='26014')
    legacy = getattr(calculator, method)(*args, draw_issue='26013')
    assert set(current) == set(range(1, 8))
    assert set(legacy) == set(range(1, 10))
    assert sum(current.values()) == sum(legacy.values())


@pytest.mark.parametrize('issue', ['19018', 'bad', '260140'])
def test_unsupported_issues_are_not_silently_assigned_a_rule(issue):
    with pytest.raises(ValueError):
        DLTCalculator().check_prize(DRAW, DRAW, draw_issue=issue)


def test_context_uses_previous_pool_not_current_post_draw_balance():
    history = pd.DataFrame([
        {'draw_num': '26015', 'front_numbers': DRAW[:5], 'back_numbers': DRAW[5:],
         'prize_pool': 700000000, 'first_prize_amount': 6000000},
        {'draw_num': '26014', 'front_numbers': [6, 7, 8, 9, 10], 'back_numbers': [3, 4],
         'prize_pool': 800000000, 'first_prize_amount': 0},
    ])
    context = DLTCalculator.get_draw_context(history, '26015', DRAW)
    assert context['prize_pool'] == 800000000
    assert context['floating_prizes'] == {1: 6000000}
    assert DLTCalculator().check_prize(bet(5, 0), DRAW, **context) == (3, 6666)


def test_context_does_not_reuse_payouts_after_manual_number_edit():
    history = pd.DataFrame([{'draw_num': '26015', 'front_numbers': DRAW[:5], 'back_numbers': DRAW[5:],
                             'prize_pool': 700000000, 'first_prize_amount': 6000000}])
    context = DLTCalculator.get_draw_context(history, '26015', bet(4, 2))
    assert context['prize_pool'] is None
    assert context['floating_prizes'] == {}


def test_context_treats_imputed_zero_pool_as_unknown(tmp_path):
    import json
    from src.core.data_manager import LotteryDataManager
    rows = [
        {'draw_num': '26015', 'draw_date': '2026-02-04', 'front_numbers': DRAW[:5],
         'back_numbers': DRAW[5:], 'prize_pool': 900000000, 'sales': 0},
        {'draw_num': '26014', 'draw_date': '2026-02-02', 'front_numbers': [6, 7, 8, 9, 10],
         'back_numbers': [3, 4], 'sales': 0},
    ]
    (tmp_path / 'dlt_history.json').write_text(json.dumps({'data': rows}))
    history = LotteryDataManager(str(tmp_path)).get_history_data('dlt')
    context = DLTCalculator.get_draw_context(history, '26015', DRAW)
    assert context['prize_pool'] is None
    assert DLTCalculator().check_prize(bet(5, 0), DRAW, **context) == (3, None)


@pytest.mark.parametrize('bad_front', [None, float('nan')])
def test_malformed_context_record_does_not_guess_amounts(bad_front):
    context = DLTCalculator.get_draw_context(
        [{'draw_num': '26015', 'front_numbers': bad_front, 'back_numbers': [1, 2]}], '26015', DRAW)
    assert context['prize_pool'] is None
    assert context['floating_prizes'] == {}


def test_mixed_known_and_unknown_prize_summary_is_explicit():
    text = DLTCalculator().format_prize_summary({1: 1, 7: 2}, prize_pool=800000000)
    assert '浮动奖金额以当期开奖公告为准' in text
    assert '已知奖金小计: 14 元' in text
    assert '总奖金:' not in text


def test_known_summary_does_not_add_extra_fixed_awards():
    text = DLTCalculator().format_prize_summary({3: 2, 4: 1}, is_additional=True, prize_pool=800000000)
    assert '总奖金: 13712 元' in text
