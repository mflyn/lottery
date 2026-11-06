"""Symmetric Metropolis sampling of exp(K F / tau), without post-selection."""
from dataclasses import replace
import math

import numpy as np
import pandas as pd

from ..base import NumberGenerator
from .config import AREAS, FusionConfig, check_cancel, positive_int
from .history import FusionHistorySnapshot
from .features import FusionFeatureContext
from .objective import FusionPortfolioObjective
from .result import FusionResult
from .uniform import uniform_ticket, unrank_combination, uniform_portfolio
from .percentile import DEFAULT_REFERENCE, attach_random_reference


def propose_ticket(old, areas, weights, rng):
    if rng.random() >= .8:
        return uniform_ticket(areas,rng)
    a = int(rng.choice(len(areas),p=weights))
    n,k = areas[a]
    if n == k:
        return old
    selected = list(old[a])
    index = int(rng.integers(k))
    complement = [x for x in range(1,n+1) if x not in selected]
    selected[index] = complement[int(rng.integers(n-k))]
    result = list(old); result[a] = tuple(sorted(selected))
    return tuple(result)


def proposal_probability(old, new, areas, weights):
    """Exact single-ticket proposal mass, also useful for finite-space audits."""
    probability = .2/math.prod(math.comb(n,k) for n,k in areas)
    changed = [a for a in range(len(areas)) if old[a] != new[a]]
    if len(changed) == 1:
        a = changed[0]; n,k = areas[a]
        if len(set(old[a])-set(new[a])) == 1:
            probability += .8*weights[a]/(k*(n-k))
    elif not changed:
        probability += sum(.8*w for (n,k),w in zip(areas,weights) if n == k)
    return probability


def acceptance_probability(delta, count, temperature):
    return 1. if delta >= 0 else math.exp(count*delta/temperature)


def accept_move(delta, count, temperature, rng):
    if delta >= 0:
        return True
    uniform = rng.random()
    return uniform == 0 or math.log(uniform) <= count*delta/temperature


class MaximumEntropyFusionGenerator(NumberGenerator):
    def __init__(self, lottery_type, config=None):
        if lottery_type not in AREAS:
            raise ValueError('不支持的彩种')
        self.lottery_type = lottery_type
        self.fusion_config = config or FusionConfig()

    def generate(self, count=1, snapshot=None, config=None, **kwargs):
        config = config or self.fusion_config
        snapshot = snapshot or FusionHistorySnapshot.from_data(self.lottery_type,pd.DataFrame(),config.history_periods)
        return self.generate_portfolio(count,snapshot,config,**kwargs).numbers

    def generate_portfolio(self, count, snapshot, config=None, cancel_event=None, progress=None,
                           reference_config=DEFAULT_REFERENCE, reference_progress=None):
        count = positive_int(count,'注数',maximum=100)
        config = config or self.fusion_config
        steps,burn = config.budget(count)
        if snapshot.lottery_type != self.lottery_type:
            raise ValueError('快照与生成彩种不一致')
        check_cancel(cancel_event)
        if config.seed is None:
            config = replace(config,seed=int(np.random.SeedSequence().entropy))
        streams = np.random.SeedSequence(config.seed).spawn(config.chains+1)
        selection_rng = np.random.default_rng(streams[-1])
        selected = int(selection_rng.integers(config.chains))
        context = FusionFeatureContext(snapshot,config,cancel_event)
        final_tickets, diagnostics = None, []
        neutral = not any(config.weights)
        if neutral:
            final_tickets = uniform_portfolio(count,context.areas,selection_rng)
            selected = -1
        else:
            for chain in range(config.chains):
                rng = np.random.default_rng(streams[chain])
                state = FusionPortfolioObjective(context,uniform_portfolio(count,context.areas,rng))
                trace, accepted, duplicate, best = [], 0, 0, state.score
                factor_blocks = []
                for step in range(steps):
                    if step % 100 == 0:
                        check_cancel(cancel_event)
                        if progress:
                            progress(chain*steps+step,config.chains*steps)
                        check_cancel(cancel_event)
                    index = int(rng.integers(count))
                    ticket = propose_ticket(state.tickets[index],context.areas,config.area_weights,rng)
                    if any(ticket == t for j,t in enumerate(state.tickets) if j != index):
                        duplicate += 1
                    else:
                        proposed = state.propose(index,ticket)
                        if accept_move(proposed.score-state.score,count,config.temperature,rng):
                            state.accept(proposed); accepted += 1
                    best = max(best,state.score)
                    if step >= burn:
                        trace.append(state.score)
                        if (step-burn) % 100 == 0:
                            factor_blocks.append([float(v) for v in state.factors])
                diagnostics.append({'steps': steps,'burn_in': burn,'acceptance_rate': accepted/steps,
                                    'duplicate_proposals': duplicate,'F_mean': float(np.mean(trace)),
                                    'F_std': float(np.std(trace)), 'F_final': state.score,'F_best_seen': best,
                                    'F_block_means': [float(np.mean(trace[i:i+100])) for i in range(0,len(trace),100)],
                                    'factor_trace_every_100': factor_blocks})
                if chain == selected:
                    final_tickets = tuple(state.tickets)
        check_cancel(cancel_event)
        # Recompute the explanation from scratch, avoiding accumulated rounding error.
        final = FusionPortfolioObjective(context,final_tickets)
        if progress:
            progress(config.chains*steps,config.chains*steps)
        check_cancel(cancel_event)
        result = FusionResult(snapshot,config,tuple(final.tickets),tuple(final.factors),tuple(map(tuple,final.features)),
                              tuple(diagnostics),selected,'exact_uniform' if neutral else 'finite_step_metropolis',tuple(context.diagnostics()))
        return attach_random_reference(result,context,reference_config,cancel_event,reference_progress)
