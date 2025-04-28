from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC

class SQQAnalyzer:
    def __init__(self, data_fetcher: Optional[SQQDataFetcher] = None, debug_mode: bool = False):
        """初始化分析器

        Args:
            data_fetcher: 数据获取器实例
            debug_mode: 是否启用调试模式
        """
        self.data_fetcher = data_fetcher or SQQDataFetcher()
        self.debug_mode = debug_mode
        self.plot_style = {
            'figure.figsize': (12, 8),
            'axes.unicode_minus': False  # 支持中文显示
        }
        self.models = {
            'random_forest': RandomForestClassifier(),
            'gradient_boost': GradientBoostingClassifier(),
            'svm': SVC(),
            'mlp': MLPClassifier()
        }