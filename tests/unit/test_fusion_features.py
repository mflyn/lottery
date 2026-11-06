"""Contracts for the approved fusion model, independent of any GUI."""
from dataclasses import FrozenInstanceError, replace
from threading import Event

import numpy as np
import pandas as pd
import pytest

from src.core.generators.fusion.config import FusionConfig, FusionCancelled
from src.core.generators.fusion.history import FusionHistorySnapshot
from src.core.generators.fusion.features import FusionFeatureContext


def history(lottery='ssq', count=12):
    rows = []
    for i in range(1, count + 1):
        row = {'draw_num': f'2026{i:03d}'}
        if lottery == 'ssq':
            row.update(red_numbers=[1, 7, 12, 18, 25, 33], blue_number=(i-1) % 16+1)
        else:
            row['draw_num'] = f'26{i:03d}'
            row.update(front_numbers=[1, 8, 16, 24, 35], back_numbers=[1, (i-1) % 11+2])
        rows.append(row)
    return pd.DataFrame(rows)


@pytest.mark.parametrize('kwargs', [
    {'temperature': 0}, {'temperature': float('nan')}, {'temperature': float('inf')},
    {'weights': (-1, 0, 0, 0, 0, 0)}, {'weights': (1, 2)},
    {'seed': True}, {'seed': -1}, {'history_periods': 0}, {'history_periods': 2.5},
    {'steps': 10, 'burn_in': 10}, {'reference_samples': 1}, {'beta': 0},
    {'area_weights': (0, 0)}, {'rho': 2}, {'windows': (0, 20, 30)},
])
def test_invalid_config_rejected(kwargs):
    with pytest.raises(ValueError):
        FusionConfig(**kwargs)


def test_config_frozen_normalized_and_hashable():
    config = FusionConfig(weights=[1, 1, 0, 0, 0, 0])
    assert config.weights == (.5, .5, 0, 0, 0, 0)
    assert hash(config)
    with pytest.raises(FrozenInstanceError):
        config.seed = 1
    assert FusionConfig().budget(100) == (20000, 5000)


def test_normalized_weights_survive_seed_replacement_and_json_reconstruction():
    config = FusionConfig(weights=(1,2,3,4,5,6), window_weights=(1,2,6), area_weights=(2,1))
    seeded = replace(config, seed=42)
    assert seeded.weights == config.weights
    assert seeded.window_weights == config.window_weights
    assert seeded.area_weights == config.area_weights
    assert FusionConfig(**seeded.to_dict()).digest == seeded.digest


def test_snapshot_sort_dedup_cutoff_and_independence():
    df = history()
    duplicate = pd.concat([df.iloc[::-1], df.iloc[[0]]], ignore_index=True)
    snapshot = FusionHistorySnapshot.from_data('ssq', duplicate, periods=5)
    assert snapshot.issues == tuple(f'2026{i:03d}' for i in range(12, 7, -1))
    assert snapshot.duplicates_removed == 1
    original_hash = snapshot.digest
    duplicate.at[0, 'red_numbers'][0] = 2
    assert snapshot.tickets[0][0] == (1, 7, 12, 18, 25, 33)
    assert snapshot.digest == original_hash


def test_conflicting_duplicate_and_invalid_numbers_rejected():
    df = history()
    df.loc[1, 'draw_num'] = df.loc[0, 'draw_num']
    with pytest.raises(ValueError, match='冲突'):
        FusionHistorySnapshot.from_data('ssq', df)
    df = history()
    df.at[0, 'red_numbers'] = [True, 7, 12, 18, 25, 33]
    with pytest.raises(ValueError):
        FusionHistorySnapshot.from_data('ssq', df)


def test_dlt_native_five_digit_issue_and_legacy_alias_deduplicate():
    df = history('dlt', 3)
    df['draw_num'] = ['26123', '26124', '26125']
    alias = df.iloc[[2]].copy(); alias['draw_num'] = '2026125'
    snap = FusionHistorySnapshot.from_data('dlt', pd.concat([alias, df], ignore_index=True))
    assert snap.issues == ('26125','26124','26123')
    assert snap.duplicates_removed == 1
    assert not snap.has_gaps
    older = df.iloc[[0]].copy(); older['draw_num'] = '07001'
    assert FusionHistorySnapshot.from_data('dlt', older).issues == ('07001',)


@pytest.mark.parametrize('lottery', ['ssq', 'dlt'])
def test_features_bounded_both_zones_and_omission_censoring(lottery):
    df = history(lottery)
    before = df.copy(deep=True)
    snapshot = FusionHistorySnapshot.from_data(lottery, df)
    context = FusionFeatureContext(snapshot, FusionConfig(reference_samples=300))
    values = context.ticket_features(snapshot.tickets[0])
    assert -1 <= values[0] <= 1
    assert all(0 <= x <= 1 for x in values[1:])
    for (n, k), stats in zip(snapshot.areas, context.stats):
        assert stats['inclusion'].sum() == pytest.approx(k)
        assert stats['target'].sum() == pytest.approx(1)
        assert len(stats['missing']) == n
    assert context.stats[0]['missing'][1] == len(df)
    assert context.stats[0]['censored'][1]
    assert context.stats[0]['missing'][0] == 0
    pd.testing.assert_frame_equal(df, before)


def test_dlt_back_history_contributes_to_frequency_and_coverage():
    a = history('dlt')
    b = a.copy()
    b['back_numbers'] = [[11, 12] for _ in range(len(b))]
    cfg = FusionConfig(reference_samples=300)
    ca = FusionFeatureContext(FusionHistorySnapshot.from_data('dlt', a), cfg)
    cb = FusionFeatureContext(FusionHistorySnapshot.from_data('dlt', b), cfg)
    ticket = ((1, 8, 16, 24, 35), (11, 12))
    assert cb.ticket_features(ticket)[0] > ca.ticket_features(ticket)[0]
    assert not np.allclose(ca.stats[1]['target'], cb.stats[1]['target'])


def test_empty_history_and_gaps_are_explicit():
    empty = FusionHistorySnapshot.from_data('ssq', pd.DataFrame())
    ctx = FusionFeatureContext(empty, FusionConfig(reference_samples=300))
    assert ctx.ticket_features(((1, 2, 3, 4, 5, 6), (7,)))[0] == 0
    assert ctx.ticket_features(((1, 2, 3, 4, 5, 6), (7,)))[3] == 0
    np.testing.assert_allclose(ctx.stats[0]['target'], np.full(33, 1/33))
    snap = FusionHistorySnapshot.from_data('ssq', history().drop(index=5))
    assert snap.has_gaps
    assert snap.to_dict()['has_gaps']


def test_reference_is_seed_independent_and_preparation_cancellable():
    snap = FusionHistorySnapshot.from_data('ssq', history())
    a = FusionFeatureContext(snap, FusionConfig(seed=1, reference_samples=300))
    b = FusionFeatureContext(snap, FusionConfig(seed=2, reference_samples=300))
    assert a.ticket_features(snap.tickets[0]) == b.ticket_features(snap.tickets[0])
    stop = Event(); stop.set()
    with pytest.raises(FusionCancelled):
        FusionFeatureContext(snap, FusionConfig(), stop)
