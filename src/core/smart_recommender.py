from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import random
from typing import List, Dict
from src.core.features.feature_engineering import FeatureEngineering
from src.core.number_data import normalize_number_data
from src.core.features.ssq_feature_processor import SSQFeatureProcessor
from src.core.features.dlt_feature_processor import DLTFeatureProcessor

try:
    from src.core.features.evaluator import NumberEvaluator
except ImportError:
    NumberEvaluator = None

class SmartRecommender:
    """智能推荐系统"""

    def __init__(self):
        self.feature_engineer = FeatureEngineering()
        self.models = self._init_models()
        self.scaler = StandardScaler()
        if NumberEvaluator is not None:
            self.evaluator = NumberEvaluator()
        else:
            self.evaluator = None

    def _prepare_data_for_feature_engineering(self, history_data: pd.DataFrame, lottery_type: str) -> pd.DataFrame:
        return normalize_number_data(history_data, lottery_type)

    def generate_recommendations(self, history_data: pd.DataFrame,
                                 num_recommendations: int = 5) -> List[Dict]:
        """从规范化的历史数据生成候选；训练集不包含未知的下一期目标。"""
        if isinstance(num_recommendations, bool) or not isinstance(num_recommendations, int) or num_recommendations < 0:
            raise ValueError("推荐注数必须为非负整数")
        if num_recommendations == 0:
            return []
        if not isinstance(history_data, pd.DataFrame) or len(history_data) < 7:
            raise ValueError("至少需要7期有效历史数据")
        if 'red_numbers' in history_data.columns or 'red_1' in history_data.columns:
            lottery_type = 'ssq'
        elif 'front_numbers' in history_data.columns or 'front_1' in history_data.columns:
            lottery_type = 'dlt'
        else:
            raise ValueError("Unknown lottery type in history_data")
        prepared = self._prepare_data_for_feature_engineering(history_data, lottery_type)
        date_column = next((column for column in ['draw_date', 'date'] if column in prepared.columns), None)
        if date_column:
            prepared[date_column] = pd.to_datetime(prepared[date_column], errors='raise')
            if prepared[date_column].isna().any():
                raise ValueError("开奖日期不能为空")
            prepared = prepared.sort_values(date_column, kind='stable')

        self.feature_engineer.lottery_type = lottery_type
        self.feature_engineer.processor = SSQFeatureProcessor() if lottery_type == 'ssq' else DLTFeatureProcessor()
        features = self.feature_engineer.generate_features(prepared)
        latest_features = features.tail(1)
        target_column = 'red_1' if lottery_type == 'ssq' else 'front_1'
        target = prepared[target_column].shift(-1).iloc[:-1]
        self.train_models(features.iloc[:-1], target)
        candidates = self._generate_candidates(latest_features, num_recommendations)
        scored = self._score_candidates(candidates)
        return self._optimize_diversity(scored)[:num_recommendations]

    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """接受数值DataFrame或数组，以时间顺序拆分训练集和验证集。"""
        label_alignment = isinstance(X, pd.DataFrame) and isinstance(y, pd.Series)
        X = pd.DataFrame(X).copy()
        values = np.asarray(y)
        if values.ndim != 1 or len(values) != len(X):
            raise ValueError("特征与一维目标的记录数必须一致")
        y = (FeatureEngineering._aligned_target(X, y) if label_alignment
             else pd.Series(values, index=X.index))
        if X.empty or y.empty:
            return {}
        if len(X) < 6 or not np.isfinite(X.to_numpy(dtype=float)).all() or not np.isfinite(y.to_numpy(dtype=float)).all():
            raise ValueError("训练至少需要6条有限数值记录")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        results = {}
        for name, model in self.models.items():
            model.fit(X_train_scaled, y_train)
            results[name] = {'train_score': model.score(X_train_scaled, y_train),
                             'test_score': model.score(X_test_scaled, y_test)}
        return results

    def _generate_candidates(self, features: pd.DataFrame, num_recommendations: int) -> List[Dict]:
        """生成候选号码"""
        candidates = []
        scaled_features = self.scaler.transform(features)
        for model_name, model in self.models.items():
            try:
                # Use predict to get a single value, then generate numbers around it
                prediction = model.predict(scaled_features)
                candidates.extend(self._convert_predictions_to_numbers(prediction, num_recommendations))
            except Exception as e:
                print(f"Error generating candidates with {model_name}: {e}")
        return candidates

    def _convert_predictions_to_numbers(self, predictions: np.ndarray, num_recommendations: int) -> List[Dict]:
        """Converts model predictions into lottery numbers."""
        numbers = []
        for _ in range(num_recommendations):
            # Simple placeholder: generate random numbers for now
            if self.feature_engineer.lottery_type == 'ssq':
                red = sorted(random.sample(range(1, 34), 6))
                blue = random.randint(1, 16)
                numbers.append({'red': red, 'blue': blue})
            else: # dlt
                front = sorted(random.sample(range(1, 36), 5))
                back = sorted(random.sample(range(1, 13), 2))
                numbers.append({'front': front, 'back': back})
        return numbers

    def _score_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """评分候选号码"""
        if not self.evaluator:
            return [{'numbers': c, 'score': 0} for c in candidates]
        scored = []
        for candidate in candidates:
            score = self.evaluator.evaluate_number(candidate)
            scored.append({'numbers': candidate, 'score': score['total_score'], 'details': score['details']})
        return sorted(scored, key=lambda x: x['score'], reverse=True)

    def _optimize_diversity(self, candidates: List[Dict]) -> List[Dict]:
        """优化推荐多样性"""
        if not candidates:
            return []
        diverse = []
        for candidate in candidates:
            if self._is_diverse_enough(candidate, diverse):
                diverse.append(candidate)
        return diverse

    def _calculate_similarity(self, num_set1: Dict, num_set2: Dict) -> float:
        """Calculates similarity between two number sets."""
        if 'red' in num_set1: # SSQ
            set1 = set(num_set1['red'])
            set2 = set(num_set2['red'])
        else: # DLT
            set1 = set(num_set1['front'])
            set2 = set(num_set2['front'])
        
        return len(set1.intersection(set2)) / len(set1.union(set2))

    def _is_diverse_enough(self, candidate: Dict, selected: List[Dict]) -> bool:
        """检查是否与已选号码足够不同"""
        if not selected:
            return True
        for existing in selected:
            similarity = self._calculate_similarity(candidate['numbers'], existing['numbers'])
            if similarity > 0.5:  # Similarity threshold
                return False
        return True

    def _init_models(self):
        """初始化推荐用的机器学习模型字典"""
        # Using regressors since the dummy target is continuous
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.neural_network import MLPRegressor
        return {
            'rf': RandomForestRegressor(random_state=42),
            'gb': GradientBoostingRegressor(random_state=42),
            'mlp': MLPRegressor(max_iter=500, random_state=42)
        }
