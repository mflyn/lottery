import json

import pytest

from src.core.generators.fusion.config import FusionConfig
from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator
from tests.unit.test_fusion_features import history


@pytest.mark.parametrize('kind',['ssq','dlt'])
def test_top_search_uses_same_profile_window_and_unrounded_F(kind,tmp_path,monkeypatch):
    from scripts import find_top_ssq,find_top_dlt
    module=find_top_ssq if kind=='ssq' else find_top_dlt
    function=module.find_top_ssq if kind=='ssq' else module.find_top_dlt
    cls=SSQNumberEvaluator if kind=='ssq' else DLTNumberEvaluator
    data=history(kind,12)
    path=tmp_path/'history.json'; path.write_text(json.dumps({'data':data.to_dict('records')}))
    report=tmp_path/'top.md'
    monkeypatch.setattr(module,'passes_pattern_filters',lambda main: True)
    cfg=FusionConfig(weights=(1,2,3,4,5,6),reference_samples=300)
    results=function(top_k=3,periods=5,pool_size=6 if kind=='ssq' else 5,
                     out_path=str(report),config=cfg,history_file=str(path))
    assert len(results)==3
    assert [r['total_score'] for r in results]==sorted([r['total_score'] for r in results],reverse=True)
    evaluator=cls(str(path))
    for item in results:
        numbers=(item['red_numbers'],item['blue_number']) if kind=='ssq' else (item['front_numbers'],item['back_numbers'])
        standalone=evaluator.evaluate(*numbers,periods=5,config=cfg)
        assert item['total_score']==pytest.approx(standalone['total_score'],abs=1e-12)
        assert item['snapshot_hash']==standalone['fusion']['snapshot_hash']
    assert '/100' not in report.read_text()
    assert '融合效用 F' in report.read_text()


@pytest.mark.parametrize('kind',['ssq','dlt'])
def test_equal_score_search_caps_results_and_orders_ties(kind,tmp_path,monkeypatch):
    from scripts import find_top_ssq,find_top_dlt
    module=find_top_ssq if kind=='ssq' else find_top_dlt
    function=module.find_top_ssq if kind=='ssq' else module.find_top_dlt
    path=tmp_path/'history.json'
    path.write_text(json.dumps({'data':history(kind,12).to_dict('records')}))
    monkeypatch.setattr(module,'passes_pattern_filters',lambda main:True)
    results=function(top_k=3,periods=5,pool_size=6 if kind=='ssq' else 5,
                     config=FusionConfig(weights=(0,)*6,reference_samples=300),history_file=str(path))
    assert len(results)==3
    assert all(r['total_score']==0 for r in results)
    if kind=='ssq':
        assert [r['blue_number'] for r in results]==[13,14,15]
    else:
        assert [r['back_numbers'] for r in results]==[[2,3],[2,4],[2,5]]
