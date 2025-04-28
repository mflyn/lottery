from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score
import numpy as np

class EnsemblePredictor:
    def __init__(self):
        self.models = {
            'rf': RandomForestClassifier(n_estimators=100),
            'gbdt': GradientBoostingClassifier(),
            'nn': MLPClassifier(hidden_layer_sizes=(100, 50))
        }
        self.weights = None
        
    def fit(self, X, y):
        scores = {}
        for name, model in self.models.items():
            score = np.mean(cross_val_score(model, X, y, cv=5))
            scores[name] = score
            model.fit(X, y)
            
        # 根据交叉验证分数计算模型权重
        total = sum(scores.values())
        self.weights = {name: score/total for name, score in scores.items()}
        
    def predict(self, X):
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict_proba(X)
            predictions[name] = pred * self.weights[name]
            
        # 加权集成预测
        final_pred = sum(predictions.values())
        return final_pred