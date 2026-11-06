"""Numerical contracts and end-to-end reproducibility of fusion sampling."""
from dataclasses import replace
from itertools import combinations
from threading import Event
import json
import math

import numpy as np
import pandas as pd
import pytest

from src.core.generators.fusion.config import FusionConfig, FusionCancelled
from src.core.generators.fusion.history import FusionHistorySnapshot
from src.core.generators.fusion.features import FusionFeatureContext
from src.core.generators.fusion.objective import FusionPortfolioObjective, diversity_cost
from src.core.generators.fusion.sampler import MaximumEntropyFusionGenerator, proposal_probability, acceptance_probability, propose_ticket
from src.core.generators.fusion.result import FusionResult


def short_config(**kwargs):
    return FusionConfig(**dict(dict(seed=42, steps=120, burn_in=20, chains=2, reference_samples=300), **kwargs))


def test_exact_transition_matrix_has_the_declared_stationary_distribution():
    # Exact finite calculation, not a noisy histogram or a copy of the sampler.
    tickets = [(x,) for x in combinations(range(1, 6), 2)]
    states = list(combinations(range(10), 2))
    objective = np.array([sum(tickets[i][0][0] for i in s)/10 for s in states])
    target = np.exp(2*objective/.3); target /= target.sum()
    q = np.zeros((45, 45))
    for i, s in enumerate(states):
        for j, t in enumerate(states):
            removed, added = set(s)-set(t), set(t)-set(s)
            if len(removed) == len(added) == 1:
                q[i, j] = proposal_probability(tickets[removed.pop()], tickets[added.pop()], ((5, 2),), (1.,))/2
        q[i, i] = 1-q[i].sum()
    np.testing.assert_allclose(q, q.T, atol=1e-15)
    transition = np.zeros_like(q)
    for i in range(45):
        for j in range(45):
            if i != j:
                transition[i,j] = q[i,j]*acceptance_probability(objective[j]-objective[i], 2, .3)
        transition[i,i] = 1-transition[i].sum()
    np.testing.assert_allclose(target @ transition, target, atol=1e-14)
    np.testing.assert_allclose(target[:,None]*transition, target[None,:]*transition.T, atol=1e-14)


def test_actual_proposal_kernel_matches_exact_probabilities():
    rng = np.random.default_rng(33)
    old = ((1, 2),)
    counts = {t: 0 for t in [(x,) for x in combinations(range(1, 6), 2)]}
    for _ in range(30000):
        counts[propose_ticket(old, ((5,2),), (1.,), rng)] += 1
    for t, count in counts.items():
        assert count/30000 == pytest.approx(proposal_probability(old,t,((5,2),),(1.,)), abs=.01)


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
@pytest.mark.parametrize('count', [1, 100])
def test_uniform_output_is_legal_unique_reproducible_and_explained(lottery, count):
    from src.core.generators.factory import create_generator
    snapshot = FusionHistorySnapshot.from_data(lottery, pd.DataFrame())
    config = short_config(weights=(0,)*6)
    result = create_generator('fusion', lottery).generate_portfolio(count, snapshot, config)
    again = MaximumEntropyFusionGenerator(lottery).generate_portfolio(count, snapshot, config)
    assert result.tickets == again.tickets
    assert len(result.numbers) == len(set(result.tickets)) == count
    assert all(number.validate() for number in result.numbers)
    assert result.score == 0
    assert result.to_dict()['method'] == 'exact_uniform'
    assert result.to_dict()['config']['seed'] == 42


