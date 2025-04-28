from sklearn.ensemble import RandomForestRegressor
from src.core.model_optimization import ModelOptimizer

# 创建模型和参数网格
model = RandomForestRegressor()
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7],
    'min_samples_split': [2, 5, 10]
}

# 初始化优化器
optimizer = ModelOptimizer(model, param_grid)

# 网格搜索优化
best_model = optimizer.grid_search(X_train, y_train)

# 特征选择
selected_features = optimizer.feature_selection(X_train, y_train)

# 降维
X_reduced, pca = optimizer.dimensionality_reduction(X_train)

# 保存模型
optimizer.save_model('best_model.joblib')

# 获取优化报告
report = optimizer.get_optimization_report()
print(report)