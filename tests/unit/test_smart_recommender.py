import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from src.core.smart_recommender import SmartRecommender

class TestSmartRecommender(unittest.TestCase):
    def setUp(self):
        self.recommender = SmartRecommender()
        # mock 依赖，避免真实特征工程和模型
        self.recommender.feature_engineer = MagicMock()
        self.recommender.models = {
            'rf': MagicMock(),
            'gb': MagicMock(),
            'mlp': MagicMock()
        }
        self.recommender.evaluator = MagicMock()  # 提前 mock，避免 NumberEvaluator 导入问题
        self.recommender.scaler = MagicMock()

    def test_analyze_historical_data(self):
        df = pd.DataFrame({'num': [1,2,3,4,5]})
        # mock 内部方法
        self.recommender._get_hot_numbers = MagicMock(return_value=[1,2,3])
        self.recommender._get_cold_numbers = MagicMock(return_value=[4,5])
        self.recommender._find_patterns = MagicMock(return_value={'pattern': 1})
        self.recommender._calculate_statistics = MagicMock(return_value={'mean': 3})
        result = self.recommender.analyze_historical_data(df)
        self.assertIn('hot_numbers', result)
        self.assertIn('cold_numbers', result)
        self.assertIn('patterns', result)
        self.assertIn('statistics', result)

    def test_train_models(self):
        X = np.random.rand(20, 3)
        y = np.random.randint(0, 2, 20)
        # mock scaler
        self.recommender.scaler.fit_transform = MagicMock(return_value=X)
        self.recommender.scaler.transform = MagicMock(return_value=X)
        for m in self.recommender.models.values():
            m.fit = MagicMock()
            m.score = MagicMock(return_value=0.9)
        result = self.recommender.train_models(X, y)
        self.assertTrue(all('train_score' in v and 'test_score' in v for v in result.values()))

    def test_generate_recommendations(self):
        # mock特征工程
        self.recommender.feature_engineer.generate_comprehensive_features = MagicMock(return_value=np.random.rand(5,3))
        # mock候选生成
        self.recommender._generate_candidates = MagicMock(return_value=[{'num': i} for i in range(10)])
        # mock评分
        self.recommender._score_candidates = MagicMock(return_value=[{'numbers': {'num': i}, 'score': 10-i, 'details': {}} for i in range(10)])
        # mock多样性
        self.recommender._optimize_diversity = MagicMock(side_effect=lambda x: x)
        recs = self.recommender.generate_recommendations(pd.DataFrame({'a':[1,2,3]}), num_recommendations=3)
        self.assertEqual(len(recs), 3)
        self.assertTrue(all('numbers' in r and 'score' in r for r in recs))

    def test_score_candidates(self):
        # mock evaluator
        self.recommender.evaluator.evaluate_number = MagicMock(return_value={'total_score': 5, 'details': {}})
        candidates = [{'num': 1}, {'num': 2}]
        scored = self.recommender._score_candidates(candidates)
        self.assertEqual(len(scored), 2)
        self.assertTrue(all('score' in s for s in scored))

    def test_optimize_diversity(self):
        # 测试多样性优化逻辑
        self.recommender._calculate_similarity = MagicMock(return_value=0.5)
        candidates = [
            {'numbers': [1,2,3]},
            {'numbers': [4,5,6]},
            {'numbers': [1,2,3]}  # 与第一个重复
        ]
        diverse = self.recommender._optimize_diversity(candidates)
        self.assertTrue(len(diverse) >= 2)

if __name__ == '__main__':
    unittest.main() 