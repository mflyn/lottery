"""Single-ticket evaluation must be the same mathematical model as recommendation."""
from dataclasses import replace
import json

import pandas as pd
import pytest

from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
from src.core.evaluators.dlt_evaluator import DLTNumberEvaluator
from src.core.generators.fusion.config import FusionConfig
from src.core.generators.fusion.history import FusionHistorySnapshot
from src.core.generators.fusion.features import FusionFeatureContext
from src.core.generators.fusion.objective import FusionPortfolioObjective
from src.core.generators.fusion.result import FusionResult
from tests.unit.test_fusion_features import history


@pytest.fixture(params=['ssq','dlt'])
def evaluation(request, tmp_path):
    kind = request.param
    data = history(kind,12)
    path = tmp_path / f'{kind}.json'
    path.write_text(json.dumps({'data':data.to_dict('records')}))
    cls = SSQNumberEvaluator if kind == 'ssq' else DLTNumberEvaluator
    numbers = ([1,7,12,18,25,33],8) if kind == 'ssq' else ([1,8,16,24,35],[3,11])
    return kind, cls(str(path)), data, numbers, path


def test_evaluator_delegates_to_same_fusion_objective(evaluation):
    kind,evaluator,data,numbers,_ = evaluation
    cfg = FusionConfig(history_periods=5,weights=(1,2,3,4,5,6),reference_samples=300)
    result = evaluator.evaluate(*numbers,periods=5,config=cfg)
    snapshot = FusionHistorySnapshot.from_data(kind,data,5)
    ticket = (tuple(numbers[0]),(numbers[1],)) if kind=='ssq' else tuple(map(tuple,numbers))
    expected = FusionPortfolioObjective(FusionFeatureContext(snapshot,cfg),[ticket])
    assert result['total_score'] == pytest.approx(expected.score,abs=1e-12)
    assert result['scores']['D'] == 0
    assert set(result['scores']) == {'H','T','C','R','E','D','total'}
    assert sum(result['fusion']['contributions'].values()) == pytest.approx(result['total_score'])
    assert result['fusion']['snapshot_hash'] == snapshot.digest
    assert FusionResult.from_dict(result['fusion']).reevaluate()['F'] == pytest.approx(expected.score)


def test_window_and_exact_match_details_are_consistent(evaluation):
    kind,evaluator,data,_,_ = evaluation
    latest = data.iloc[-1]
    numbers = (latest.red_numbers,int(latest.blue_number)) if kind=='ssq' else (latest.front_numbers,latest.back_numbers)
    result=evaluator.evaluate(*numbers,periods=3)
    assert result['frequency']['periods'] == 3
    assert result['historical']['observed_periods'] == 3
    assert len(result['fusion']['snapshot']['issues']) == 3
    assert result['historical']['exact_match']
    key = 'max_red_match' if kind=='ssq' else 'max_total_match'
    assert result['historical'][key] == (6 if kind=='ssq' else 7)
    assert result['fusion']['method'] == 'deterministic_evaluation'


def test_unseen_omissions_are_lower_bounds_and_empty_history_scores(evaluation):
    kind,evaluator,_,numbers,path = evaluation
    result=evaluator.evaluate(*numbers,periods=2)
    key = 'red_details' if kind=='ssq' else 'front_details'
    missing=evaluator._analyze_missing(*(([2,3,4,5,6,8],1) if kind=='ssq' else ([2,3,4,5,6],[3,4])),evaluator.load_history()[:2])
    assert all(d['missing'] == 2 for d in missing[key])
    path.write_text('{"data": []}')
    empty=evaluator.evaluate(*numbers,force_reload=True)
    assert empty['scores']['H'] == empty['scores']['R'] == empty['scores']['D'] == 0
    assert empty['fusion']['snapshot']['issues'] == []


def test_changed_window_invalidates_cached_statistics(evaluation):
    _,evaluator,_,numbers,_=evaluation
    one=evaluator.evaluate(*numbers,periods=1)
    two=evaluator.evaluate(*numbers,periods=10)
    assert one['frequency']['periods']==1 and two['frequency']['periods']==10
    assert one['fusion']['snapshot_hash'] != two['fusion']['snapshot_hash']


def test_prepared_context_scores_without_reloading_files(evaluation):
    kind,evaluator,_,numbers,path=evaluation
    context=evaluator.prepare_fusion_context(periods=5)
    ticket=(tuple(numbers[0]),(numbers[1],)) if kind=='ssq' else tuple(map(tuple,numbers))
    before=evaluator.score_ticket(ticket,context)
    path.unlink()
    assert evaluator.score_ticket(ticket,context)==before


@pytest.mark.parametrize('periods',[0,-1,True,2.5])
def test_invalid_window_is_rejected(evaluation,periods):
    _,evaluator,_,numbers,_=evaluation
    with pytest.raises(ValueError):
        evaluator.evaluate(*numbers,periods=periods)


def test_parallel_snapshots_do_not_share_descriptive_frequency_cache(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    evaluator=SSQNumberEvaluator(str(tmp_path/'unused.json'))
    first=pd.DataFrame([dict(draw_num='2026001',red_numbers=[1,7,12,18,25,33],blue_number=1)])
    second=first.copy(); second['blue_number']=2
    snapshots=[FusionHistorySnapshot.from_data('ssq',data,1) for data in (first,second)]
    ready,completed=Event(),Event()
    original=evaluator._analyze_frequency
    def ordered(red,blue,rows,periods):
        if rows[0]['blue_number']==1:
            assert ready.wait(3)
            value=original(red,blue,rows,periods)
            completed.set()
            return value
        ready.set()
        assert completed.wait(3)
        return original(red,blue,rows,periods)
    monkeypatch.setattr(evaluator,'_analyze_frequency',ordered)
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(evaluator.evaluate,[1,7,12,18,25,33],1,snapshot=snapshots[0])
        b=pool.submit(evaluator.evaluate,[1,7,12,18,25,33],2,snapshot=snapshots[1])
        for future in (a,b):
            assert future.result()['frequency']['blue_detail']['frequency']==1
