import unittest
from unittest.mock import patch, MagicMock
from src.core.data_fetcher import DLTDataFetcher, SSQDataFetcher

class TestDLTDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DLTDataFetcher()

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_success(self, mock_get):
        # 构造模拟返回
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'value': {
                'list': [
                    {
                        'lotteryDrawResult': '01 02 03 04 05 06 07',
                        'lotteryDrawNum': '2023001',
                        'lotteryDrawTime': '2023-01-01',
                        'poolBalanceAmt': '10000000',
                        'totalSaleAmount': '20000000'
                    }
                ],
                'total': 1
            }
        }
        mock_get.return_value = mock_response
        result = self.fetcher.fetch_history(page=1, page_size=1)
        self.assertIn('items', result)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['front_numbers'], [1,2,3,4,5])
        self.assertEqual(result['items'][0]['back_numbers'], [6,7])

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_network_error(self, mock_get):
        mock_get.side_effect = Exception('network error')
        with self.assertRaises(Exception):
            self.fetcher.fetch_history()

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_data_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': False, 'message': 'error'}
        mock_get.return_value = mock_response
        with self.assertRaises(Exception):
            self.fetcher.fetch_history()

    @patch('src.core.data_fetcher.DLTDataFetcher.fetch_history')
    def test_search_history(self, mock_fetch):
        mock_fetch.return_value = {
            'items': [
                {'draw_num': '2023001', 'draw_date': '2023-01-01'},
                {'draw_num': '2023002', 'draw_date': '2023-01-02'}
            ],
            'total_pages': 1
        }
        result = self.fetcher.search_history(draw_num='2023001')
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['draw_num'], '2023001')

class TestSSQDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = SSQDataFetcher()

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'value': {
                'list': [
                    {
                        'lotteryDrawResult': '01 02 03 04 05 06 07',
                        'lotteryDrawNum': '2023001',
                        'lotteryDrawTime': '2023-01-01',
                        'poolBalanceAmt': '10000000',
                        'totalSaleAmount': '20000000'
                    }
                ],
                'total': 1
            }
        }
        mock_get.return_value = mock_response
        result = self.fetcher.fetch_history(page=1, page_size=1)
        self.assertIn('items', result)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['red_numbers'], [1,2,3,4,5,6])
        self.assertEqual(result['items'][0]['blue_numbers'], [7])

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_network_error(self, mock_get):
        mock_get.side_effect = Exception('network error')
        with self.assertRaises(Exception):
            self.fetcher.fetch_history()

    @patch('src.core.data_fetcher.requests.get')
    def test_fetch_history_data_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': False, 'message': 'error'}
        mock_get.return_value = mock_response
        with self.assertRaises(Exception):
            self.fetcher.fetch_history()

    @patch('src.core.data_fetcher.SSQDataFetcher.fetch_history')
    def test_search_history(self, mock_fetch):
        mock_fetch.return_value = {
            'items': [
                {'draw_num': '2023001', 'draw_date': '2023-01-01'},
                {'draw_num': '2023002', 'draw_date': '2023-01-02'}
            ],
            'total_pages': 1
        }
        result = self.fetcher.search_history(draw_num='2023001')
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['draw_num'], '2023001')

if __name__ == '__main__':
    unittest.main() 