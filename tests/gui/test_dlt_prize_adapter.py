"""Run the actual prize callback against lightweight controls, without creating Tk."""
import subprocess
import sys


def test_dlt_callback_uses_pre_draw_pool_and_no_fixed_additional_prize():
    script = '''
from types import SimpleNamespace
import pandas as pd
from src.core.dlt_calculator import DLTCalculator
from src.gui.main_window import DLTFrame
history = pd.DataFrame([
    {'draw_num':'26015','front_numbers':[1,2,3,4,5],'back_numbers':[1,2], 'prize_pool':700000000},
    {'draw_num':'26014','front_numbers':[6,7,8,9,10],'back_numbers':[3,4], 'prize_pool':800000000}])
output = []
frame = SimpleNamespace(calculator=DLTCalculator(),
    data_manager=SimpleNamespace(get_history_data=lambda kind: history),
    prize_result_label=SimpleNamespace(config=lambda **values: output.append(values['text'])))
fields = {'draw_entry':'1 2 3 4 5 1 2', 'check_issue_entry':'26015',
    'check_additional_bet':True, 'my_bet_front_entry':'1 2 3 4 5', 'my_bet_back_entry':'3 4',
    'my_bet_front_dan_entry':'', 'my_bet_front_tuo_entry':'',
    'my_bet_back_dan_entry':'', 'my_bet_back_tuo_entry':''}
for name, value in fields.items():
    setattr(frame, name, SimpleNamespace(get=lambda value=value: value))
DLTFrame.check_prize(frame)
assert '3等奖: 1 注 x 6666 元' in output[-1], output
assert '总奖金: 6666 元' in output[-1], output
'''
    result = subprocess.run([sys.executable, '-c', script], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr + result.stdout
