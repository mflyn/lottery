import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.core.data_manager import LotteryDataManager
from src.core.features.feature_engineering import FeatureEngineering
from src.core.smart_recommender import SmartRecommender
from src.core.dlt_calculator import DLTCalculator

class TestEndToEndWorkflow(unittest.TestCase):
    def setUp(self):
        # 构造临时历史数据
        self.history_data = pd.DataFrame({
            'draw_date': ['2024-01-01', '2024-01-02'],
            'draw_number': ['2024001', '2024002'],
            'front_numbers': [[1,2,3,4,5], [6,7,8,9,10]],
            'back_numbers': [[1,2], [3,4]],
            'prize_pool': [10000000, 12000000],
            'sales': [20000000, 22000000]
        })
        # 数据管理器 mock
        self.data_manager = MagicMock(spec=LotteryDataManager)
        self.data_manager.get_history_data.return_value = self.history_data
        # 特征工程 mock
        self.feature_engineering = MagicMock(spec=FeatureEngineering)
        self.feature_engineering.generate_features.return_value = pd.DataFrame({
            'front_sum': [15, 40],
            'back_sum': [3, 7]
        })
        # 智能选号 mock
        self.smart_recommender = MagicMock(spec=SmartRecommender)
        self.smart_recommender.generate_recommendations.return_value = [
            {'numbers': {'front': [1,2,3,4,5], 'back': [1,2]}, 'score': 0.9},
            {'numbers': {'front': [6,7,8,9,10], 'back': [3,4]}, 'score': 0.8}
        ]
        # 投注计算器
        self.calculator = DLTCalculator()

    def test_full_workflow(self):
        # 1. 数据导入
        data = self.data_manager.get_history_data('dlt')
        self.assertEqual(len(data), 2)
        # 2. 特征生成
        features = self.feature_engineering.generate_features(data)
        self.assertIn('front_sum', features.columns)
        # 3. 智能选号
        recommendations = self.smart_recommender.generate_recommendations(data, num_recommendations=2)
        self.assertEqual(len(recommendations), 2)
        # 4. 投注计算
        rec = recommendations[0]['numbers']
        bet_result = self.calculator.calculate_complex_bet(rec['front'], rec['back'])
        self.assertGreater(bet_result.total_bets, 0)
        # 5. 中奖对照
        # 假设开奖号码与推荐号码完全一致
        level, prize = self.calculator.check_prize(
            rec['front'] + rec['back'],
            rec['front'] + rec['back']
        )
        self.assertEqual(level, 1)
        self.assertTrue(prize > 0)

if __name__ == '__main__':
    unittest.main() 