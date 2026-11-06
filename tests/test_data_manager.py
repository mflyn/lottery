"""Exercise the JSON history store using real temporary files."""
import copy
import json
from unittest.mock import patch

import pandas as pd
import pytest
from src.core.data_manager import LotteryDataManager

SSQ_ROWS = [
    {'draw_num': '2024001', 'draw_date': '2024-01-01',
     'red_numbers': [1, 2, 3, 4, 5, 6], 'blue_number': 7,
     'prize_pool': 100000000, 'sales': 300000000},
    {'draw_num': '2024002', 'draw_date': '2024-01-03',
     'red_numbers': [8, 9, 10, 11, 12, 13], 'blue_number': 14,
     'prize_pool': 110000000, 'sales': 310000000},
]
DLT_ROWS = [
    {'draw_num': '24001', 'draw_date': '2024-01-02',
     'front_numbers': [1, 2, 3, 4, 5], 'back_numbers': [1, 2],
     'prize_pool': 50000000, 'sales': 200000000},
    {'draw_num': '24002', 'draw_date': '2024-01-04',
     'front_numbers': [6, 7, 8, 9, 10], 'back_numbers': [3, 4],
     'prize_pool': 55000000, 'sales': 210000000},
]
NEW_SSQ = {'draw_num': '2024003', 'draw_date': '2024-01-05',
           'red_numbers': [20, 21, 22, 23, 24, 25], 'blue_number': 16,
           'prize_pool': 130000000, 'sales': 330000000}


def write_history(path, rows):
    path.write_text(json.dumps({'data': rows, 'total_periods': len(rows),
                                'fetch_time': '2024-01-05 12:00:00'}), encoding='utf-8')


