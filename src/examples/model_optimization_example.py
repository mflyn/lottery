import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.core.model_optimization import ModelOptimizer

# 创建虚拟数据 (在实际使用中，您需要加载真实数据)
X_train = pd.DataFrame(np.random.rand(100, 10), columns=[f'feature_{i}' for i in range(10)])
y_train = pd.Series(np.random.rand(100))

# 创建模型和参数网格
model = RandomForestRegressor()
param_grid = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5],
    'min_samples_split': [2, 5]
}

# 初始化优化器
optimizer = ModelOptimizer(model)

# 执行优化
best_model, best_params = optimizer.optimize(X_train, y_train, param_grid, scoring='neg_mean_squared_error')

print("优化完成！")
print(f"最佳参数: {best_params}")

# 获取优化摘要
report = optimizer.get_optimization_summary()
print("\n优化报告:")
print(report)

# 绘制优化历史
optimizer.plot_optimization_history()
