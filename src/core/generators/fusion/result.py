"""Portable result with its original scoring context, separate from legacy scores."""
from dataclasses import dataclass
from copy import deepcopy
import platform

import numpy as np
import pandas as pd

from ...models import SSQNumber, DLTNumber
from .config import FusionConfig, VERSION, FACTOR_NAMES
from .features import FusionFeatureContext
from .history import FusionHistorySnapshot
from .objective import FusionPortfolioObjective
from .percentile import RandomReferenceSummary


@dataclass(frozen=True)
class FusionResult:
    snapshot: FusionHistorySnapshot
    config: FusionConfig
    tickets: tuple
    factors: tuple
    ticket_factors: tuple
    chains: tuple
    selected_chain: int
    method: str
    statistics: tuple
    random_reference: RandomReferenceSummary = None

    @property
    def score(self):
        return float(self.config.weights[0]*self.factors[0]-sum(w*v for w,v in zip(self.config.weights[1:],self.factors[1:])))

    @property
    def numbers(self):
        if self.snapshot.lottery_type == 'ssq':
            return [SSQNumber(list(t[0]), t[1][0]) for t in self.tickets]
        return [DLTNumber(list(t[0]), list(t[1])) for t in self.tickets]

    def reevaluate(self):
        return FusionPortfolioObjective(FusionFeatureContext(self.snapshot,self.config), self.tickets).breakdown()

    def to_dict(self):
        contributions = {key: float(w*v*(1 if i == 0 else -1)) for i,(key,w,v) in enumerate(zip(FACTOR_NAMES,self.config.weights,self.factors))}
        ticket_details = []
        for values in self.ticket_factors:
            signed = [float(v*w*(1 if i == 0 else -1)) for i,(v,w) in enumerate(zip(values,self.config.weights))]
            ticket_details.append({'factors': dict(zip(FACTOR_NAMES[:4], map(float,values))),
                                   'contributions': dict(zip(FACTOR_NAMES[:4],signed)), 'q': sum(signed)})
        return {'version': VERSION, 'status': 'complete', 'method': self.method,
                'lottery_type': self.snapshot.lottery_type, 'count': len(self.tickets),
                'tickets': [[list(a) for a in t] for t in self.tickets],
                'factors': dict(zip(FACTOR_NAMES,map(float,self.factors))), 'F': self.score,
                'contributions': contributions, 'ticket_details': ticket_details,
                'config': self.config.to_dict(), 'config_hash': self.config.digest,
                'snapshot': self.snapshot.to_dict(), 'snapshot_hash': self.snapshot.digest,
                'statistics': deepcopy(list(self.statistics)), 'chains': deepcopy(list(self.chains)),
                'selected_chain': self.selected_chain,
                'random_reference': self.random_reference.to_dict() if self.random_reference else None,
                'environment': {'python': platform.python_version(), 'numpy': np.__version__}}

    @classmethod
    def from_dict(cls, payload):
        if payload['version'] != VERSION or payload.get('status') != 'complete':
            raise ValueError('不兼容的融合结果版本或状态')
        config = FusionConfig(**payload['config'])
        source = payload['snapshot']
        rows = []
        for issue, ticket in zip(source['issues'], source['tickets']):
            row = {'draw_num': issue}
            if source['lottery_type'] == 'ssq':
                row.update(red_numbers=ticket[0],blue_number=ticket[1][0])
            else:
                row.update(front_numbers=ticket[0],back_numbers=ticket[1])
            rows.append(row)
        snap = FusionHistorySnapshot.from_data(source['lottery_type'],pd.DataFrame(rows),source['requested_periods'])
        snap = FusionHistorySnapshot(snap.lottery_type,snap.issues,snap.tickets,snap.requested_periods,
                                     source['duplicates_removed'],snap.has_gaps)
        if snap.digest != payload['snapshot_hash'] or config.digest != payload['config_hash']:
            raise ValueError('融合快照或参数校验失败')
        ctx = FusionFeatureContext(snap,config)
        obj = FusionPortfolioObjective(ctx,payload['tickets'])
        reference = RandomReferenceSummary.from_dict(payload['random_reference']) if payload.get('random_reference') is not None else None
        if reference is not None:
            reference.validate_context(ctx,obj.score,len(obj.tickets))
        return cls(snap,config,tuple(obj.tickets),tuple(obj.factors),tuple(map(tuple,obj.features)),
                   tuple(payload['chains']),payload['selected_chain'],payload['method'],tuple(ctx.diagnostics()),reference)

    def to_markdown(self, details=True):
        data = self.to_dict()
        method = {'exact_uniform':'精确均匀抽样',
                  'deterministic_evaluation':'确定性效用评价（K=1，D=0）'}.get(self.method,'有限步近似采样（未声称已收敛）')
        title = '双色球' if self.snapshot.lottery_type == 'ssq' else '大乐透'
        lines = [f'# {title}融合推荐', '', f'{len(self.tickets)} 注', '']
        if self.random_reference:
            lines += [self.random_reference.display_text(), '',
                      '参照为同彩种、同历史、同权重、同注数的均匀随机合法组合。', '']
        else:
            lines += ['随机参照未计算。原始效用可在详细信息中查看。', '']
        lines += [f'截止期：{self.snapshot.issues[0] if self.snapshot.issues else "无历史"}；实际记录：{len(self.snapshot.issues)}', '']
        for i,t in enumerate(self.tickets,1):
            balls = ' | '.join(' '.join(f'{x:02d}' for x in area) for area in t)
            lines.append(f'{i}. {balls}')
        if details:
            lines += ['', '## 评分详细信息', '',
                      f'组合偏好 F={self.score:.6f}；分散程度 1−D={1-self.factors[5]:.4f}；随机性 τ={self.config.temperature:g}', '',
                      f'评价方式：{method}；种子：{self.config.seed}', '',
                      '偏好分数用于解释推荐取舍。历史新颖度为软成本。', '',
                      '## 组合解释', '', '| 因素 | 原值 | 加权贡献 |', '| --- | ---: | ---: |']
            for key in FACTOR_NAMES:
                lines.append(f'| {key} | {data["factors"][key]:.6f} | {data["contributions"][key]:+.6f} |')
            lines += ['', 'H 历史倾向；T 形态成本；C 去热门偏好；R 历史新颖度；E 探索覆盖成本；D 近似重复成本。', '', '## 单注解释', '']
            for i,t in enumerate(data['ticket_details'],1):
                lines.append(f'{i}. q={t["q"]:.6f}；' + '；'.join(f'{key}={v:.4f}（贡献 {t["contributions"][key]:+.4f}）' for key,v in t['factors'].items()))
            lines += ['', '## 复现信息', '', f'算法：{VERSION}', f'配置哈希：{self.config.digest}',
                      f'历史哈希：{self.snapshot.digest}', f'历史说明：{self.snapshot.to_dict()["coverage_note"]}',
                      '未出现号码的遗漏是观察下界；完整快照、参数和截尾标记见同结果的 JSON 导出。',
                      f'参数：{self.config.to_dict()}', f'链诊断：{list(self.chains)}']
        return '\n'.join(lines)+'\n'
