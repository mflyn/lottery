"""Canonical, detached historical data; no generator loads files implicitly."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

import pandas as pd

from ...number_data import normalize_number_data
from .config import AREAS, positive_int


@dataclass(frozen=True)
class FusionHistorySnapshot:
    lottery_type: str
    issues: tuple
    tickets: tuple
    requested_periods: int
    duplicates_removed: int = 0
    has_gaps: bool = False

    @property
    def areas(self):
        return AREAS[self.lottery_type]

    @classmethod
    def from_data(cls, lottery_type, data, periods=180):
        if lottery_type not in AREAS:
            raise ValueError('不支持的彩种')
        periods = positive_int(periods, '历史期数')
        if not isinstance(data, pd.DataFrame):
            raise ValueError('历史必须是DataFrame')
        if data.empty:
            return cls(lottery_type, (), (), periods)
        df = normalize_number_data(data.reset_index(drop=True), lottery_type)
        issue_col = 'draw_num' if 'draw_num' in df else 'issue'
        if issue_col not in df:
            raise ValueError('历史缺少期号')
        records = {}
        duplicates = 0
        for row in df.to_dict('records'):
            issue = str(row[issue_col]).strip()
            # DLT stores YYNNN; accept the legacy YYYYNNN alias at the boundary.
            if lottery_type == 'dlt' and re.fullmatch(r'20[0-9]{5}', issue):
                issue = issue[2:]
            digits = 7 if lottery_type == 'ssq' else 5
            if not re.fullmatch(r'[0-9]{%d}' % digits, issue) or int(issue[-3:]) == 0:
                raise ValueError(f'无效历史期号: {issue}')
            if lottery_type == 'ssq':
                ticket = (tuple(row['red_numbers']), (int(row['blue_number']),))
            else:
                ticket = (tuple(row['front_numbers']), tuple(row['back_numbers']))
            if issue in records:
                if records[issue] != ticket:
                    raise ValueError(f'同一期号存在冲突: {issue}')
                duplicates += 1
            records[issue] = ticket
        issues = tuple(sorted(records, reverse=True)[:periods])
        # Cross-year continuity cannot be established without a draw calendar.
        gaps = any(a[:-3] != b[:-3] or int(a) - int(b) != 1 for a, b in zip(issues, issues[1:]))
        return cls(lottery_type, issues, tuple(records[i] for i in issues), periods, duplicates, gaps)

    def to_dict(self):
        return {'lottery_type': self.lottery_type, 'issues': list(self.issues),
                'tickets': [[list(a) for a in t] for t in self.tickets],
                'requested_periods': self.requested_periods,
                'duplicates_removed': self.duplicates_removed, 'has_gaps': self.has_gaps,
                'cutoff': self.issues[0] if self.issues else None,
                'coverage_note': '仅观察记录；有缺口或跨年完整性未核实' if self.has_gaps else '仅观察记录'}

    @property
    def digest(self):
        return sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()
