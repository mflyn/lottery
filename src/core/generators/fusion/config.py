"""Immutable, validated inputs shared by scoring, sampling and exports."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from numbers import Integral, Real

VERSION = 'maxent-fusion-1'
FACTOR_NAMES = ('H', 'T', 'C', 'R', 'E', 'D')
AREAS = {'ssq': ((33, 6), (16, 1)), 'dlt': ((35, 5), (12, 2))}


class FusionCancelled(Exception):
    """A requested cancellation, never a successful partial portfolio."""


def check_cancel(event):
    if event is not None and event.is_set():
        raise FusionCancelled('融合生成已取消')


def positive_int(value, name, minimum=1, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f'{name}必须是{minimum}以上的整数' + (f'，且不超过{maximum}' if maximum is not None else ''))
    return int(value)


def finite(value, name, minimum=0, strict=False):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < minimum or (strict and value == minimum):
        raise ValueError(f'{name}必须为有效' + ('正数' if strict else '非负数'))
    return float(value)


def normalized(values, length, name, allow_zero=False):
    try:
        values = tuple(finite(x, name) for x in values)
    except TypeError as exc:
        raise ValueError(f'{name}必须为数值序列') from exc
    if len(values) != length:
        raise ValueError(f'{name}必须包含{length}项')
    peak = max(values)
    if peak == 0:
        if allow_zero:
            return values
        raise ValueError(f'{name}不能全部为零')
    # Preserve the canonical IEEE values on JSON restore / dataclasses.replace.
    # Renormalizing a unit-sum vector can change its last bit and break its hash.
    if peak <= 1 and math.isclose(math.fsum(values), 1., rel_tol=1e-15, abs_tol=0.):
        return values
    scaled = tuple(x / peak for x in values)
    total = math.fsum(scaled)
    return tuple(x / total for x in scaled)


@dataclass(frozen=True)
class FusionConfig:
    weights: tuple = (.25, .15, .10, .05, .20, .25)
    temperature: float = .15
    history_periods: int = 180
    seed: int = None
    windows: tuple = (20, 60, 180)
    window_weights: tuple = (.2, .3, .5)
    prior_strength: float = 20.
    half_life: float = 20.
    area_weights: tuple = (.7, .3)
    rho: float = 1.
    beta: float = 8.
    reference_samples: int = 20000
    reference_seed: int = 20261103
    chains: int = 4
    steps: int = None
    burn_in: int = None

    def __post_init__(self):
        for name, length, allow_zero in [('weights', 6, True), ('area_weights', 2, False), ('window_weights', 3, False)]:
            object.__setattr__(self, name, normalized(getattr(self, name), length, name, allow_zero))
        # SSQ shape/style have only a main-area term, so its weight must exist.
        if self.area_weights[0] == 0:
            raise ValueError('主区权重必须为正')
        for name in ('temperature', 'prior_strength', 'half_life', 'beta'):
            object.__setattr__(self, name, finite(getattr(self, name), name, strict=True))
        object.__setattr__(self, 'rho', finite(self.rho, 'rho'))
        if self.rho > 1:
            raise ValueError('rho必须在0到1之间')
        for name, minimum in [('history_periods', 1), ('reference_samples', 2), ('reference_seed', 0), ('chains', 1)]:
            object.__setattr__(self, name, positive_int(getattr(self, name), name, minimum))
        try:
            windows = tuple(positive_int(x, '窗口') for x in self.windows)
        except TypeError as exc:
            raise ValueError('窗口必须为整数序列') from exc
        if len(windows) != 3:
            raise ValueError('必须指定三个历史窗口')
        object.__setattr__(self, 'windows', windows)
        for name, minimum in [('seed', 0), ('steps', 1), ('burn_in', 0)]:
            if getattr(self, name) is not None:
                object.__setattr__(self, name, positive_int(getattr(self, name), name, minimum))
        if self.steps is not None and self.burn_in is not None and self.burn_in >= self.steps:
            raise ValueError('采样步数必须大于预热步数')

    def budget(self, count):
        positive_int(count, '注数', maximum=100)
        steps = self.steps if self.steps is not None else max(5000, 200 * count)
        burn = self.burn_in if self.burn_in is not None else max(1000, 50 * count)
        if burn >= steps:
            raise ValueError('采样步数必须大于预热步数')
        return steps, burn

    def to_dict(self):
        return asdict(self)

    @property
    def digest(self):
        return sha256(json.dumps({'version': VERSION, **self.to_dict()}, sort_keys=True).encode()).hexdigest()