def test_incremental_scoring_equals_full_recomputation_and_is_permutation_invariant():
    snap = FusionHistorySnapshot.from_data('ssq', pd.DataFrame())
    cfg = short_config()
    ctx = FusionFeatureContext(snap, cfg)
    tickets = [((1,2,3,4,5,6),(7,)), ((2,8,10,15,22,33),(8,)), ((3,8,11,16,25,32),(9,))]
    obj = FusionPortfolioObjective(ctx, tickets)
    rng = np.random.default_rng(21)
    for _ in range(100):
        index = int(rng.integers(3))
        ticket = propose_ticket(obj.tickets[index], ctx.areas, cfg.area_weights, rng)
        if ticket in obj.tickets:
            continue
        proposal = obj.propose(index, ticket)
        changed = obj.tickets.copy(); changed[index] = ticket
        full = FusionPortfolioObjective(ctx, changed)
        assert proposal.score == pytest.approx(full.score, abs=1e-12)
        obj.accept(proposal)
    reverse = FusionPortfolioObjective(ctx, obj.tickets[::-1])
    assert reverse.score == pytest.approx(obj.score, abs=1e-12)


def test_diversity_distinguishes_equal_exposure_counts():
    a = [((1,2,3),), ((1,2,4),), ((4,5,6),)]
    b = [((1,2,3),), ((1,4,5),), ((2,4,6),)]
    assert diversity_cost(a, ((6,3),), (1.,), 8) == pytest.approx(.5383001179990968)
    assert diversity_cost(b, ((6,3),), (1.,), 8) == pytest.approx(1/3)


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
def test_sampling_export_round_trip_and_snapshot_reevaluation(lottery):
    from tests.unit.test_fusion_features import history
    data = history(lottery)
    config = short_config()
    snapshot = FusionHistorySnapshot.from_data(lottery, data)
    result = MaximumEntropyFusionGenerator(lottery).generate_portfolio(3, snapshot, config)
    data.iloc[0, 0] = '2099001'
    exported = json.loads(json.dumps(result.to_dict(), allow_nan=False))
    restored = FusionResult.from_dict(exported)
    assert restored.reevaluate()['F'] == pytest.approx(result.score)
    assert result.score == pytest.approx(sum(exported['contributions'].values()))
    assert exported['snapshot_hash'] == snapshot.digest
    assert exported['method'] == 'finite_step_metropolis'
    assert len(exported['chains']) == 2
    assert '有限步近似' in result.to_markdown()
    assert 'H' in result.to_markdown(details=True)
    assert result.tickets == MaximumEntropyFusionGenerator(lottery).generate_portfolio(3, snapshot, config).tickets


def test_cancel_during_sampling_and_reject_bad_count():
    snapshot = FusionHistorySnapshot.from_data('ssq', pd.DataFrame())
    gen = MaximumEntropyFusionGenerator('ssq')
    event = Event()
    def progress(done, total):
        if done >= 100:
            event.set()
    with pytest.raises(FusionCancelled):
        gen.generate_portfolio(2, snapshot, short_config(steps=1000), event, progress)
    for count in (0, 101, True, 2.5):
        with pytest.raises(ValueError):
            gen.generate_portfolio(count, snapshot, short_config())


def test_extreme_beta_and_low_temperature_stay_finite():
    cfg = short_config(beta=10000, temperature=1e-300)
    snap = FusionHistorySnapshot.from_data('ssq', pd.DataFrame())
    result = MaximumEntropyFusionGenerator('ssq').generate_portfolio(2, snap, cfg)
    assert math.isfinite(result.score)
    assert 0 <= result.reevaluate()['D'] <= 1


def test_custom_weight_export_restores_its_own_configuration():
    cfg = short_config(weights=(1,2,3,4,5,6), area_weights=(2,1), window_weights=(1,2,6))
    snap = FusionHistorySnapshot.from_data('ssq', pd.DataFrame())
    result = MaximumEntropyFusionGenerator('ssq').generate_portfolio(2, snap, cfg)
    payload = json.loads(json.dumps(result.to_dict()))
    restored = FusionResult.from_dict(payload)
    assert restored.config.digest == result.config.digest
    assert restored.tickets == result.tickets
    assert restored.score == pytest.approx(result.score, abs=1e-12)
