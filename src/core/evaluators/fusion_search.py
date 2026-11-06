"""Restricted candidate search ranked by the same K=1 fusion utility."""
import heapq
from itertools import combinations
from pathlib import Path

from ..generators.fusion.config import FACTOR_NAMES, positive_int
from ..generators.fusion.objective import FusionPortfolioObjective
from ..generators.fusion.percentile import compare_random_reference, RandomReferenceSummary


def search_fusion(evaluator,top_k,periods,pool_size,pattern_filter,config=None,out_path=None):
    top_k=positive_int(top_k,'返回数量',maximum=100)
    context=evaluator.prepare_fusion_context(periods=periods,config=config)
    n,k=context.areas[0]
    pool_size=positive_int(pool_size,'候选池',minimum=k,maximum=n)
    preference=context.stats[0]['preference']
    pool=sorted(sorted(range(1,n+1),key=lambda x:(-preference[x-1],x))[:pool_size])
    tail_n,tail_k=context.areas[1]
    tails=list(combinations(range(1,tail_n+1),tail_k))
    exact=set()
    for row in evaluator.history_data:
        if evaluator.lottery_type=='ssq':
            exact.add((tuple(sorted(row['red_numbers'])),(int(row['blue_number']),)))
        else:
            exact.add((tuple(sorted(row['front_numbers'])),tuple(sorted(row['back_numbers']))))

    def candidates():
        for main in combinations(pool,k):
            if not pattern_filter(main):
                continue
            for tail in tails:
                ticket=(main,tail)
                if ticket not in exact:
                    yield evaluator.score_ticket(ticket,context),ticket

    # Bound memory and return exactly top_k at most; equal F uses numeric order.
    ranked=heapq.nsmallest(top_k,candidates(),key=lambda item:(-item[0],item[1]))
    results=[]
    for score,ticket in ranked:
        item={'total_score':score,'snapshot_hash':context.snapshot.digest,
              'config_hash':context.config.digest,'score_method':'fusion_K1',
              'factors':FusionPortfolioObjective(context,[ticket]).breakdown()}
        item['random_reference']=compare_random_reference(context,score,1).to_dict()
        if evaluator.lottery_type=='ssq':
            item.update(red_numbers=list(ticket[0]),blue_number=ticket[1][0])
        else:
            item.update(front_numbers=list(ticket[0]),back_numbers=list(ticket[1]))
        results.append(item)
    if out_path:
        lines=['# 最高评分候选：融合效用 F','',
               '在候选池与形态筛选范围内按单注 K=1 排序；同分按号码稳定排序。',
               f'历史范围：请求 {context.config.history_periods} 条，实际 {len(context.snapshot.issues)} 条',
               f'配置：{context.config.to_dict()}',f'历史哈希：{context.snapshot.digest}',
               f'配置哈希：{context.config.digest}','']
        for i,(_,ticket) in enumerate(ranked,1):
            balls=' | '.join(' '.join(f'{v:02d}' for v in a) for a in ticket)
            lines.append(f'{i}. {balls} | 融合效用 F={results[i-1]["total_score"]:.8f}')
            reference=RandomReferenceSummary.from_dict(results[i-1]['random_reference'])
            lines.append(f'   {reference.display_text()}')
            lines.append(f'   参照种子={reference.seed}；同分容差={reference.tie_atol:g}；参照哈希={reference.reference_hash}')
        path=Path(out_path); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return results
