from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import random
from typing import List, Dict
from src.core.features.feature_engineering import FeatureEngineering
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
        """Prepare data for feature engineering by expanding number columns."""
        df = history_data.copy()
        if lottery_type == 'ssq' and 'red_1' not in df.columns:
            red_numbers = df['red_numbers'].apply(pd.Series)
            red_numbers.columns = [f'red_{i+1}' for i in range(red_numbers.shape[1])]
            blue_numbers = df['blue_number'].apply(pd.Series)
            blue_numbers.columns = [f'blue_{i+1}' for i in range(blue_numbers.shape[1])]
            df = pd.concat([df, red_numbers, blue_numbers], axis=1)
        elif lottery_type == 'dlt' and 'front_1' not in df.columns:
            front_numbers = df['front_numbers'].apply(pd.Series)
            front_numbers.columns = [f'front_{i+1}' for i in range(front_numbers.shape[1])]
            back_numbers = df['back_numbers'].apply(pd.Series)
            back_numbers.columns = [f'back_{i+1}' for i in range(back_numbers.shape[1])]
            df = pd.concat([df, front_numbers, back_numbers], axis=1)
        return df

    def generate_recommendations(self,
                               history_data: pd.DataFrame,
                               num_recommendations: int = 5) -> List[Dict]:
        """生成智能推荐号码"""
        if 'red_numbers' in history_data.columns:
            lottery_type = 'ssq'
        elif 'front_numbers' in history_data.columns:
            lottery_type = 'dlt'
        else:
            raise ValueError("Unknown lottery type in history_data")

        self.feature_engineer.lottery_type = lottery_type
        self.feature_engineer.processor = SSQFeatureProcessor() if lottery_type == 'ssq' else DLTFeatureProcessor()

        prepared_data = self._prepare_data_for_feature_engineering(history_data, lottery_type)
        print(prepared_data.dtypes)
        print(prepared_data.dtypes)
        features = self.feature_engineer.generate_features(prepared_data)

        # Create a dummy target variable (e.g., sum of next draw's red numbers)
        if lottery_type == 'ssq':
            y = prepared_data['red_1'].shift(-1)
        else:
            y = prepared_data['front_1'].shift(-1)
            
        features = features.iloc[:-1]
        y = y.iloc[:-1]
        
        # Drop rows with NaN in features or target
        features = features.dropna()
        y = y[features.index]
        
        if features.empty:
            raise ValueError("Not enough data to generate features and target.")

        print(features.dtypes)
        self.train_models(features, y)

        # Predict on the last set of features
        last_features = features.tail(1)
        candidates = self._generate_candidates(last_features, num_recommendations)

        if self.evaluator:
            scored_candidates = self._score_candidates(candidates)
        else:
            scored_candidates = [{'numbers': c, 'score': 0} for c in candidates]

        diverse_recommendations = self._optimize_diversity(scored_candidates)

        return diverse_recommendations[:num_recommendations]

    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """训练机器学习模型"""
        if X.empty or y.empty:
            return {}
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print(X_train.dtypes)
        print(X_train.head())
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        results = {}
        for name, model in self.models.items():
            model.fit(X_train_scaled, y_train)
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            results[name] = {'train_score': train_score, 'test_score': test_score}
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