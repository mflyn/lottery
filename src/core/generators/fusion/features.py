"""Bounded preference factors, computed against one immutable snapshot."""
from functools import lru_cache
from itertools import combinations
import math
import threading

import numpy as np

from .config import check_cancel

_REFERENCES = {}
_REFERENCE_LOCK = threading.Lock()


def shape_matrix(numbers, n):
    x = np.asarray(numbers, dtype=float)
    k = x.shape[1]
    columns = [(x % 2).mean(axis=1), (x > n // 2).mean(axis=1),
               (x.sum(axis=1) - k) / (k * (n - 1)),
               (x[:, -1] - x[:, 0]) / (n - 1),
               (np.diff(x, axis=1) == 1).sum(axis=1) / (k - 1),
               (x <= n // 3).mean(axis=1),
               ((x > n // 3) & (x <= 2 * n // 3)).mean(axis=1)]
    if k >= 3:
        diffs = np.sort(np.column_stack([x[:, j] - x[:, i] for i, j in combinations(range(k), 2)]), axis=1)
        distinct = 1 + (np.diff(diffs, axis=1) != 0).sum(axis=1)
        columns.append((distinct - (k - 1)) / (math.comb(k, 2) - (k - 1)))
    return np.column_stack(columns)


def shape_reference(n, k, samples, seed, cancel_event):
    check_cancel(cancel_event)
    key = (n, k, samples, seed)
    with _REFERENCE_LOCK:
        cached = _REFERENCES.get(key)
    if cached is not None:
        return cached
    rng = np.random.default_rng(np.random.SeedSequence([seed, n, k]))
    batches = []
    for start in range(0, samples, 500):
        check_cancel(cancel_event)
        # iid continuous ranks choose every k-subset with equal probability.
        ranks = rng.random((min(500, samples - start), n))
        numbers = np.sort(np.argpartition(ranks, k-1, axis=1)[:, :k] + 1, axis=1)
        batches.append(shape_matrix(numbers, n))
    phi = np.concatenate(batches)
    mask = phi.var(axis=0) > 0
    phi = phi[:, mask]
    mean = phi.mean(axis=0)
    covariance = np.atleast_2d(np.cov(phi, rowvar=False))
    regularized = .9 * covariance + .1 * np.diag(np.diag(covariance)) + 1e-6 * np.eye(len(mean))
    inverse = np.linalg.inv(regularized)
    reference = (mask, mean, inverse)
    for value in reference:
        value.setflags(write=False)
    check_cancel(cancel_event)
    with _REFERENCE_LOCK:
        # Bound the process-wide cache when many custom configurations are used.
        if len(_REFERENCES) >= 16:
            _REFERENCES.pop(next(iter(_REFERENCES)))
        _REFERENCES[key] = reference
    return reference


def style_cost(area, n):
    k = len(area)
    numbers = set(area)
    longest = 2
    for first, second in combinations(area, 2):
        step, length, value = second-first, 2, second + (second-first)
        while value in numbers:
            length += 1
            value += step
        longest = max(longest, length)
    terms = [(longest-2)/(k-2),
             (max(sum(v % 10 == i for v in area) for i in range(10))-1)/(k-1),
             max(0, sum(v % 5 == 0 for v in area)-1)/(k-1)]
    if n > 31:
        terms.append(min(1., max(0., (sum(v <= 31 for v in area)-(k-2))/2)))
    return float(sum(terms)/len(terms))


class FusionFeatureContext:
    def __init__(self, snapshot, config, cancel_event=None):
        check_cancel(cancel_event)
        if len(snapshot.tickets) > config.history_periods:
            raise ValueError('历史快照超出配置期数，请先截取同一快照')
        self.snapshot, self.config = snapshot, config
        self.areas = snapshot.areas
        self.stats, self.references = [], []
        count = len(snapshot.tickets)
        self.history_masks = []
        for a, (n, k) in enumerate(self.areas):
            check_cancel(cancel_event)
            draws = np.zeros((count, n), dtype=float)
            for j, ticket in enumerate(snapshot.tickets):
                draws[j, np.asarray(ticket[a])-1] = 1
            p0 = k/n
            inclusion = np.zeros(n)
            for window, weight in zip(config.windows, config.window_weights):
                length = min(window, count)
                inclusion += weight * ((draws[:length].sum(axis=0) + config.prior_strength*p0)/(length+config.prior_strength))
            frequency = np.tanh(np.log(inclusion/p0))
            missing = np.full(n, count, dtype=int)
            censored = np.ones(n, dtype=bool)
            trend = np.zeros(n)
            if count:
                ew = np.exp2(-np.arange(count)/config.half_life)
                ew /= ew.sum()
                effective = 1/np.dot(ew, ew)
                recent = (effective*(ew @ draws)+config.prior_strength*p0)/(effective+config.prior_strength)
                trend = np.tanh((recent-inclusion)/p0)
                seen = draws.any(axis=0)
                missing[seen] = draws[:, seen].argmax(axis=0)
                censored[seen] = snapshot.has_gaps
            else:
                frequency[:] = 0
            absence = -np.expm1(missing * np.log1p(-p0))
            target = 1+config.rho*((1-frequency)/2+absence)/2
            target /= target.sum()
            stats = dict(inclusion=inclusion, frequency=frequency, trend=trend,
                         preference=.7*frequency+.3*trend, missing=missing,
                         censored=censored, target=target)
            for value in stats.values():
                value.setflags(write=False)
            self.stats.append(stats)
            self.history_masks.append(draws[:100])
            self.references.append(shape_reference(n, k, config.reference_samples, config.reference_seed, cancel_event) if k >= 2 else None)
        self.stats, self.references = tuple(self.stats), tuple(self.references)
        length = min(100, count)
        self.history_weights = np.exp2(-np.arange(length)/config.half_life)
        if length:
            self.history_weights /= self.history_weights.sum()
        self.ticket_features = lru_cache(maxsize=4096)(self._ticket_features)

    def _ticket_features(self, ticket):
        historical, shape, shape_weight, style, style_weight = 0., 0., 0., 0., 0.
        similarity = np.zeros(len(self.history_weights))
        for a, ((n, k), numbers, weight) in enumerate(zip(self.areas, ticket, self.config.area_weights)):
            indices = np.asarray(numbers)-1
            historical += weight * self.stats[a]['preference'][indices].mean()
            reference = self.references[a]
            if reference is not None:
                mask, mean, inverse = reference
                diff = shape_matrix([numbers], n)[0, mask]-mean
                if len(diff):
                    distance = max(0., float(diff @ inverse @ diff))
                    shape += weight * distance/(len(diff)+distance)
                    shape_weight += weight
            if a == 0:
                style += weight * style_cost(numbers, n)
                style_weight += weight
            elif k == 2:
                style += weight * (numbers[1]-numbers[0] == 1)
                style_weight += weight
            if len(similarity):
                similarity += weight * self.history_masks[a][:, indices].sum(axis=1)/k
        novelty = float(self.history_weights @ (similarity**2))
        return (float(historical), float(shape/shape_weight) if shape_weight else 0.,
                float(style/style_weight) if style_weight else 0., novelty)

    def diagnostics(self):
        return [{name: value.tolist() for name, value in stats.items()} for stats in self.stats]
