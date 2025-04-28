from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from src.core.features.feature_engineering import FeatureEngineering
try:
    from src.core.features.evaluator import NumberEvaluator
except ImportError:
    NumberEvaluator = None  # 测试时可被 mock 替代

class SmartRecommender:
    """智能推荐系统"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineering()
        self.models = self._init_models()
        if NumberEvaluator is not None:
            self.evaluator = NumberEvaluator()
        else:
            self.evaluator = None  # 测试时可被 mock
        
    def analyze_historical_data(self, data: pd.DataFrame) -> Dict:
        """分析历史数据"""
        analysis_results = {
            'hot_numbers': self._get_hot_numbers(data),
            'cold_numbers': self._get_cold_numbers(data),
            'patterns': self._find_patterns(data),
            'statistics': self._calculate_statistics(data)
        }
        return analysis_results
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """训练机器学习模型"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # 数据标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        for name, model in self.models.items():
            # 训练模型
            model.fit(X_train_scaled, y_train)
            
            # 评估模型
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            
            results[name] = {
                'train_score': train_score,
                'test_score': test_score
            }
            
        return results
    
    def optimize_strategy(self, historical_data: pd.DataFrame) -> Dict:
        """优化推荐策略"""
        strategy = {
            'weights': self._calculate_weights(),
            'thresholds': self._determine_thresholds(),
            'constraints': self._define_constraints()
        }
        return strategy
    
    def generate_recommendations(self, 
                               history_data: pd.DataFrame,
                               num_recommendations: int = 5) -> List[Dict]:
        """生成智能推荐号码"""
        # 特征工程
        features = self.feature_engineer.generate_comprehensive_features(history_data)
        
        # 模型预测
        candidates = self._generate_candidates(features)
        
        # 评分和筛选
        scored_candidates = self._score_candidates(candidates)
        
        # 多样性优化
        diverse_recommendations = self._optimize_diversity(scored_candidates)
        
        # 返回前N个推荐
        return diverse_recommendations[:num_recommendations]
        
    def _generate_candidates(self, features: Dict) -> List[Dict]:
        """生成候选号码"""
        candidates = []
        
        # 使用多个模型生成候选
        for model_name, model in self.models.items():
            predictions = model.predict_proba(features)
            candidates.extend(self._convert_predictions_to_numbers(predictions))
            
        return candidates
        
    def _score_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """评分候选号码"""
        scored = []
        for candidate in candidates:
            score = self.evaluator.evaluate_number(candidate)
            scored.append({
                'numbers': candidate,
                'score': score['total_score'],
                'details': score['details']
            })
            
        return sorted(scored, key=lambda x: x['score'], reverse=True)
        
    def _optimize_diversity(self, candidates: List[Dict]) -> List[Dict]:
        """优化推荐多样性"""
        diverse = []
        for candidate in candidates:
            if self._is_diverse_enough(candidate, diverse):
                diverse.append(candidate)
                
        return diverse
        
    def _is_diverse_enough(self, candidate: Dict, selected: List[Dict]) -> bool:
        """检查是否与已选号码足够不同"""
        if not selected:
            return True
            
        for existing in selected:
            similarity = self._calculate_similarity(
                candidate['numbers'],
                existing['numbers']
            )
            if similarity > 0.8:  # 相似度阈值
                return False
                
        return True

    def _init_models(self):
        """初始化推荐用的机器学习模型字典"""
        return {
            'rf': RandomForestClassifier(),
            'gb': GradientBoostingClassifier(),
            'mlp': MLPClassifier(max_iter=200)
        }
