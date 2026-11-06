"""Strict F exceedance against uniform legal portfolios; never changes F."""
from collections import OrderedDict
from dataclasses import asdict, dataclass, fields, replace
from hashlib import sha256
import json
import math
from numbers import Real
import threading

import numpy as np

from .config import VERSION, finite, positive_int, check_cancel
from .objective import FusionPortfolioObjective
from .uniform import uniform_portfolio

REFERENCE_VERSION = 'uniform-fusion-reference-1'
_CACHE = OrderedDict()
_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class RandomReferenceConfig:
    samples: int = 2000
    seed: int = 20261104
    tie_atol: float = 1e-12

    def __post_init__(self):
        object.__setattr__(self,'samples',positive_int(self.samples,'参照样本数',maximum=100000))
        object.__setattr__(self,'seed',positive_int(self.seed,'参照种子',minimum=0))
        object.__setattr__(self,'tie_atol',finite(self.tie_atol,'同分容差'))


DEFAULT_REFERENCE = RandomReferenceConfig()


def scoring_fingerprint(config):
    non_scoring = {'seed','temperature','chains','steps','burn_in'}
    profile = {k:v for k,v in config.to_dict().items() if k not in non_scoring}
    return sha256(json.dumps({'score_version':VERSION,**profile},sort_keys=True).encode()).hexdigest()


def wilson_interval(successes,total):
    z = 1.959963984540054
    p = successes/total
    denominator = 1+z*z/total
    center = (p+z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return (0. if successes==0 else max(0.,center-half),
            1. if successes==total else min(1.,center+half))


@dataclass(frozen=True)
class RandomReferenceSummary:
    score: float
    count: int
    samples: int
    seed: int
    tie_atol: float
    below: int
    tied: int
    above: int
    snapshot_hash: str
    scoring_hash: str
    reference_hash: str

    def __post_init__(self):
        settings=RandomReferenceConfig(self.samples,self.seed,self.tie_atol)
        object.__setattr__(self,'count',positive_int(self.count,'参照注数',maximum=100))
        for name in ('samples','seed','tie_atol'):
            object.__setattr__(self,name,getattr(settings,name))
        if isinstance(self.score,bool) or not isinstance(self.score,Real) or not math.isfinite(self.score):
            raise ValueError('参照目标 F 必须是有限数值')
        object.__setattr__(self,'score',float(self.score))
        for name in ('below','tied','above'):
            object.__setattr__(self,name,positive_int(getattr(self,name),name,minimum=0))
        if self.below+self.tied+self.above != settings.samples:
            raise ValueError('参照计数与样本量不一致')
        for digest in (self.snapshot_hash,self.scoring_hash,self.reference_hash):
            if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('参照哈希无效')

    @property
    def exceed_percent(self):
        return 100*self.below/self.samples

    @property
    def tied_percent(self):
        return 100*self.tied/self.samples

    @property
    def interval_95(self):
        return tuple(100*x for x in wilson_interval(self.below,self.samples))

    def to_dict(self):
        return {'version':REFERENCE_VERSION,'distribution':'uniform_distinct_portfolios',
                'comparison':'strict_with_absolute_tie_tolerance',**asdict(self),
                'exceed_percent':self.exceed_percent,'tied_percent':self.tied_percent,
                'interval_95_percent':list(self.interval_95)}

    @classmethod
    def from_dict(cls,data):
        if data.get('version')!=REFERENCE_VERSION or data.get('distribution')!='uniform_distinct_portfolios' or data.get('comparison')!='strict_with_absolute_tie_tolerance':
            raise ValueError('不兼容的随机参照口径')
        return cls(**{field.name:data[field.name] for field in fields(cls)})

    def validate_context(self,context,score,count):
        if self.count!=count or self.snapshot_hash!=context.snapshot.digest or self.scoring_hash!=scoring_fingerprint(context.config) or not math.isclose(self.score,score,rel_tol=0,abs_tol=1e-12):
            raise ValueError('随机参照与评分、注数或历史参数不一致')

    def headline(self):
        return f'F 严格超过约 {self.exceed_percent:.1f}% 的随机参照组合'

    def display_text(self):
        low,high=self.interval_95
        return (f'{self.headline()}；参照 {self.samples:,} 组、每组 {self.count} 注，'
                f'持平 {self.tied_percent:.1f}%；抽样 95% 区间 {low:.1f}%–{high:.1f}%')


def summarize_scores(scores,target_score,count,snapshot_hash,scoring_hash,settings=DEFAULT_REFERENCE):
    scores=np.asarray(scores,dtype=float)
    if scores.ndim!=1 or len(scores)!=settings.samples or not np.isfinite(scores).all() or isinstance(target_score,bool) or not isinstance(target_score,Real) or not math.isfinite(target_score):
        raise ValueError('随机参照分布必须包含指定数量的有限 F 值')
    delta=scores-target_score
    below=int(np.count_nonzero(delta < -settings.tie_atol))
    tied=int(np.count_nonzero(np.abs(delta) <= settings.tie_atol))
    digest=sha256(scores.astype('<f8').tobytes()).hexdigest()
    return RandomReferenceSummary(float(target_score),count,settings.samples,settings.seed,settings.tie_atol,
                                  below,tied,len(scores)-below-tied,snapshot_hash,scoring_hash,digest)


def reference_scores(context,count,settings=DEFAULT_REFERENCE,cancel_event=None,progress=None):
    count=positive_int(count,'参照注数',maximum=100)
    check_cancel(cancel_event)
    key=(REFERENCE_VERSION,context.snapshot.digest,scoring_fingerprint(context.config),count,settings.samples,settings.seed)
    def notify(done):
        check_cancel(cancel_event)
        if progress: progress(done,settings.samples)
        check_cancel(cancel_event)
    notify(0)
    with _CACHE_LOCK:
        cached=_CACHE.get(key)
        if cached is not None: _CACHE.move_to_end(key)
    if cached is not None:
        notify(settings.samples)
        return cached
    rng=np.random.default_rng(np.random.SeedSequence([settings.seed,count,*[v for area in context.areas for v in area]]))
    scores=np.empty(settings.samples)
    for i in range(settings.samples):
        check_cancel(cancel_event)
        tickets=uniform_portfolio(count,context.areas,rng)
        # Sampling a constant F distribution needs no feature evaluation.
        scores[i]=FusionPortfolioObjective(context,tickets).score if any(context.config.weights) else 0.
        if (i+1)%25==0: notify(i+1)
    notify(settings.samples)
    # Immutable bytes backing prevents callers from re-enabling writes on cache data.
    scores=np.frombuffer(scores.astype('<f8').tobytes(),dtype='<f8')
    with _CACHE_LOCK:
        _CACHE[key]=scores
        _CACHE.move_to_end(key)
        while len(_CACHE)>16: _CACHE.popitem(last=False)
    return scores


def compare_random_reference(context,score,count,settings=DEFAULT_REFERENCE,cancel_event=None,progress=None):
    values=reference_scores(context,count,settings,cancel_event,progress)
    return summarize_scores(values,score,count,context.snapshot.digest,scoring_fingerprint(context.config),settings)


def attach_random_reference(result,context,settings=DEFAULT_REFERENCE,cancel_event=None,progress=None):
    if settings is None:
        return result
    summary=compare_random_reference(context,result.score,len(result.tickets),settings,cancel_event,progress)
    return replace(result,random_reference=summary)
