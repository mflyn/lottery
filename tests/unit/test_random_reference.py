"""The displayed percentage is an empirical comparison under uniform Q0."""
from dataclasses import replace
from threading import Event

import numpy as np
import pandas as pd
import pytest

from src.core.generators.fusion.config import FusionConfig, FusionCancelled
from src.core.generators.fusion.features import FusionFeatureContext
from src.core.generators.fusion.history import FusionHistorySnapshot
from src.core.generators.fusion.objective import FusionPortfolioObjective
from src.core.generators.fusion.percentile import (
    RandomReferenceConfig, RandomReferenceSummary, summarize_scores,
    reference_scores, compare_random_reference, scoring_fingerprint,
)


def context(lottery='ssq', **kwargs):
    return FusionFeatureContext(FusionHistorySnapshot.from_data(lottery,pd.DataFrame()),
                               FusionConfig(reference_samples=300,**kwargs))


def test_strict_exceedance_ties_and_known_confidence_interval():
    settings=RandomReferenceConfig(samples=5)
    result=summarize_scores(np.array([1.,2.,3.,3.,4.]),3.,1,'a'*64,'b'*64,settings)
    assert (result.below,result.tied,result.above)==(2,2,1)
    assert result.exceed_percent==40
    assert result.tied_percent==40
    assert result.interval_95[0] < 40 < result.interval_95[1]
    assert '2,000' not in result.display_text()
    assert '5' in result.display_text()


def test_equal_scores_are_not_exceeded_and_tolerance_is_explicit():
    settings=RandomReferenceConfig(samples=4)
    result=summarize_scores(np.array([0.,1e-13,-1e-13,0.]),0.,1,'a'*64,'b'*64,settings)
    assert result.exceed_percent==0
    assert result.tied_percent==100
    assert result.interval_95[0]==0
    upper=summarize_scores(np.array([-4.,-3.,-2.,-1.]),0.,1,'a'*64,'b'*64,settings)
    assert upper.exceed_percent==100
    assert upper.interval_95[1]==100


@pytest.mark.parametrize('kwargs',[{'samples':0},{'samples':True},{'samples':2.5},
                                  {'seed':-1},{'tie_atol':float('nan')},{'tie_atol':-1}])
def test_invalid_reference_settings_rejected(kwargs):
    with pytest.raises(ValueError): RandomReferenceConfig(**kwargs)


@pytest.mark.parametrize('lottery',['ssq','dlt'])
@pytest.mark.parametrize('count',[1,3])
def test_reference_is_reproducible_and_does_not_mutate_global_rng(lottery,count):
    ctx=context(lottery)
    settings=RandomReferenceConfig(samples=30,seed=123)
    np.random.seed(55); before=np.random.get_state()
    first=reference_scores(ctx,count,settings)
    after=np.random.get_state()
    np.testing.assert_array_equal(before[1],after[1])
    assert before[2:]==after[2:]
    np.testing.assert_array_equal(first,reference_scores(ctx,count,settings))
    assert not first.flags.writeable
    with pytest.raises(ValueError): first.setflags(write=True)
    assert len(first)==30 and np.isfinite(first).all()


def test_reference_uses_actual_same_cardinality_objective(monkeypatch):
    ctx=context()
    original=FusionPortfolioObjective.__init__
    sizes=[]
    def observe(self,features,tickets):
        sizes.append(len(tickets))
        assert len(set(tickets))==len(tickets)
        original(self,features,tickets)
    monkeypatch.setattr(FusionPortfolioObjective,'__init__',observe)
    reference_scores(ctx,7,RandomReferenceConfig(samples=11,seed=987))
    assert sizes==[7]*11


def test_cache_signature_tracks_F_and_ignores_sampling_settings():
    base=FusionConfig(reference_samples=300)
    assert scoring_fingerprint(base)==scoring_fingerprint(replace(base,seed=7,temperature=.7,chains=1,steps=100,burn_in=20))
    for cfg in (replace(base,weights=(1,0,0,0,0,0)),replace(base,rho=0),replace(base,beta=4),replace(base,reference_seed=3)):
        assert scoring_fingerprint(base)!=scoring_fingerprint(cfg)


def test_summary_round_trip_validates_context_and_counts():
    ctx=context()
    ticket=((1,7,12,18,25,33),(8,))
    score=FusionPortfolioObjective(ctx,[ticket]).score
    summary=compare_random_reference(ctx,score,1,RandomReferenceConfig(samples=25))
    restored=RandomReferenceSummary.from_dict(summary.to_dict())
    restored.validate_context(ctx,score,1)
    assert restored.to_dict()==summary.to_dict()
    with pytest.raises(ValueError): restored.validate_context(ctx,score,2)
    with pytest.raises(ValueError): restored.validate_context(ctx,score+.1,1)
    damaged=summary.to_dict(); damaged['below']+=1
    with pytest.raises(ValueError): RandomReferenceSummary.from_dict(damaged)


