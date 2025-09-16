import pandas as pd

class SSQFeatureProcessor:
    """双色球特征处理器"""
    
    def __init__(self):
        """初始化双色球特征处理器"""
        self.window_sizes = [3, 5, 10]  # 滑动窗口大小
        
    def generate_basic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成基础特征
        
        Args:
            data: 输入数据DataFrame
            
        Returns:
            包含基础特征的DataFrame
        """
        if data is None or data.empty:
            raise ValueError("输入数据不能为空")
            
        features = pd.DataFrame(index=data.index)
        
        # 为每个数字列生成统计特征
        for col in data.columns:
            # 移动平均
            features[f'{col}_mean_3'] = data[col].rolling(window=3).mean()
            features[f'{col}_mean_5'] = data[col].rolling(window=5).mean()
            
            # 移动标准差
            features[f'{col}_std_3'] = data[col].rolling(window=3).std()
            features[f'{col}_std_5'] = data[col].rolling(window=5).std()
            
            # 移动最大最小值
            features[f'{col}_max_3'] = data[col].rolling(window=3).max()
            features[f'{col}_min_3'] = data[col].rolling(window=3).min()
            
        # 删除包含NaN的行
        features = features.dropna()
        
        return features
