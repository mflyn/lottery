"""Shared adapter: descriptive evaluation and recommendation use one utility."""
from dataclasses import replace

import pandas as pd

from ..generators.fusion.config import FusionConfig, positive_int, check_cancel
from ..generators.fusion.features import FusionFeatureContext
from ..generators.fusion.history import FusionHistorySnapshot
from ..generators.fusion.objective import FusionPortfolioObjective, validate_ticket
from ..generators.fusion.result import FusionResult
from ..generators.fusion.percentile import DEFAULT_REFERENCE, attach_random_reference

DEFAULT_PERIODS = object()


class FusionEvaluationMixin:
    def prepare_fusion_context(self, periods=DEFAULT_PERIODS, config=None,
                               force_reload=False, snapshot=None, cancel_event=None):
        config = config or FusionConfig()
        check_cancel(cancel_event)
        if snapshot is None:
            data = self.load_history(force_reload=force_reload)
            window = config.history_periods if periods is DEFAULT_PERIODS else (
                max(1,len(data)) if periods is None else positive_int(periods,'历史期数'))
            config = replace(config,history_periods=window)
            snapshot = FusionHistorySnapshot.from_data(self.lottery_type,pd.DataFrame(data),window)
        else:
            if snapshot.lottery_type != self.lottery_type:
                raise ValueError('评价彩种与历史快照不一致')
            config = replace(config,history_periods=snapshot.requested_periods)
        key = (snapshot.digest,config.digest)
        cached = self._cache.get('fusion_context')
        if cached is None or cached[0] != key:
            # All descriptive caches must use exactly the same historical slice.
            self.clear_cache()
            context = FusionFeatureContext(snapshot,config,cancel_event)
            self._cache['fusion_context'] = (key,context)
        else:
            context = cached[1]
        return context

    def score_ticket(self, ticket, context):
        """Fast candidate-search entry point: never reads history from disk."""
        return FusionPortfolioObjective(context,[ticket]).score

    def _evaluate_fusion(self, ticket, periods=DEFAULT_PERIODS, force_reload=False,
                         config=None, snapshot=None, cancel_event=None,
                         reference_config=DEFAULT_REFERENCE, reference_progress=None):
        context = self.prepare_fusion_context(periods,config,force_reload,snapshot,cancel_event)
        ticket = validate_ticket(ticket,context.areas)
        canonical = context.snapshot
        rows = []
        for issue,t in zip(canonical.issues,canonical.tickets):
            row = {'draw_num':issue}
            if self.lottery_type == 'ssq':
                row.update(red_numbers=list(t[0]),blue_number=t[1][0])
            else:
                row.update(front_numbers=list(t[0]),back_numbers=list(t[1]))
            rows.append(row)
        numbers = (list(ticket[0]),ticket[1][0]) if self.lottery_type == 'ssq' else tuple(map(list,ticket))
        frequency = self._analyze_frequency(*numbers,rows,len(rows))
        missing = self._analyze_missing(*numbers,rows)
        patterns = self._analyze_patterns(numbers[0]) if self.lottery_type == 'ssq' else self._analyze_patterns(*numbers)
        historical = self._check_historical(*numbers,rows)
        historical['observed_periods'] = len(rows)
        groups = [missing['red_details'],[missing['blue_detail']]] if self.lottery_type=='ssq' else [missing['front_details'],missing['back_details']]
        for area,details in enumerate(groups):
            for detail in details:
                detail['censored'] = bool(context.stats[area]['censored'][detail['number']-1])
                if detail['censored']:
                    detail['classification'] = '观察下界（至少）'
        objective = FusionPortfolioObjective(context,[ticket])
        result = FusionResult(canonical,context.config,(ticket,),tuple(objective.factors),
                              tuple(map(tuple,objective.features)),(),-1,'deterministic_evaluation',
                              tuple(context.diagnostics()))
        result = attach_random_reference(result,context,reference_config,cancel_event,reference_progress)
        check_cancel(cancel_event)
        scores = dict(zip(('H','T','C','R','E','D'),map(float,objective.factors)))
        scores['total'] = objective.score
        return {'frequency':frequency,'missing':missing,'pattern':patterns,'historical':historical,
                'scores':scores,'total_score':objective.score,'rating':'单注融合效用（K=1）','stars':'',
                'fusion':result.to_dict(),'_periods_used':len(rows),
                'suggestions':['采用与融合推荐相同的特征和权重，F越大越符合当前偏好。',
                               '单注K=1，整注相似成本D=0；组合评分需对整组重新计算。',
                               '频率、遗漏、形态详情描述同一历史快照；观察下界已作标记。']}