def test_cancellation_during_reference_build():
    event=Event()
    def progress(done,total):
        if done >= 25: event.set()
    with pytest.raises(FusionCancelled):
        reference_scores(context(),2,RandomReferenceConfig(samples=100,seed=666),event,progress)


@pytest.mark.parametrize('lottery',['ssq','dlt'])
def test_reference_attachment_preserves_generated_tickets_F_and_replays(lottery):
    import json
    from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator
    from src.core.generators.fusion.result import FusionResult
    cfg=FusionConfig(seed=18,steps=80,burn_in=20,chains=1,reference_samples=300)
    snap=FusionHistorySnapshot.from_data(lottery,pd.DataFrame())
    gen=MaximumEntropyFusionGenerator(lottery)
    plain=gen.generate_portfolio(3,snap,cfg,reference_config=None)
    calibrated=gen.generate_portfolio(3,snap,cfg,reference_config=RandomReferenceConfig(samples=30))
    assert calibrated.tickets==plain.tickets
    assert calibrated.score==plain.score
    assert calibrated.chains==plain.chains
    assert calibrated.random_reference.count==3
    payload=json.loads(json.dumps(calibrated.to_dict()))
    restored=FusionResult.from_dict(payload)
    assert restored.random_reference.to_dict()==calibrated.random_reference.to_dict()
    assert '严格超过约' in restored.to_markdown(details=False)
    assert '每组 3 注' in restored.to_markdown()
    brief=restored.to_markdown(details=False)
    detailed=restored.to_markdown(details=True)
    score_text=f'{restored.score:.6f}'
    assert score_text not in brief
    assert detailed.index('严格超过约') < detailed.index(score_text)
    assert score_text in detailed
    broken=json.loads(json.dumps(payload)); broken['random_reference']['count']=1
    with pytest.raises(ValueError): FusionResult.from_dict(broken)
    del payload['random_reference']
    assert FusionResult.from_dict(payload).random_reference is None


def test_evaluation_F_unchanged_by_comparison_and_summary_export(tmp_path):
    import json
    from src.core.evaluators.ssq_evaluator import SSQNumberEvaluator
    path=tmp_path/'history.json'; path.write_text('{"data": []}')
    evaluator=SSQNumberEvaluator(str(path))
    numbers=([1,7,12,18,25,33],8)
    cfg=FusionConfig(reference_samples=300)
    plain=evaluator.evaluate(*numbers,config=cfg,reference_config=None)
    calibrated=evaluator.evaluate(*numbers,config=cfg,reference_config=RandomReferenceConfig(samples=40))
    assert calibrated['total_score']==plain['total_score']
    assert calibrated['scores']==plain['scores']
    summary=calibrated['fusion']['random_reference']
    assert summary['count']==1 and summary['samples']==40
    assert 0 <= summary['exceed_percent'] <= 100


def test_cancel_during_generation_reference_stage():
    from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator
    stop=Event()
    def progress(done,total):
        if done>=25: stop.set()
    cfg=FusionConfig(seed=11,steps=60,burn_in=10,chains=1,reference_samples=300)
    snap=FusionHistorySnapshot.from_data('ssq',pd.DataFrame())
    with pytest.raises(FusionCancelled):
        MaximumEntropyFusionGenerator('ssq').generate_portfolio(
            2,snap,cfg,cancel_event=stop,reference_config=RandomReferenceConfig(samples=80,seed=10001),reference_progress=progress)


def test_summary_normalizes_numpy_integers_for_json_export():
    import json
    settings=RandomReferenceConfig(samples=3)
    summary=summarize_scores(np.array([-1.,0.,1.]),0.,np.int64(1),'a'*64,'b'*64,settings)
    payload=json.loads(json.dumps(summary.to_dict(),allow_nan=False))
    assert payload['count']==1 and payload['below']==1


def test_changed_history_cannot_reuse_reference_distribution():
    cfg=FusionConfig(weights=(1,0,0,0,0,0),reference_samples=300)
    empty=FusionFeatureContext(FusionHistorySnapshot.from_data('ssq',pd.DataFrame()),cfg)
    data=pd.DataFrame([dict(draw_num='2026001',red_numbers=[1,2,3,4,5,6],blue_number=1)])
    observed=FusionFeatureContext(FusionHistorySnapshot.from_data('ssq',data),cfg)
    settings=RandomReferenceConfig(samples=12,seed=721)
    a=reference_scores(empty,1,settings)
    b=reference_scores(observed,1,settings)
    assert np.all(a==0)
    assert not np.array_equal(a,b)
    assert reference_scores(empty,1,settings) is a


@pytest.mark.parametrize('target',[True,float('nan'),'invalid'])
def test_invalid_target_score_is_rejected(target):
    with pytest.raises(ValueError):
        summarize_scores(np.array([0.]),target,1,'a'*64,'b'*64,RandomReferenceConfig(samples=1))
