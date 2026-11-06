"""A single bounded objective, with incremental fixed-cardinality replacements."""
from dataclasses import dataclass
from itertools import combinations
from numbers import Integral
import math

import numpy as np


def validate_ticket(ticket, areas):
    if len(ticket) != len(areas):
        raise ValueError('号码区域数量错误')
    canonical = []
    for values, (n, k) in zip(ticket, areas):
        if len(values) != k or any(isinstance(x, bool) or not isinstance(x, Integral) or not 1 <= x <= n for x in values) or len(set(values)) != k:
            raise ValueError('号码不合法')
        canonical.append(tuple(sorted(int(x) for x in values)))
    return tuple(canonical)


def similarity(x, y, areas, weights):
    return sum(w*len(set(a)&set(b))/k for a, b, (_, k), w in zip(x,y,areas,weights))


def smooth_max(values, beta):
    if len(values) == 0:
        return 0.
    values = np.asarray(values)
    peak = float(values.max())
    # expm1/log1p retain the mean-overlap limit even for very small beta.
    return float(np.clip(peak + np.log1p(np.expm1(beta*(values-peak)).mean())/beta, 0, 1))


def diversity_cost(tickets, areas, weights, beta):
    return smooth_max([similarity(a,b,areas,weights) for a,b in combinations(tickets,2)], beta)


def coverage_cost(counts, context, size):
    total = 0.
    for c, stats, (_, k), weight in zip(counts, context.stats, context.areas, context.config.area_weights):
        p, q = c/(size*k), stats['target']
        m = (p+q)/2
        mask = p > 0
        total += weight * (np.dot(p[mask], np.log(p[mask]/m[mask])) + np.dot(q, np.log(q/m)))/(2*math.log(2))
    return float(np.clip(total, 0, 1))


@dataclass
class Replacement:
    index: int
    ticket: tuple
    features: tuple
    counts: list
    row: np.ndarray
    exponential_row: np.ndarray
    pair_total: float
    factors: tuple
    score: float


class FusionPortfolioObjective:
    def __init__(self, context, tickets):
        self.context = context
        self.tickets = [validate_ticket(t, context.areas) for t in tickets]
        self.size = len(self.tickets)
        if not 1 <= self.size <= 100 or len(set(self.tickets)) != self.size:
            raise ValueError('组合必须包含1至100注不重复的号码')
        self.features = np.asarray([context.ticket_features(t) for t in self.tickets])
        self.feature_sum = self.features.sum(axis=0)
        self.memberships = []
        self.counts = []
        for a, (n, _) in enumerate(context.areas):
            matrix = np.zeros((self.size, n), dtype=float)
            for j, t in enumerate(self.tickets):
                matrix[j, np.asarray(t[a])-1] = 1
            self.memberships.append(matrix)
            self.counts.append(matrix.sum(axis=0))
        self.similarities = sum(w*(m @ m.T)/k for m, (_,k),w in zip(self.memberships,context.areas,context.config.area_weights))
        np.fill_diagonal(self.similarities, 0)
        self.upper = np.triu_indices(self.size, 1)
        self.fast_exp = 1e-6 <= context.config.beta <= 50
        self.exponentials = np.zeros_like(self.similarities)
        if self.fast_exp:
            self.exponentials = np.exp(context.config.beta*(self.similarities-1))
            np.fill_diagonal(self.exponentials, 0)
        self.pair_total = float(self.exponentials[self.upper].sum())
        e = coverage_cost(self.counts, context, self.size)
        d = smooth_max(self.similarities[self.upper], context.config.beta)
        self.factors = tuple(self.feature_sum/self.size) + (e,d)
        self.score = self._score(self.factors)

    def _score(self, factors):
        w = self.context.config.weights
        return float(w[0]*factors[0]-sum(x*y for x,y in zip(w[1:], factors[1:])))

    def propose(self, index, ticket):
        ticket = validate_ticket(ticket, self.context.areas)
        if any(ticket == t for j,t in enumerate(self.tickets) if j != index):
            raise ValueError('替换后存在重复完整单注')
        features = self.context.ticket_features(ticket)
        counts, row = [], np.zeros(self.size)
        for a, ((_,k), weight) in enumerate(zip(self.context.areas,self.context.config.area_weights)):
            old, new = np.asarray(self.tickets[index][a])-1, np.asarray(ticket[a])-1
            c = self.counts[a].copy(); c[old] -= 1; c[new] += 1
            counts.append(c)
            row += weight*self.memberships[a][:,new].sum(axis=1)/k
        row[index] = 0
        row = np.clip(row, 0, 1)
        beta = self.context.config.beta
        exp_row = np.zeros(self.size)
        total = self.pair_total
        if self.size == 1:
            d = 0.
        elif self.fast_exp:
            exp_row = np.exp(beta*(row-1)); exp_row[index] = 0
            total += float(exp_row.sum()-self.exponentials[index].sum())
            if total <= max(0., self.pair_total*.01):
                # Recompute when subtracting a dominant pair would lose precision.
                matrix = self.exponentials.copy()
                matrix[index,:] = exp_row; matrix[:,index] = exp_row
                total = float(matrix[self.upper].sum())
            d = float(np.clip(1+math.log(total/len(self.upper[0]))/beta, 0, 1))
        else:
            matrix = self.similarities.copy()
            matrix[index,:] = row; matrix[:,index] = row
            d = smooth_max(matrix[self.upper], beta)
        e = coverage_cost(counts, self.context, self.size)
        means = (self.feature_sum-self.features[index]+features)/self.size
        factors = tuple(means)+(e,d)
        return Replacement(index,ticket,features,counts,row,exp_row,total,factors,self._score(factors))

    def accept(self, proposal):
        i = proposal.index
        self.feature_sum += np.asarray(proposal.features)-self.features[i]
        self.features[i] = proposal.features
        self.tickets[i] = proposal.ticket
        self.counts = proposal.counts
        for a, matrix in enumerate(self.memberships):
            matrix[i] = 0
            matrix[i,np.asarray(proposal.ticket[a])-1] = 1
        self.similarities[i,:] = proposal.row; self.similarities[:,i] = proposal.row
        self.exponentials[i,:] = proposal.exponential_row; self.exponentials[:,i] = proposal.exponential_row
        self.pair_total = proposal.pair_total
        self.factors, self.score = proposal.factors, proposal.score

    def breakdown(self):
        return dict(zip(('H','T','C','R','E','D','F'), self.factors+(self.score,)))
