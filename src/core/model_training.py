from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class ModelTraining:
    def evaluate_model(self, X_test, y_test):
        """评估模型"""
        try:
            predictions = self.model.predict(X_test)
            scores = {
                'accuracy': accuracy_score(y_test, predictions),
                'precision': precision_score(y_test, predictions, average='weighted'),
                'recall': recall_score(y_test, predictions, average='weighted'),
                'f1': f1_score(y_test, predictions, average='weighted')
            }
            return scores
        except Exception as e:
            self.logger.error(f"模型评估失败: {str(e)}")
            return None

    def predict(self, X):
        """模型预测"""
        try:
            predictions = self.model.predict(X)
            return {
                'class': predictions,
                'probability': self.model.predict_proba(X)
            }
        except Exception as e:
            self.logger.error(f"预测失败: {str(e)}")
            return None
