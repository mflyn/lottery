import pandas as pd
from src.core.features.feature_engineering import FeatureEngineering

# 创建特征工程实例
fe = FeatureEngineering(scaler_type='standard')

# 读取数据
data = pd.read_csv('lottery_data.csv')

# 生成特征
features = fe.generate_basic_features(data)
features = fe.generate_advanced_features(features)

# 特征选择
target = data['winning_numbers']
selected_features = fe.select_features(features, target, method='mutual_info', k=10)

# 查看特征重要性
importance = fe.get_feature_importance()
print("Feature importance:", importance)

# 使用转换流水线
transformed_features = fe.transform(data)
print("Transformed features shape:", transformed_features.shape)