class TestDataManager:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.test_dir = tmp_path
        self.data_manager = LotteryDataManager(str(tmp_path))
        self.ssq_file = tmp_path / 'ssq_history.json'
        self.dlt_file = tmp_path / 'dlt_history.json'
        write_history(self.ssq_file, SSQ_ROWS)
        write_history(self.dlt_file, DLT_ROWS)

    def test_get_history_data_ssq_all(self):
        data = self.data_manager.get_history_data('ssq')
        assert data['draw_num'].tolist() == ['2024002', '2024001']
        assert data.iloc[0]['red_numbers'] == [8, 9, 10, 11, 12, 13]

    def test_get_history_data_dlt_periods(self):
        data = self.data_manager.get_history_data('dlt', periods=1)
        assert data['draw_num'].tolist() == ['24002']
        assert data.iloc[0]['back_numbers'] == [3, 4]

    def test_get_history_data_nonexistent(self):
        with pytest.raises(ValueError):
            self.data_manager.get_history_data('xyz')
        self.ssq_file.unlink()
        assert self.data_manager.get_history_data('ssq').empty

    def test_update_data_success(self, monkeypatch):
        monkeypatch.setattr(self.data_manager, '_fetch_online_data_as_list',
                            lambda lottery_type: [copy.deepcopy(NEW_SSQ)])
        assert self.data_manager.update_data('ssq')
        saved = json.loads(self.ssq_file.read_text())
        assert saved['total_periods'] == 3
        assert saved['data'][0] == NEW_SSQ

    @pytest.mark.parametrize('response, expected', [(None, False), ([], True)])
    def test_update_data_no_new_data(self, monkeypatch, response, expected):
        before = self.ssq_file.read_bytes()
        monkeypatch.setattr(self.data_manager, '_fetch_online_data_as_list',
                            lambda lottery_type: response)
        assert self.data_manager.update_data('ssq') is expected
        assert self.ssq_file.read_bytes() == before

    @pytest.mark.parametrize('format, suffix', [('csv', '.csv'), ('json', '.json'), ('excel', '.xlsx')])
    def test_export_data(self, format, suffix):
        output = self.test_dir / ('export' + suffix)
        assert self.data_manager.export_data('ssq', str(output), format=format)
        if format == 'json':
            assert json.loads(output.read_text())['data'] == SSQ_ROWS
        else:
            data = pd.read_csv(output) if format == 'csv' else pd.read_excel(output)
            assert data['draw_num'].astype(str).tolist() == ['2024002', '2024001']

    def test_export_data_invalid_format(self):
        assert not self.data_manager.export_data('ssq', str(self.test_dir / 'bad.txt'), 'txt')

    @pytest.mark.parametrize('suffix', ['.csv', '.xlsx', '.json'])
    def test_import_canonical_data(self, suffix):
        source = self.test_dir / ('import' + suffix)
        if suffix == '.csv':
            pd.DataFrame([NEW_SSQ]).to_csv(source, index=False)
        elif suffix == '.xlsx':
            pd.DataFrame([NEW_SSQ]).to_excel(source, index=False)
        else:
            source.write_text(json.dumps({'data': [NEW_SSQ]}), encoding='utf-8')
        assert self.data_manager.import_data(str(source), 'ssq')
        saved = json.loads(self.ssq_file.read_text())
        assert saved['total_periods'] == 3
        assert saved['data'][0] == NEW_SSQ
        assert saved['data'][1:] == list(reversed(SSQ_ROWS))

    def test_import_legacy_csv(self):
        source = self.test_dir / 'legacy.csv'
        pd.DataFrame([{'date': '2024-01-05', 'issue': '2024003',
                       'numbers': '20,21,22,23,24,25,16',
                       'prize_pool': 130000000, 'sales': 330000000}]).to_csv(source, index=False)
        assert self.data_manager.import_data(str(source), 'ssq')
        assert json.loads(self.ssq_file.read_text())['data'][0] == NEW_SSQ

    def test_excel_date_cells_are_imported(self):
        source = self.test_dir / 'date-cell.xlsx'
        pd.DataFrame([dict(NEW_SSQ, draw_date=pd.Timestamp('2024-01-05'))]).to_excel(source, index=False)
        assert self.data_manager.import_data(str(source), 'ssq')
        assert json.loads(self.ssq_file.read_text())['data'][0] == NEW_SSQ

    def test_missing_optional_amounts_default_to_zero_per_record(self):
        source = self.test_dir / 'partial-amounts.json'
        row = dict(NEW_SSQ, draw_num='2024004')
        row.pop('sales')
        row.pop('prize_pool')
        source.write_text(json.dumps({'data': [NEW_SSQ, row]}), encoding='utf-8')
        assert self.data_manager.import_data(str(source), 'ssq')
        saved = json.loads(self.ssq_file.read_text())
        assert saved['data'][0]['sales'] == 0
        assert saved['data'][0]['prize_pool'] == 0
        assert saved['data'][1]['sales'] == 330000000

    def test_import_json_list(self):
        source = self.test_dir / 'list.json'
        source.write_text(json.dumps([NEW_SSQ]), encoding='utf-8')
        assert self.data_manager.import_data(str(source), 'ssq')
        assert json.loads(self.ssq_file.read_text())['data'][0] == NEW_SSQ

    @pytest.mark.parametrize('field, value', [
        ('draw_num', '20240030'), ('draw_date', 'invalid-date'), ('draw_date', None),
        ('red_numbers', [1, 2, 3, 4, 5, 34]), ('red_numbers', [1, 2, 3, 4, 5, 5]),
        ('red_numbers', [1, 2, 3]), ('red_numbers', [1, 2, 3, 4, 5, 6.5]),
        ('blue_number', 17), ('blue_number', True), ('sales', 'invalid'), ('sales', float('inf')),
        ('source', float('nan')), ('metadata', {'score': float('inf')}),
    ])
    def test_invalid_import_preserves_history(self, field, value):
        row = copy.deepcopy(NEW_SSQ)
        row[field] = value
        source = self.test_dir / 'invalid.json'
        source.write_text(json.dumps({'data': [row]}), encoding='utf-8')
        before = self.ssq_file.read_bytes()
        assert not self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_bytes() == before

    def test_missing_fields_do_not_create_history(self):
        self.ssq_file.unlink()
        source = self.test_dir / 'missing.csv'
        pd.DataFrame({'col1': [1], 'col2': [2]}).to_csv(source, index=False)
        assert not self.data_manager.import_data(str(source), 'ssq')
        assert not self.ssq_file.exists()

    @pytest.mark.parametrize('suffix', ['.json', '.csv', '.xlsx'])
    @pytest.mark.parametrize('numeric_date', [20240105, 45296, 0])
    def test_numeric_dates_are_rejected_without_changing_history(self, suffix, numeric_date):
        row = dict(NEW_SSQ, draw_date=numeric_date)
        source = self.test_dir / ('numeric-date' + suffix)
        if suffix == '.json':
            source.write_text(json.dumps({'data': [row]}), encoding='utf-8')
        elif suffix == '.csv':
            pd.DataFrame([row]).to_csv(source, index=False)
        else:
            pd.DataFrame([row]).to_excel(source, index=False)
        before = self.ssq_file.read_bytes()
        assert not self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_bytes() == before

    @pytest.mark.parametrize('format', ['json', 'json-list', 'csv', 'excel'])
    def test_sparse_optional_metadata_is_preserved(self, format):
        rows = [dict(NEW_SSQ, source='manual', confidence=0.5),
                dict(NEW_SSQ, draw_num='2024004', draw_date='2024-01-07')]
        suffix = {'json': '.json', 'json-list': '.json', 'csv': '.csv', 'excel': '.xlsx'}[format]
        source = self.test_dir / ('metadata' + suffix)
        if format in ('json', 'json-list'):
            source.write_text(json.dumps(rows if format == 'json-list' else {'data': rows}), encoding='utf-8')
        elif format == 'csv':
            pd.DataFrame(rows).to_csv(source, index=False)
        else:
            pd.DataFrame(rows).to_excel(source, index=False)
        assert self.data_manager.import_data(str(source), 'ssq')
        saved = json.loads(self.ssq_file.read_text())
        assert saved['total_periods'] == 4
        assert saved['data'][0]['draw_num'] == '2024004'
        assert saved['data'][0].get('source') is None
        assert saved['data'][0].get('confidence') is None
        assert saved['data'][1]['source'] == 'manual'
        assert saved['data'][1]['confidence'] == 0.5

    def test_mixed_valid_and_invalid_rows_are_rejected_together(self):
        source = self.test_dir / 'mixed.json'
        source.write_text(json.dumps({'data': [NEW_SSQ, {'draw_num': '2024004'}]}), encoding='utf-8')
        before = self.ssq_file.read_bytes()
        assert not self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_bytes() == before

    def test_duplicate_import_does_not_overwrite_existing_record(self):
        source = self.test_dir / 'duplicate.json'
        source.write_text(json.dumps({'data': [dict(SSQ_ROWS[0], blue_number=16)]}), encoding='utf-8')
        before = self.ssq_file.read_bytes()
        assert self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_bytes() == before

    def test_dlt_csv_preserves_leading_zero_issue(self):
        write_history(self.dlt_file, [dict(DLT_ROWS[0], draw_num='07001', draw_date='2007-05-30')])
        source = self.test_dir / 'dlt.csv'
        pd.DataFrame([dict(DLT_ROWS[1], draw_num='07002')]).to_csv(source, index=False)
        assert self.data_manager.import_data(str(source), 'dlt')
        saved = json.loads(self.dlt_file.read_text())
        assert [r['draw_num'] for r in saved['data']] == ['07002', '07001']
        assert saved['data'][0]['front_numbers'] == [6, 7, 8, 9, 10]

    @pytest.mark.parametrize('operation', ['serialize', 'replace'])
    def test_failed_write_preserves_history(self, operation):
        source = self.test_dir / 'new.json'
        source.write_text(json.dumps({'data': [NEW_SSQ]}), encoding='utf-8')
        before = self.ssq_file.read_bytes()
        target = 'src.core.data_manager.json.dump' if operation == 'serialize' else 'pathlib.Path.replace'
        with patch(target, side_effect=OSError('simulated write failure')):
            assert not self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_bytes() == before
        assert not list(self.test_dir.glob('*.tmp'))

    def test_corrupt_history_is_not_overwritten(self):
        self.ssq_file.write_text('broken JSON', encoding='utf-8')
        source = self.test_dir / 'new.json'
        source.write_text(json.dumps({'data': [NEW_SSQ]}), encoding='utf-8')
        assert not self.data_manager.import_data(str(source), 'ssq')
        assert self.ssq_file.read_text() == 'broken JSON'

    def test_import_unsupported_file(self):
        source = self.test_dir / 'bad.txt'
        source.write_text('invalid content', encoding='utf-8')
        assert not self.data_manager.import_data(str(source), 'ssq')

    def test_validate_data_format_valid(self):
        assert self.data_manager._validate_data_format(pd.DataFrame(SSQ_ROWS), 'ssq')

    def test_validate_data_format_invalid(self):
        assert not self.data_manager._validate_data_format(pd.DataFrame({'draw_date': ['2024-01-01']}), 'ssq')

    def test_get_statistics(self):
        stats = self.data_manager.get_statistics('ssq')
        assert stats['total_periods'] == 2
        assert stats['total_sales'] == 610000000
        assert stats['last_updated'] == '2024-01-03'

    def test_get_statistics_with_date(self):
        stats = self.data_manager.get_statistics('ssq', start_date='2024-01-02')
        assert stats['total_periods'] == 1
        assert stats['total_sales'] == 310000000
        assert stats['last_updated'] == '2024-01-03'

    def test_get_statistics_after_last_date(self):
        assert self.data_manager.get_statistics('ssq', start_date='2025-01-01') == {}
